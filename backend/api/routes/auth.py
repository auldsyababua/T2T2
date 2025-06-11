from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import jwt
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import os

from db.database import get_db
from models.models import User

router = APIRouter()
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


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
    check_hash = auth_data.pop('hash', '')
    
    # Create data-check-string
    data_check_arr = []
    for key in sorted(auth_data.keys()):
        data_check_arr.append(f"{key}={auth_data[key]}")
    data_check_string = "\n".join(data_check_arr)
    
    # Calculate HMAC
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == check_hash


@router.post("/telegram-auth")
async def telegram_auth(
    auth_data: TelegramAuthData,
    db: AsyncSession = Depends(get_db)
):
    # Verify auth data
    auth_dict = auth_data.dict()
    if not verify_telegram_auth(auth_dict):
        raise HTTPException(status_code=401, detail="Invalid authentication data")
    
    # Check auth date (not older than 1 hour)
    if datetime.utcnow().timestamp() - auth_data.auth_date > 3600:
        raise HTTPException(status_code=401, detail="Authentication data expired")
    
    # Get or create user
    result = await db.execute(
        select(User).where(User.tg_user_id == auth_data.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            tg_user_id=auth_data.id,
            username=auth_data.username,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Generate JWT
    payload = {
        "user_id": user.id,
        "tg_user_id": user.tg_user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")