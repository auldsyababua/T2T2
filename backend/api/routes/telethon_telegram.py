"""
Telegram routes using Telethon for full chat history access.
Replaces bot-based routes with user client functionality.
"""
import os
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.api.dependencies import require_current_user
from backend.db.database import get_db
from backend.models.models import User
from backend.services.chat_service import TelethonChatService
from backend.services.embedding_service import EmbeddingService
from backend.utils.cache import cache
from backend.utils.logging import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

# Initialize services
api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
api_hash = os.getenv("TELEGRAM_API_HASH", "")

if not api_id or not api_hash:
    logger.error("[TELETHON_TELEGRAM] Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")
    raise ValueError("Telegram API credentials not configured")

chat_service = TelethonChatService(api_id, api_hash)
embedding_service = EmbeddingService()


# Request/Response models
class ChatInfo(BaseModel):
    id: str
    title: str
    type: str
    username: Optional[str] = None
    unread_count: int = 0
    last_message_date: Optional[str] = None
    participant_count: Optional[int] = None
    indexed_at: Optional[str] = None
    message_count: Optional[int] = None


class ChatSelectionRequest(BaseModel):
    chat_ids: List[int] = Field(..., description="List of chat IDs to index")


class IndexingProgress(BaseModel):
    chat_id: int
    chat_title: str
    status: str  # "pending", "indexing", "completed", "failed"
    progress: float  # 0.0 to 1.0
    indexed_messages: int
    total_messages: Optional[int] = None
    error: Optional[str] = None


class IndexingStatusResponse(BaseModel):
    status: str  # "idle", "indexing", "completed", "failed"
    chats: List[IndexingProgress]
    total_chats: int
    completed_chats: int
    total_messages: int
    indexed_messages: int
    overall_progress: float


@router.get("/chats", response_model=List[ChatInfo])
async def get_user_chats(
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, description="Maximum number of chats to return"),
):
    """
    Get all chats available for the authenticated user.
    Unlike Bot API, this returns ALL chats the user has access to.
    """
    logger.info(f"[TELETHON_TELEGRAM] Getting chats for user {current_user.id}")
    logger.info(f"[TELETHON_TELEGRAM] Username: {current_user.username}")

    if not current_user.session_string:
        logger.warning(f"[TELETHON_TELEGRAM] User {current_user.id} has no session")
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Telegram. Please complete phone authentication.",
        )

    try:
        # Get chats from Telegram
        chats_data = await chat_service.get_user_chats(
            current_user.session_string, limit=limit
        )

        logger.info(f"[TELETHON_TELEGRAM] Retrieved {len(chats_data)} chats")

        # Convert to response model
        chats = []
        for chat_data in chats_data:
            chat = ChatInfo(**chat_data)

            # Check if chat is indexed in our database
            # TODO: Add database lookup for indexed_at and message_count

            chats.append(chat)

        # Cache for faster retrieval
        await cache.set(f"user_chats_{current_user.id}", chats, expire=300)

        logger.info(f"[TELETHON_TELEGRAM] Returning {len(chats)} chats")
        return chats

    except Exception as e:
        logger.error(
            f"[TELETHON_TELEGRAM] Error getting chats: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get chats: {str(e)}")


@router.get("/chats/{chat_id}/history")
async def get_chat_history(
    chat_id: int,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, description="Number of messages to return"),
    offset_id: int = Query(0, description="Message ID to start from"),
):
    """
    Get chat history with full access to all messages.
    This is the key advantage - we can get messages from before the bot joined!
    """
    logger.info(f"[TELETHON_TELEGRAM] Getting history for chat {chat_id}")
    logger.info(
        f"[TELETHON_TELEGRAM] User: {current_user.id}, limit: {limit}, offset: {offset_id}"
    )

    if not current_user.session_string:
        raise HTTPException(status_code=400, detail="Not authenticated with Telegram")

    try:
        messages = await chat_service.get_chat_history(
            current_user.session_string, chat_id, limit=limit, offset_id=offset_id
        )

        logger.info(f"[TELETHON_TELEGRAM] Retrieved {len(messages)} messages")

        return {"chat_id": chat_id, "messages": messages, "count": len(messages)}

    except Exception as e:
        logger.error(
            f"[TELETHON_TELEGRAM] Error getting history: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat history: {str(e)}"
        )


@router.post("/index-chats")
async def index_selected_chats(
    request: ChatSelectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start indexing selected chats in the background.
    This will retrieve and store the ENTIRE chat history for each selected chat.
    """
    logger.info(f"[TELETHON_TELEGRAM] Index request for {len(request.chat_ids)} chats")
    logger.info(f"[TELETHON_TELEGRAM] User: {current_user.id}")
    logger.info(f"[TELETHON_TELEGRAM] Chat IDs: {request.chat_ids}")

    if not current_user.session_string:
        raise HTTPException(status_code=400, detail="Not authenticated with Telegram")

    # Initialize indexing status
    initial_status = {
        "status": "starting",
        "chats": [
            {
                "chat_id": chat_id,
                "chat_title": f"Chat {chat_id}",  # Will be updated during indexing
                "status": "pending",
                "progress": 0.0,
                "indexed_messages": 0,
                "total_messages": None,
                "error": None,
            }
            for chat_id in request.chat_ids
        ],
        "total_chats": len(request.chat_ids),
        "completed_chats": 0,
        "total_messages": 0,
        "indexed_messages": 0,
        "overall_progress": 0.0,
    }

    await cache.set(f"indexing_status_{current_user.id}", initial_status)

    logger.info(f"[TELETHON_TELEGRAM] Starting background indexing task")

    # Start background task
    background_tasks.add_task(
        index_chats_task, current_user.id, current_user.session_string, request.chat_ids
    )

    return {
        "message": f"Started indexing {len(request.chat_ids)} chats",
        "task_id": f"indexing_{current_user.id}",
    }


@router.get("/indexing-status", response_model=IndexingStatusResponse)
async def get_indexing_status(current_user: User = Depends(require_current_user)):
    """Get the current indexing status for the user"""
    logger.info(f"[TELETHON_TELEGRAM] Status check for user {current_user.id}")

    status = await cache.get(f"indexing_status_{current_user.id}")

    if not status:
        logger.info(
            f"[TELETHON_TELEGRAM] No active indexing for user {current_user.id}"
        )
        return IndexingStatusResponse(
            status="idle",
            chats=[],
            total_chats=0,
            completed_chats=0,
            total_messages=0,
            indexed_messages=0,
            overall_progress=0.0,
        )

    logger.info(f"[TELETHON_TELEGRAM] Indexing status: {status['status']}")
    logger.info(f"[TELETHON_TELEGRAM] Progress: {status['overall_progress']}%")

    return IndexingStatusResponse(**status)


async def index_chats_task(user_id: int, session_string: str, chat_ids: List[int]):
    """Background task to index multiple chats"""
    logger.info(f"[INDEXING_TASK] Starting for user {user_id}")
    logger.info(f"[INDEXING_TASK] Indexing {len(chat_ids)} chats")

    # Get current status
    status = await cache.get(f"indexing_status_{user_id}")
    if not status:
        logger.error(f"[INDEXING_TASK] No status found for user {user_id}")
        return

    status["status"] = "indexing"
    await cache.set(f"indexing_status_{user_id}", status)

    try:
        for i, chat_id in enumerate(chat_ids):
            logger.info(
                f"[INDEXING_TASK] Processing chat {i+1}/{len(chat_ids)}: {chat_id}"
            )

            # Update chat status
            chat_status = status["chats"][i]
            chat_status["status"] = "indexing"
            await cache.set(f"indexing_status_{user_id}", status)

            try:
                # Define progress callback
                async def progress_callback(progress_data):
                    logger.info(
                        f"[INDEXING_TASK] Progress for chat {chat_id}: {progress_data['indexed']} messages"
                    )

                    # Update status
                    chat_status["indexed_messages"] = progress_data["indexed"]
                    status["indexed_messages"] = sum(
                        c["indexed_messages"] for c in status["chats"]
                    )

                    # Calculate overall progress
                    completed = sum(
                        1 for c in status["chats"] if c["status"] == "completed"
                    )
                    in_progress = sum(
                        c["progress"]
                        for c in status["chats"]
                        if c["status"] == "indexing"
                    )
                    status["overall_progress"] = (
                        (completed + in_progress) / len(chat_ids)
                    ) * 100

                    await cache.set(f"indexing_status_{user_id}", status)

                # Index the chat
                result = await chat_service.index_chat(
                    session_string, chat_id, progress_callback=progress_callback
                )

                # Update status with results
                chat_status["status"] = "completed"
                chat_status["chat_title"] = result["chat_title"]
                chat_status["progress"] = 1.0
                chat_status["total_messages"] = result["total_messages"]
                chat_status["indexed_messages"] = result["total_messages"]

                status["completed_chats"] += 1
                status["total_messages"] += result["total_messages"]

                logger.info(
                    f"[INDEXING_TASK] Completed chat {chat_id}: {result['total_messages']} messages"
                )

            except Exception as e:
                logger.error(
                    f"[INDEXING_TASK] Error indexing chat {chat_id}: {type(e).__name__}: {str(e)}"
                )
                chat_status["status"] = "failed"
                chat_status["error"] = str(e)

            await cache.set(f"indexing_status_{user_id}", status)

        # Mark overall status as completed
        status["status"] = "completed"
        status["overall_progress"] = 100.0
        await cache.set(
            f"indexing_status_{user_id}", status, expire=3600
        )  # Keep for 1 hour

        logger.info(f"[INDEXING_TASK] Completed all chats for user {user_id}")
        logger.info(
            f"[INDEXING_TASK] Total messages indexed: {status['total_messages']}"
        )

    except Exception as e:
        logger.error(f"[INDEXING_TASK] Fatal error: {type(e).__name__}: {str(e)}")
        status["status"] = "failed"
        await cache.set(f"indexing_status_{user_id}", status, expire=3600)
