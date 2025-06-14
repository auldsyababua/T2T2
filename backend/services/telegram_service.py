from __future__ import annotations

import os
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient
from telethon.tl.types import Chat as TgChat
from telethon.tl.types import Message as TgMessage
from telethon.tl.types import User as TgUser

from backend.models.models import (
    Chat as DBChat,
)
from backend.models.models import (
    Message as DBMessage,
)
from backend.models.models import (
    MessageImage,
    UserMessage,
)
from backend.models.models import (
    User as DBUser,
)
from backend.services.embedding_service import EmbeddingService
from backend.services.image_service import ImageService
from backend.utils.cache import cache
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class TelegramService:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self._clients: Dict[int, TelegramClient] = {}

    async def _get_client(self, session_file: str) -> TelegramClient:
        """Get or create a TelegramClient instance for the given session file."""
        if session_file not in self._clients:
            client = TelegramClient(session_file, self.api_id, self.api_hash)
            await client.connect()
            self._clients[session_file] = client
        return self._clients[session_file]

    # QR login removed - using direct Telegram authentication through bot

    async def get_user_chats(self, session_file: str) -> List[dict]:
        """Get all chats for the authenticated user."""
        try:
            client = await self._get_client(session_file)
            dialogs = await client.get_dialogs()

            chats = []
            for dialog in dialogs:
                entity = dialog.entity
                if isinstance(entity, (TgChat, TgUser)):
                    chat_data = {
                        "id": entity.id,
                        "title": getattr(entity, "title", None)
                        or f"{entity.first_name} {entity.last_name or ''}",
                        "type": "channel"
                        if getattr(entity, "broadcast", False)
                        else "group"
                        if getattr(entity, "megagroup", False)
                        else "private",
                    }
                    chats.append(chat_data)

            return chats
        except Exception as e:
            logger.error(f"Error getting user chats: {str(e)}")
            raise

    async def index_chat(
        self,
        user_id: int,
        chat_id: int,
        db: AsyncSession,
        *,
        image_service: Optional[ImageService] = None,
    ) -> None:
        """Index messages from a chat for the user."""
        # Initialize progress tracking
        progress_key = f"indexing_progress:{user_id}"
        status_key = f"indexing_status:{user_id}"
        try:
            # Get user's session file
            user_result = await db.execute(select(DBUser).where(DBUser.id == user_id))
            db_user = user_result.scalar_one()
            # Ensure user has session_file
            client = await self._get_client(db_user.session_file)

            # Get or create chat in database
            db_chat = await db.execute(select(DBChat).where(DBChat.chat_id == chat_id))
            db_chat = db_chat.scalar_one_or_none()

            if not db_chat:
                chat_entity = await client.get_entity(chat_id)
                db_chat = DBChat(
                    chat_id=chat_id,
                    title=getattr(chat_entity, "title", None)
                    or f"{chat_entity.first_name} {chat_entity.last_name or ''}",
                    type="channel"
                    if getattr(chat_entity, "broadcast", False)
                    else "group"
                    if getattr(chat_entity, "megagroup", False)
                    else "private",
                )
                db.add(db_chat)
                await db.commit()

            # Update status to indicate we're starting this chat
            await cache.set(status_key, "indexing", ttl=3600)

            # Get total message count first
            total_count = await client.get_messages(chat_id, limit=0)
            total_messages = total_count.total if hasattr(total_count, "total") else 0

            # Initialize progress for this chat
            progress_data = await cache.get(progress_key) or {}
            progress_data[str(chat_id)] = {
                "status": "indexing",
                "total": total_messages,
                "indexed": 0,
                "chat_title": db_chat.title,
            }
            await cache.set(progress_key, progress_data, ttl=3600)

            # Get messages in batches
            indexed_count = 0

            # Initialize embedding service
            embedding_service = EmbeddingService()

            # Fetch messages in batches
            async for msg in client.iter_messages(chat_id, limit=None):
                if not isinstance(msg, TgMessage):
                    continue

                indexed_count += 1

                # Update progress every 50 messages
                if indexed_count % 50 == 0:
                    progress_data = await cache.get(progress_key) or {}
                    progress_data[str(chat_id)]["indexed"] = indexed_count
                    await cache.set(progress_key, progress_data, ttl=3600)

                # Check if message already exists
                existing_msg = await db.execute(
                    select(DBMessage).where(
                        DBMessage.chat_id == db_chat.id, DBMessage.msg_id == msg.id
                    )
                )
                if existing_msg.scalar_one_or_none():
                    continue

                # Create message record
                db_message = DBMessage(
                    chat_id=db_chat.id,
                    msg_id=msg.id,
                    sender_id=msg.sender_id,
                    sender_name=getattr(msg.sender, "first_name", "")
                    + " "
                    + getattr(msg.sender, "last_name", ""),
                    text=msg.text or msg.raw_text or "",
                    date=msg.date,
                    reply_to_msg_id=msg.reply_to_msg_id,
                    has_media=bool(msg.media),
                    media_type=msg.media.__class__.__name__ if msg.media else None,
                )
                db.add(db_message)
                await db.commit()

                # Create user-message association
                user_message = UserMessage(user_id=user_id, message_id=db_message.id)
                db.add(user_message)
                await db.commit()  # Commit before embedding so message exists

                # Generate embeddings for the message
                try:
                    # If we have OCR text from images, include it
                    ocr_text = None
                    if msg.media and image_service is not None and msg.photo:
                        # We'll get OCR text from the image processing below
                        pass

                    await embedding_service.chunk_and_embed_message(
                        db_message, db, ocr_text
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to generate embeddings for message {msg.id}: {str(e)}"
                    )

                # ------------------------------------------------------
                # 🖼  Media handling (photos/documents → S3, embeddings)
                # ------------------------------------------------------
                if msg.media and image_service is not None and msg.photo:
                    try:
                        raw = BytesIO()
                        await msg.download_media(file=raw)
                        image_bytes = raw.getvalue()

                        # Skip empty downloads (rare but happens on service messages)
                        if not image_bytes:
                            raise ValueError("Downloaded media is empty")

                        processed = await image_service.process_image(image_bytes)

                        # Check for dupes by hash
                        existing_img = await db.execute(
                            select(MessageImage).where(
                                MessageImage.file_hash == processed["file_hash"]
                            )
                        )
                        if existing_img.scalar_one_or_none() is None:
                            db_image = MessageImage(
                                message_id=db_message.id,
                                file_hash=processed["file_hash"],
                                s3_url=processed["s3_url"],
                                ocr_text=processed["ocr_text"],
                                img_embedding=processed["img_embedding"],
                                width=processed["width"],
                                height=processed["height"],
                            )
                            db.add(db_image)
                    except Exception as media_exc:
                        logger.warning(
                            "Failed to process media for msg %s: %s", msg.id, media_exc
                        )

                await db.commit()

            # Mark this chat as completed
            progress_data = await cache.get(progress_key) or {}
            if str(chat_id) in progress_data:
                progress_data[str(chat_id)]["status"] = "completed"
                progress_data[str(chat_id)]["indexed"] = indexed_count
            await cache.set(progress_key, progress_data, ttl=3600)

        except Exception as e:
            logger.error(f"Error indexing chat: {str(e)}")
            # Mark as failed in progress
            progress_data = await cache.get(progress_key) or {}
            if str(chat_id) in progress_data:
                progress_data[str(chat_id)]["status"] = "failed"
                progress_data[str(chat_id)]["error"] = str(e)
            await cache.set(progress_key, progress_data, ttl=3600)
            raise
