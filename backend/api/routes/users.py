from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes.auth import get_current_user
from backend.db.database import get_db
from backend.models.models import User
from backend.utils.logging import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


class UserBase(BaseModel):
    username: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    tg_user_id: Optional[int] = None


class UserUpdate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    tg_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    logger.info(f"User {current_user.id} requested their profile")
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User {current_user.id} requested non-existent user {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"User {current_user.id} retrieved user {user_id}")
    return user


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users with pagination"""
    # Count total users
    count_result = await db.execute(select(User))
    total = len(count_result.scalars().all())

    # Get paginated users
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    total_pages = (total + per_page - 1) // per_page

    logger.info(f"User {current_user.id} listed users (page {page}/{total_pages})")

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile"""
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    await db.execute(
        update(User).where(User.id == current_user.id).values(**update_data)
    )
    await db.commit()

    # Get updated user
    result = await db.execute(select(User).where(User.id == current_user.id))
    updated_user = result.scalar_one()

    logger.info(f"User {current_user.id} updated their profile")

    return updated_user


@router.delete("/me")
async def delete_current_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete current user's account"""
    await db.delete(current_user)
    await db.commit()

    logger.info(f"User {current_user.id} deleted their account")

    return {"message": "User account deleted successfully"}


@router.get("/search/", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search users by username, first name, or last name"""
    search_term = f"%{q}%"

    result = await db.execute(
        select(User)
        .where(
            (User.username.ilike(search_term))
            | (User.first_name.ilike(search_term))
            | (User.last_name.ilike(search_term))
        )
        .limit(limit)
    )
    users = result.scalars().all()

    logger.info(
        f"User {current_user.id} searched for '{q}', found {len(users)} results"
    )

    return users
