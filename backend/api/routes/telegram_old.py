from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from db.database import get_db
from models.models import User
from services.image_service import ImageService
from services.telegram_service import TelegramService
from utils.cache import cache
from utils.logging import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")


# QR login classes removed - using Telegram bot authentication


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


@router.post("/qr-login", response_model=QRLoginResponse)
async def generate_qr_login(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Generate QR code for desktop Telegram authentication"""

    try:
        # Use the telegram service to generate QR code
        telegram_service = TelegramService(API_ID, API_HASH)
        result = await telegram_service.generate_qr_login(current_user.id)

        if result["status"] == "qr_generated":
            # Update user's session file path in database
            current_user.session_file = result["session_file"]
            await db.commit()

            return QRLoginResponse(
                status="qr_generated",
                qr_code=result["qr_code"],
                session_file=result["session_file"],
                message="Scan the QR code with your Telegram mobile app",
            )
        elif result["status"] == "already_authorized":
            return QRLoginResponse(
                status="already_authorized",
                message="User is already authorized with Telegram",
            )
        else:
            return QRLoginResponse(
                status="error", message="Unexpected status from QR generation"
            )

    except Exception as e:
        logger.error(f"Error generating QR login for user {current_user.id}: {str(e)}")
        return QRLoginResponse(
            status="error", message=f"Failed to generate QR code: {str(e)}"
        )


@router.get("/qr-login/status")
async def check_qr_login_status(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Check if QR login has been completed"""

    if not current_user.session_file:
        return {"status": "not_initiated", "message": "QR login not initiated"}

    try:
        from telethon import TelegramClient

        client = TelegramClient(current_user.session_file, API_ID, API_HASH)
        await client.connect()

        try:
            is_authorized = await client.is_user_authorized()
            if is_authorized:
                # Get user info
                me = await client.get_me()
                return {
                    "status": "authorized",
                    "telegram_user": {
                        "id": me.id,
                        "username": me.username,
                        "first_name": me.first_name,
                        "last_name": me.last_name,
                    },
                }
            else:
                return {"status": "waiting", "message": "Waiting for QR code scan"}
        finally:
            await client.disconnect()

    except Exception as e:
        logger.error(f"Error checking QR login status: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/chats")
async def get_user_chats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get list of user's Telegram chats"""

    if not current_user.session_file:
        raise HTTPException(
            status_code=400, detail="User not authenticated with Telegram"
        )

    telegram_service = TelegramService(API_ID, API_HASH)
    chats = await telegram_service.get_user_chats(current_user.session_file)

    return {"chats": chats}


@router.post("/index-chats")
async def index_selected_chats(
    request: ChatSelectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start indexing selected chats in background"""

    if not current_user.session_file:
        raise HTTPException(
            status_code=400, detail="User not authenticated with Telegram"
        )

    # Add background task for indexing
    background_tasks.add_task(
        index_chats_task,
        current_user.id,
        current_user.session_file,
        request.chat_ids,
        db,
    )

    return {"status": "indexing_started", "chats_to_index": len(request.chat_ids)}


@router.get("/indexing-status", response_model=IndexingStatusResponse)
async def get_indexing_status(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get current indexing status"""

    progress_key = f"indexing_progress:{current_user.id}"
    status_key = f"indexing_status:{current_user.id}"

    # Get current status
    status = await cache.get(status_key) or "idle"
    progress_data = await cache.get(progress_key) or {}

    # Calculate totals
    chats_info = []
    total_messages = 0
    indexed_messages = 0
    completed_chats = 0

    for chat_id, chat_data in progress_data.items():
        chats_info.append(
            {
                "chat_id": int(chat_id),
                "chat_title": chat_data.get("chat_title", "Unknown"),
                "status": chat_data.get("status", "pending"),
                "total_messages": chat_data.get("total", 0),
                "indexed_messages": chat_data.get("indexed", 0),
                "error": chat_data.get("error"),
            }
        )

        total_messages += chat_data.get("total", 0)
        indexed_messages += chat_data.get("indexed", 0)
        if chat_data.get("status") == "completed":
            completed_chats += 1

    # Calculate overall progress
    overall_progress = indexed_messages / total_messages if total_messages > 0 else 0.0

    # Determine overall status
    if not chats_info:
        status = "idle"
    elif completed_chats == len(chats_info):
        status = "completed"
    elif any(chat["status"] == "failed" for chat in chats_info):
        status = "partial_failure"

    return IndexingStatusResponse(
        status=status,
        chats=chats_info,
        total_chats=len(chats_info),
        completed_chats=completed_chats,
        total_messages=total_messages,
        indexed_messages=indexed_messages,
        overall_progress=overall_progress,
    )


async def index_chats_task(
    user_id: int, session_file: str, chat_ids: List[int], db: AsyncSession
):
    """Background task to index selected chats"""

    status_key = f"indexing_status:{user_id}"
    progress_key = f"indexing_progress:{user_id}"

    # Set initial status
    await cache.set(status_key, "indexing", ttl=3600)

    # Initialize progress for all chats
    progress_data = {}
    for chat_id in chat_ids:
        progress_data[str(chat_id)] = {"status": "pending", "total": 0, "indexed": 0}
    await cache.set(progress_key, progress_data, ttl=3600)

    telegram_service = TelegramService(API_ID, API_HASH)

    # Initialise ImageService once per task
    s3_bucket = os.getenv("AWS_BUCKET_NAME")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

    image_service: Optional[ImageService] = None
    if s3_bucket and aws_key and aws_secret:
        image_service = ImageService(s3_bucket, aws_key, aws_secret)

    try:
        for chat_id in chat_ids:
            await telegram_service.index_chat(
                user_id,
                chat_id,
                db,
                image_service=image_service,
            )

        # All done - update status
        await cache.set(status_key, "completed", ttl=3600)
    except Exception as e:
        # Mark as failed
        await cache.set(status_key, "failed", ttl=3600)
        logger.error(f"Indexing failed for user {user_id}: {str(e)}")
        raise
