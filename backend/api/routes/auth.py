import hashlib
import hmac
import os
import sys
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.config.authorized_users import is_user_authorized

from backend.db.database import get_db
from backend.models.models import User
from backend.utils.logging import setup_logger

router = APIRouter()
security = HTTPBearer()
logger = setup_logger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger.info(f"[AUTH] Bot token loaded: {bool(BOT_TOKEN)}, last 4 chars: ...{BOT_TOKEN[-4:] if BOT_TOKEN else 'None'}")

# Force flush logs
import sys
sys.stdout.flush()
sys.stderr.flush()


class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: str = None
    username: str = None
    photo_url: str = None
    auth_date: int
    hash: str


def verify_telegram_auth(auth_data: dict) -> bool:
    """Verify Telegram Mini App initData HMAC"""
    logger.debug(f"Verifying Telegram auth for user_id: {auth_data.get('id')}")
    check_hash = auth_data.pop("hash", "")

    # Create data-check-string
    data_check_arr = []
    for key in sorted(auth_data.keys()):
        data_check_arr.append(f"{key}={auth_data[key]}")
    data_check_string = "\n".join(data_check_arr)

    # Calculate HMAC
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    is_valid = calculated_hash == check_hash
    logger.debug(f"Auth verification result: {is_valid}")
    return is_valid


@router.post("/telegram-webapp-auth")
async def telegram_webapp_auth(
    request: Request, db: AsyncSession = Depends(get_db)
):
    """Authenticate using Telegram Mini App initData"""
    from backend.utils.telegram_auth import verify_telegram_webapp_data, extract_user_from_init_data
    
    # Also print to stdout for Railway
    print(f"[AUTH] telegram-webapp-auth endpoint called", flush=True)
    
    # Log all headers for debugging
    logger.info("[AUTH] Request headers:")
    print(f"[AUTH] All headers: {list(request.headers.keys())}", flush=True)
    
    for header_name, header_value in request.headers.items():
        if header_name.lower().startswith('x-telegram'):
            logger.info(f"[AUTH] Header {header_name}: {header_value[:50]}...")
            print(f"[AUTH] Header {header_name}: {header_value[:50]}...", flush=True)
    
    # Get initData from header
    init_data = request.headers.get("X-Telegram-Init-Data")
    logger.info(f"[AUTH] Raw init_data from header: {repr(init_data)[:100] if init_data else 'None'}")
    
    # Also check lowercase version
    if not init_data:
        init_data = request.headers.get("x-telegram-init-data")
        logger.info(f"[AUTH] Trying lowercase header: {repr(init_data)[:100] if init_data else 'None'}")
    
    if not init_data:
        logger.warning("[AUTH] No init data in request")
        logger.warning(f"[AUTH] All headers: {list(request.headers.keys())}")
        raise HTTPException(status_code=401, detail="No authentication data")
    
    logger.info("[AUTH] Received webapp auth request")
    logger.info(f"[AUTH] Init data length: {len(init_data)}")
    logger.info(f"[AUTH] Init data first 50 chars: {init_data[:50]}...")
    logger.info(f"[AUTH] Bot token present: {bool(BOT_TOKEN)}")
    
    # Verify the data and get debug info
    verified_data = verify_telegram_webapp_data(init_data, BOT_TOKEN)
    if not verified_data:
        logger.warning("[AUTH] Invalid init data")
        
        # Calculate debug info to return in error
        import hmac
        import hashlib
        from urllib.parse import unquote
        
        debug_info = {"error": "Invalid authentication data"}
        try:
            # Parse the data for debugging
            parsed_data = {}
            data_check_string_parts = []
            received_hash = ""
            
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
            
            debug_info = {
                "error": "Invalid authentication data",
                "debug": {
                    "received_hash": received_hash[:20] + "...",
                    "calculated_hash": calculated_hash[:20] + "...",
                    "hash_match": calculated_hash == received_hash,
                    "data_check_string_preview": data_check_string[:100] + "...",
                    "parsed_params": list(parsed_data.keys()),
                    "bot_token_last4": BOT_TOKEN[-4:] if BOT_TOKEN else "None"
                }
            }
        except Exception as e:
            debug_info["debug_error"] = str(e)
        
        raise HTTPException(status_code=401, detail=debug_info)
    
    # Extract user info
    user_data = extract_user_from_init_data(verified_data)
    if not user_data:
        logger.warning("[AUTH] No user data in init data")
        raise HTTPException(status_code=401, detail="No user data")
    
    telegram_id = int(user_data["telegram_id"])
    username = user_data.get("username")
    
    logger.info(f"[AUTH] Webapp auth for user: {username} (ID: {telegram_id})")
    
    # Check whitelist
    if username and not is_user_authorized(username=username, user_id=telegram_id):
        logger.warning(f"[AUTH] Unauthorized: @{username} (ID: {telegram_id})")
        raise HTTPException(status_code=403, detail="Not authorized to use this service")
    
    # Get or create user
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"[AUTH] Created new user: {user.username}")
    else:
        logger.info(f"[AUTH] Found existing user: {user.username}")
    
    # Generate JWT token
    token_data = {"user_id": str(user.id)}
    token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }


@router.post("/telegram-auth")
async def telegram_auth(
    auth_data: TelegramAuthData, db: AsyncSession = Depends(get_db)
):
    # Verify auth data
    auth_dict = auth_data.dict()
    if not verify_telegram_auth(auth_dict):
        raise HTTPException(status_code=401, detail="Invalid authentication data")

    # Check auth date (not older than 1 hour)
    if datetime.utcnow().timestamp() - auth_data.auth_date > 3600:
        raise HTTPException(status_code=401, detail="Authentication data expired")
    
    # Check whitelist authorization
    if not auth_data.username:
        raise HTTPException(
            status_code=403, 
            detail="You need a Telegram username to use this service"
        )
    
    if not is_user_authorized(auth_data.username):
        logger.warning(f"Unauthorized access attempt by @{auth_data.username} (ID: {auth_data.id})")
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to use this service. Contact admin for access."
        )

    # Get or create user
    result = await db.execute(select(User).where(User.tg_user_id == auth_data.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            tg_user_id=auth_data.id,
            username=auth_data.username,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate JWT
    payload = {
        "user_id": user.id,
        "tg_user_id": user.tg_user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"[AUTH] Getting current user from token")
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        logger.info(f"[AUTH] Token decoded, user_id: {user_id}")

        if not user_id:
            logger.warning("[AUTH] No user_id in token payload")
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"[AUTH] User not found in DB: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")

        logger.info(f"[AUTH] User authenticated: {user.username} (ID: {user.telegram_id})")
        return user

    except jwt.ExpiredSignatureError:
        logger.warning("[AUTH] Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.warning("[AUTH] Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
