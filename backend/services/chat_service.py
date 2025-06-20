"""
Telethon-based chat service for full Telegram chat history access.
Replaces the Bot API service with MTProto client functionality.
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import (
    Channel,
    Chat,
    User as TgUser,
    Message as TgMessage,
)
from telethon.errors import SessionPasswordNeededError

from backend.utils.logging import setup_logger
from backend.db.database import get_db
from backend.models.models import Chat as DBChat, Message as DBMessage, User
from backend.services.session_service import SessionService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = setup_logger(__name__)


class TelethonChatService:
    """Handles all chat operations using Telethon for full history access"""

    def __init__(self, api_id: int, api_hash: str):
        """Initialize with Telegram API credentials"""
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_service = SessionService()

        logger.info(f"[CHAT_SERVICE] Initialized Telethon chat service")
        logger.info(f"[CHAT_SERVICE] API ID: {api_id}")

    async def _get_client(self, encrypted_session: str) -> TelegramClient:
        """Get authenticated Telethon client from encrypted session"""
        logger.info(f"[CHAT_SERVICE] Creating client from encrypted session")

        # Decrypt session
        session_string = self.session_service.decrypt_session(encrypted_session)

        # Create client
        session = StringSession(session_string)
        client = TelegramClient(session, self.api_id, self.api_hash)

        await client.connect()

        if not await client.is_user_authorized():
            logger.error(f"[CHAT_SERVICE] Client not authorized")
            raise ValueError("Session not authorized")

        logger.info(f"[CHAT_SERVICE] Client connected and authorized")
        return client

    async def get_user_chats(
        self, encrypted_session: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all user's chats with full details.
        This is the key advantage over Bot API - we get ALL chats the user is in.
        """
        logger.info(f"[CHAT_SERVICE] Getting user chats, limit: {limit}")

        client = await self._get_client(encrypted_session)

        try:
            # Get dialogs (chats)
            dialogs = await client.get_dialogs(limit=limit)

            logger.info(f"[CHAT_SERVICE] Retrieved {len(dialogs)} dialogs")

            chats = []
            for dialog in dialogs:
                entity = dialog.entity

                # Determine chat type and details
                if isinstance(entity, Channel):
                    chat_type = "channel" if entity.broadcast else "supergroup"
                    chat_id = -1000000000000 - entity.id  # Telegram's ID format
                elif isinstance(entity, Chat):
                    chat_type = "group"
                    chat_id = -entity.id
                elif isinstance(entity, TgUser):
                    chat_type = "private"
                    chat_id = entity.id
                else:
                    logger.warning(
                        f"[CHAT_SERVICE] Unknown entity type: {type(entity)}"
                    )
                    continue

                chat_info = {
                    "id": str(chat_id),
                    "title": entity.title
                    if hasattr(entity, "title")
                    else f"{entity.first_name or ''} {entity.last_name or ''}".strip(),
                    "type": chat_type,
                    "username": getattr(entity, "username", None),
                    "unread_count": dialog.unread_count,
                    "last_message_date": dialog.message.date.isoformat()
                    if dialog.message
                    else None,
                    "participant_count": getattr(entity, "participants_count", None),
                    "is_verified": getattr(entity, "verified", False),
                    "is_restricted": getattr(entity, "restricted", False),
                    "is_scam": getattr(entity, "scam", False),
                    "is_fake": getattr(entity, "fake", False),
                }

                logger.info(f"[CHAT_SERVICE] Chat: {chat_info['title']} ({chat_type})")
                chats.append(chat_info)

            logger.info(f"[CHAT_SERVICE] Processed {len(chats)} chats")
            return chats

        finally:
            await client.disconnect()

    async def get_chat_history(
        self,
        encrypted_session: str,
        chat_id: int,
        limit: int = 100,
        offset_id: int = 0,
        offset_date: Optional[datetime] = None,
        min_id: int = 0,
        max_id: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get full chat history - the main advantage of using Telethon!
        Can retrieve ALL messages, not just those after bot joined.
        """
        logger.info(f"[CHAT_SERVICE] Getting chat history for {chat_id}")
        logger.info(f"[CHAT_SERVICE] Limit: {limit}, offset_id: {offset_id}")

        client = await self._get_client(encrypted_session)

        try:
            # Get the chat entity
            entity = await client.get_entity(chat_id)
            logger.info(f"[CHAT_SERVICE] Got entity: {type(entity).__name__}")

            # Get messages
            messages = await client.get_messages(
                entity,
                limit=limit,
                offset_id=offset_id,
                offset_date=offset_date,
                min_id=min_id,
                max_id=max_id,
                reverse=False,  # Get newest first
            )

            logger.info(f"[CHAT_SERVICE] Retrieved {len(messages)} messages")

            # Process messages
            processed_messages = []
            for msg in messages:
                if not isinstance(msg, TgMessage):
                    continue

                # Get sender info
                sender_name = "Unknown"
                if msg.sender:
                    if isinstance(msg.sender, TgUser):
                        sender_name = f"{msg.sender.first_name or ''} {msg.sender.last_name or ''}".strip()
                        if not sender_name:
                            sender_name = msg.sender.username or f"User{msg.sender.id}"
                    elif hasattr(msg.sender, "title"):
                        sender_name = msg.sender.title

                # Detect media type
                media_type = None
                if msg.photo:
                    media_type = "photo"
                elif msg.document:
                    media_type = "document"
                elif msg.video:
                    media_type = "video"
                elif msg.voice:
                    media_type = "voice"
                elif msg.audio:
                    media_type = "audio"
                elif msg.sticker:
                    media_type = "sticker"
                elif msg.gif:
                    media_type = "gif"

                message_info = {
                    "id": msg.id,
                    "text": msg.text or msg.message or "",
                    "date": msg.date.isoformat(),
                    "sender_id": msg.sender_id,
                    "sender_name": sender_name,
                    "reply_to_msg_id": msg.reply_to_msg_id,
                    "has_media": bool(msg.media),
                    "media_type": media_type,
                    "views": msg.views,
                    "forwards": msg.forwards,
                    "edit_date": msg.edit_date.isoformat() if msg.edit_date else None,
                    "is_pinned": msg.pinned,
                    "is_mentioned": msg.mentioned,
                    "is_media_unread": msg.media_unread,
                }

                processed_messages.append(message_info)

            logger.info(f"[CHAT_SERVICE] Processed {len(processed_messages)} messages")
            return processed_messages

        finally:
            await client.disconnect()

    async def index_chat(
        self,
        encrypted_session: str,
        chat_id: int,
        batch_size: int = 100,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Index all messages from a chat into the database.
        This can retrieve the ENTIRE chat history, not just recent messages.
        """
        logger.info(f"[CHAT_SERVICE] Starting to index chat {chat_id}")
        logger.info(f"[CHAT_SERVICE] Batch size: {batch_size}")

        client = await self._get_client(encrypted_session)

        try:
            # Get chat entity
            entity = await client.get_entity(chat_id)

            # Determine chat details
            if isinstance(entity, Channel):
                chat_type = "channel" if entity.broadcast else "supergroup"
                chat_title = entity.title
            elif isinstance(entity, Chat):
                chat_type = "group"
                chat_title = entity.title
            elif isinstance(entity, TgUser):
                chat_type = "private"
                chat_title = (
                    f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                )
            else:
                raise ValueError(f"Unknown entity type: {type(entity)}")

            logger.info(f"[CHAT_SERVICE] Indexing {chat_type} chat: {chat_title}")

            # Save chat to database
            async with get_db() as db:
                # Check if chat exists
                result = await db.execute(
                    select(DBChat).where(DBChat.chat_id == chat_id)
                )
                db_chat = result.scalar_one_or_none()

                if not db_chat:
                    db_chat = DBChat(chat_id=chat_id, title=chat_title, type=chat_type)
                    db.add(db_chat)
                    await db.commit()
                    await db.refresh(db_chat)
                    logger.info(f"[CHAT_SERVICE] Created new chat in database")
                else:
                    # Update chat info
                    db_chat.title = chat_title
                    db_chat.type = chat_type
                    await db.commit()
                    logger.info(f"[CHAT_SERVICE] Updated existing chat in database")

            # Index messages in batches
            total_messages = 0
            offset_id = 0
            indexed_messages = []

            while True:
                # Get batch of messages
                messages = await client.get_messages(
                    entity, limit=batch_size, offset_id=offset_id
                )

                if not messages:
                    logger.info(f"[CHAT_SERVICE] No more messages to index")
                    break

                logger.info(
                    f"[CHAT_SERVICE] Processing batch of {len(messages)} messages"
                )

                # Process and save messages
                async with get_db() as db:
                    for msg in messages:
                        if not isinstance(msg, TgMessage):
                            continue

                        # Check if message exists
                        result = await db.execute(
                            select(DBMessage).where(
                                DBMessage.chat_id == db_chat.id,
                                DBMessage.msg_id == msg.id,
                            )
                        )
                        existing = result.scalar_one_or_none()

                        if existing:
                            logger.debug(
                                f"[CHAT_SERVICE] Message {msg.id} already indexed"
                            )
                            continue

                        # Create new message
                        db_message = DBMessage(
                            chat_id=db_chat.id,
                            msg_id=msg.id,
                            sender_id=msg.sender_id,
                            sender_name=self._get_sender_name(msg),
                            text=msg.text or msg.message or "",
                            date=msg.date,
                            reply_to_msg_id=msg.reply_to_msg_id,
                            has_media=bool(msg.media),
                            media_type=self._get_media_type(msg),
                        )
                        db.add(db_message)
                        indexed_messages.append(msg.id)

                    await db.commit()
                    logger.info(f"[CHAT_SERVICE] Saved batch to database")

                total_messages += len(messages)
                offset_id = messages[-1].id

                # Progress callback
                if progress_callback:
                    await progress_callback(
                        {
                            "chat_id": chat_id,
                            "indexed": total_messages,
                            "current_batch": len(messages),
                            "oldest_date": messages[-1].date.isoformat(),
                        }
                    )

                logger.info(f"[CHAT_SERVICE] Total indexed so far: {total_messages}")

                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)

                # If we got less than batch_size, we're done
                if len(messages) < batch_size:
                    logger.info(f"[CHAT_SERVICE] Reached end of chat history")
                    break

            logger.info(f"[CHAT_SERVICE] Indexing complete!")
            logger.info(f"[CHAT_SERVICE] Total messages indexed: {total_messages}")

            return {
                "chat_id": chat_id,
                "chat_title": chat_title,
                "chat_type": chat_type,
                "total_messages": total_messages,
                "new_messages": len(indexed_messages),
                "status": "completed",
            }

        except Exception as e:
            logger.error(
                f"[CHAT_SERVICE] Error indexing chat: {type(e).__name__}: {str(e)}"
            )
            raise
        finally:
            await client.disconnect()

    def _get_sender_name(self, msg: TgMessage) -> str:
        """Extract sender name from message"""
        if not msg.sender:
            return "Unknown"

        if isinstance(msg.sender, TgUser):
            name = f"{msg.sender.first_name or ''} {msg.sender.last_name or ''}".strip()
            if not name:
                name = msg.sender.username or f"User{msg.sender.id}"
            return name
        elif hasattr(msg.sender, "title"):
            return msg.sender.title
        else:
            return "Unknown"

    def _get_media_type(self, msg: TgMessage) -> Optional[str]:
        """Determine media type from message"""
        if not msg.media:
            return None

        if msg.photo:
            return "photo"
        elif msg.document:
            return "document"
        elif msg.video:
            return "video"
        elif msg.voice:
            return "voice"
        elif msg.audio:
            return "audio"
        elif msg.sticker:
            return "sticker"
        elif msg.gif:
            return "gif"
        else:
            return "other"
