"""
Telegram Mini App authentication middleware
"""
import os
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from utils.telegram_auth import verify_telegram_webapp_data, extract_user_from_init_data

class TelegramAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify Telegram Mini App authentication
    """
    
    def __init__(self, app, bot_token: Optional[str] = None):
        super().__init__(app)
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for certain paths
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get init data from header
        init_data = request.headers.get("X-Telegram-Init-Data")
        
        if not init_data:
            # For development, allow requests without auth
            if os.getenv("ENVIRONMENT") == "development":
                # Create a mock user for development
                request.state.user = {
                    "telegram_id": "12345",
                    "username": "dev_user",
                    "first_name": "Dev",
                    "last_name": "User",
                }
                request.state.telegram_user_id = "12345"
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Missing Telegram authentication data"
                )
        else:
            # Verify the init data
            verified_data = verify_telegram_webapp_data(init_data, self.bot_token)
            
            if not verified_data:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Telegram authentication data"
                )
            
            # Extract user info
            user_info = extract_user_from_init_data(verified_data)
            
            if not user_info:
                raise HTTPException(
                    status_code=401,
                    detail="No user data in authentication"
                )
            
            # Add user info to request state
            request.state.user = user_info
            request.state.telegram_user_id = user_info["telegram_id"]
        
        response = await call_next(request)
        return response

def get_current_user(request: Request) -> dict:
    """
    Get the current authenticated user from request state
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    return request.state.user

def get_telegram_user_id(request: Request) -> str:
    """
    Get the current user's Telegram ID from request state
    """
    if not hasattr(request.state, "telegram_user_id"):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    return request.state.telegram_user_id