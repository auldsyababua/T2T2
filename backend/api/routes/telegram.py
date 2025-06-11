from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.auth import ExportLoginTokenRequest, AcceptLoginTokenRequest

from db.database import get_db
from models.models import User, Chat
from api.routes.auth import get_current_user
from services.telegram_service import TelegramService

router = APIRouter()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")


class QRLoginRequest(BaseModel):
    pass


class QRLoginResponse(BaseModel):
    qr_link: str
    token: bytes
    expires_in: int


class ChatSelectionRequest(BaseModel):
    chat_ids: List[int]


class IndexingStatusResponse(BaseModel):
    status: str
    indexed_chats: int
    total_messages: int
    progress: float


@router.post("/qr-login", response_model=QRLoginResponse)
async def generate_qr_login(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate QR code for desktop Telegram authentication"""
    
    session_file = f"sessions/session_{current_user.tg_user_id}.session"
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Export login token for QR
        result = await client(ExportLoginTokenRequest(
            api_id=API_ID,
            api_hash=API_HASH,
            except_ids=[]
        ))
        
        # Create QR link
        qr_link = f"tg://login?token={result.token.hex()}"
        
        # Store session file path
        current_user.session_file = session_file
        await db.commit()
        
        return QRLoginResponse(
            qr_link=qr_link,
            token=result.token,
            expires_in=result.expires.timestamp()
        )
        
    finally:
        await client.disconnect()


@router.get("/chats")
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of user's Telegram chats"""
    
    if not current_user.session_file:
        raise HTTPException(status_code=400, detail="User not authenticated with Telegram")
    
    telegram_service = TelegramService(current_user.session_file)
    chats = await telegram_service.get_user_chats()
    
    return {"chats": chats}


@router.post("/index-chats")
async def index_selected_chats(
    request: ChatSelectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start indexing selected chats in background"""
    
    if not current_user.session_file:
        raise HTTPException(status_code=400, detail="User not authenticated with Telegram")
    
    # Add background task for indexing
    background_tasks.add_task(
        index_chats_task,
        current_user.id,
        current_user.session_file,
        request.chat_ids,
        db
    )
    
    return {
        "status": "indexing_started",
        "chats_to_index": len(request.chat_ids)
    }


@router.get("/indexing-status", response_model=IndexingStatusResponse)
async def get_indexing_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current indexing status"""
    
    # This would check Redis or database for indexing progress
    # For now, return mock data
    return IndexingStatusResponse(
        status="indexing",
        indexed_chats=3,
        total_messages=1500,
        progress=0.45
    )


async def index_chats_task(
    user_id: int,
    session_file: str,
    chat_ids: List[int],
    db: AsyncSession
):
    """Background task to index selected chats"""
    telegram_service = TelegramService(session_file)
    
    for chat_id in chat_ids:
        # Fetch and process messages
        await telegram_service.index_chat(user_id, chat_id, db)