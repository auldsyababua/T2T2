"""
API dependencies for authentication and common functionality.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
import os

from backend.db.database import get_db
from backend.models.models import User
from backend.utils.logging import setup_logger
from backend.utils.auth import decode_access_token

logger = setup_logger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    Returns None if not authenticated (for optional auth endpoints).
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Decode JWT token
    payload = decode_access_token(token)

    if not payload:
        logger.warning("[DEPENDENCIES] Invalid or expired token")
        return None

    user_id: str = payload.get("sub")

    if user_id is None:
        logger.warning("[DEPENDENCIES] Token missing user ID")
        return None

    logger.info(f"[DEPENDENCIES] Token decoded for user {user_id}")

    # Get user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"[DEPENDENCIES] User {user_id} not found in database")
        return None

    logger.info(f"[DEPENDENCIES] Authenticated user {user.id}")
    return user


async def require_current_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Require authenticated user (for protected endpoints).
    Raises 401 if not authenticated.
    """
    if not current_user:
        logger.warning("[DEPENDENCIES] Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user
