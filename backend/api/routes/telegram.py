from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes.auth import get_current_user
from backend.db.database import get_db
from backend.models.models import User
from backend.services.embedding_service import EmbeddingService

# from backend.services.image_service import ImageService  # Temporarily disabled
from backend.services.telegram_service import TelegramService
from backend.utils.cache import cache
from backend.utils.logging import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")


class ChatSelectionRequest(BaseModel):
    chat_ids: List[int]


class IndexingStatusResponse(BaseModel):
    status: str  # "idle", "indexing", "completed", "failed"
    chats: List[dict]  # List of chat progress info
    total_chats: int
    completed_chats: int
    total_messages: int
    indexed_messages: int
    overall_progress: float


@router.get("/chats")
async def get_user_chats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all chats available for the authenticated user"""
    logger.info(
        f"[CHATS] Request from user: {current_user.username} (ID: {current_user.tg_user_id})"
    )

    if not current_user.session_file:
        logger.warning(f"[CHATS] User {current_user.username} has no session_file")
        raise HTTPException(
            status_code=400,
            detail="User not connected to Telegram. Please use the bot to authenticate.",
        )

    try:
        telegram_service = TelegramService(API_ID, API_HASH)
        chats = await telegram_service.get_user_chats(current_user.session_file)

        # Store in cache for faster retrieval
        await cache.set(f"user_chats_{current_user.id}", chats, expire=300)

        return {"chats": chats}
    except Exception as e:
        logger.error(f"Error getting chats for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chats: {str(e)}")


@router.post("/index-chats")
async def index_selected_chats(
    request: ChatSelectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start indexing selected chats in the background"""

    if not current_user.session_file:
        raise HTTPException(
            status_code=400,
            detail="User not connected to Telegram. Please use the bot to authenticate.",
        )

    # Update indexing status
    await cache.set(
        f"indexing_status_{current_user.id}",
        {
            "status": "starting",
            "chats": [],
            "total_chats": len(request.chat_ids),
            "completed_chats": 0,
            "total_messages": 0,
            "indexed_messages": 0,
            "overall_progress": 0.0,
        },
    )

    # Start background task
    background_tasks.add_task(
        index_chats_task,
        current_user.id,
        current_user.session_file,
        request.chat_ids,
        db,
    )

    return {"status": "indexing_started", "chat_count": len(request.chat_ids)}


async def index_chats_task(
    user_id: int, session_file: str, chat_ids: List[int], db: AsyncSession
):
    """Background task to index selected chats"""
    try:
        telegram_service = TelegramService(API_ID, API_HASH)
        embedding_service = EmbeddingService()

        # Initialize image service for media handling
        image_service = None
        if all(
            [
                os.getenv("AWS_ACCESS_KEY_ID"),
                os.getenv("AWS_SECRET_ACCESS_KEY"),
                os.getenv("AWS_S3_BUCKET"),
            ]
        ):
            image_service = ImageService(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                bucket_name=os.getenv("AWS_S3_BUCKET"),
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )

        # Index each chat
        for i, chat_id in enumerate(chat_ids):
            try:
                # Update progress
                progress = {
                    "status": "indexing",
                    "current_chat": chat_id,
                    "completed_chats": i,
                    "total_chats": len(chat_ids),
                    "overall_progress": (i / len(chat_ids)) * 100,
                }
                await cache.set(f"indexing_status_{user_id}", progress)

                # Index the chat
                await telegram_service.index_chat(
                    session_file=session_file,
                    chat_id=chat_id,
                    user_id=user_id,
                    db=db,
                    embedding_service=embedding_service,
                    image_service=image_service,
                )

            except Exception as e:
                logger.error(f"Failed to index chat {chat_id}: {str(e)}")

        # Mark as completed
        await cache.set(
            f"indexing_status_{user_id}",
            {
                "status": "completed",
                "completed_chats": len(chat_ids),
                "total_chats": len(chat_ids),
                "overall_progress": 100.0,
            },
        )

    except Exception as e:
        logger.error(f"Indexing task failed for user {user_id}: {str(e)}")
        await cache.set(
            f"indexing_status_{user_id}",
            {"status": "failed", "error": str(e)},
        )


@router.get("/indexing-status", response_model=IndexingStatusResponse)
async def get_indexing_status(
    current_user: User = Depends(get_current_user),
):
    """Get the current status of chat indexing"""

    status = await cache.get(f"indexing_status_{current_user.id}")

    if not status:
        return IndexingStatusResponse(
            status="idle",
            chats=[],
            total_chats=0,
            completed_chats=0,
            total_messages=0,
            indexed_messages=0,
            overall_progress=0.0,
        )

    return IndexingStatusResponse(**status)
