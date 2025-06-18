"""
Authentication utilities for JWT token management.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt

from backend.utils.logging import setup_logger

logger = setup_logger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(f"[AUTH_UTILS] Created JWT token for subject: {data.get('sub')}")
    logger.info(f"[AUTH_UTILS] Token expires at: {expire.isoformat()}")
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token to decode
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"[AUTH_UTILS] Successfully decoded token for subject: {payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning(f"[AUTH_UTILS] Token expired")
        return None
    except jwt.JWTError as e:
        logger.error(f"[AUTH_UTILS] Token decode error: {type(e).__name__}: {str(e)}")
        return None