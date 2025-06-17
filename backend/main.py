import time
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware import RateLimitMiddleware
from backend.api.routes import auth, query, telegram, timeline
from backend.db.database import init_db
from backend.utils.logging import log_api_request, log_api_response, setup_logger

load_dotenv()

# Set up main logger
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting T2T2 backend application")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise

    yield

    logger.info("Shutting down T2T2 backend application")


app = FastAPI(
    title="Talk2Telegram 2",
    description="RAG over Telegram chat history",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://t2t2-app.vercel.app",
        "https://t2t2-*.vercel.app"  # Allow preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Telegram-Init-Data"],  # Explicitly allow custom header
)

# Global rate-limit: 100 req / minute per client IP
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)


# Add request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    log_api_request(
        logger,
        request.method,
        request.url.path,
        client_host=request.client.host if request.client else None,
        query_params=dict(request.query_params),
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration_ms = (time.time() - start_time) * 1000
    log_api_response(logger, response.status_code, duration_ms)

    return response


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(query.router, prefix="/api/query", tags=["query"])


@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    print("[HEALTH] Health check called", flush=True)
    return {"status": "healthy"}


@app.get("/test-logging")
async def test_logging():
    """Test endpoint to verify logging is working"""
    print("[TEST] Print statement", flush=True)
    logger.debug("[TEST] Debug log")
    logger.info("[TEST] Info log")
    logger.warning("[TEST] Warning log")
    logger.error("[TEST] Error log")
    return {"message": "Check logs for test output"}


@app.post("/test-auth-headers")
async def test_auth_headers(request: Request):
    """Test endpoint to see what headers are received"""
    import json
    from datetime import datetime
    
    headers_dict = dict(request.headers)
    print(f"[TEST-AUTH] Received headers: {list(headers_dict.keys())}", flush=True)
    
    # Look for telegram headers
    telegram_headers = {k: v for k, v in headers_dict.items() if 'telegram' in k.lower()}
    print(f"[TEST-AUTH] Telegram headers: {telegram_headers}", flush=True)
    
    # Check for debug info header
    debug_info_header = headers_dict.get("x-debug-info")
    if debug_info_header:
        print(f"[TEST-AUTH] Debug info header: {debug_info_header}", flush=True)
    
    # Check request body
    try:
        body = await request.json()
        if body.get("debugInfo"):
            print(f"[TEST-AUTH] Debug info from body: {json.dumps(body['debugInfo'], indent=2)}", flush=True)
    except:
        pass
    
    return {
        "all_headers": list(headers_dict.keys()),
        "telegram_headers": telegram_headers,
        "x_telegram_init_data": headers_dict.get("x-telegram-init-data"),
        "X_Telegram_Init_Data": headers_dict.get("X-Telegram-Init-Data"),
        "debug_info_header": headers_dict.get("x-debug-info"),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/test-auth-verify")
async def test_auth_verify(request: Request):
    """Test endpoint that returns verification details instead of just logging"""
    from backend.utils.telegram_auth import verify_telegram_webapp_data
    import os
    
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    init_data = request.headers.get("X-Telegram-Init-Data")
    
    if not init_data:
        return {"error": "No init data provided"}
    
    # Manual verification to get details
    import hmac
    import hashlib
    from urllib.parse import parse_qs, unquote
    
    try:
        # Parse the data
        parsed_data = {}
        data_check_string_parts = []
        
        for part in init_data.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                key = unquote(key)
                value = unquote(value)
                
                if key != 'hash':
                    data_check_string_parts.append(f"{key}={value}")
                    parsed_data[key] = value
                else:
                    received_hash = value
        
        # Sort and create data check string
        data_check_string_parts.sort()
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Calculate hash
        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "success": calculated_hash == received_hash,
            "received_hash": received_hash,
            "calculated_hash": calculated_hash,
            "data_check_string": data_check_string,
            "parsed_params": list(parsed_data.keys()),
            "bot_token_last4": f"...{BOT_TOKEN[-4:]}" if BOT_TOKEN else "None"
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }


if __name__ == "__main__":
    logger.info("Starting Uvicorn server on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
