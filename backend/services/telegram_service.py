import logging
from typing import List, Dict, Optional
from telethon import TelegramClient
from telethon.tl.types import Message, Chat, User
from telethon.errors import SessionPasswordNeededError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import qrcode
import io
import base64

from models.models import User, Chat as DBChat, Message as DBMessage, UserMessage, MessageImage
from utils.logging import setup_logger

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

    async def generate_qr_login(self, user_id: int) -> dict:
        """Generate QR code for Telegram login."""
        try:
            session_file = f"sessions/user_{user_id}"
            client = TelegramClient(session_file, self.api_id, self.api_hash)
            await client.connect()
            
            if await client.is_user_authorized():
                return {"status": "already_authorized"}
            
            qr = await client.qr_login()
            qr_image = qrcode.make(qr.url)
            
            # Convert QR code to base64
            buffer = io.BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "status": "qr_generated",
                "qr_code": qr_base64,
                "session_file": session_file
            }
        except Exception as e:
            logger.error(f"Error generating QR login: {str(e)}")
            raise

    async def get_user_chats(self, session_file: str) -> List[dict]:
        """Get all chats for the authenticated user."""
        try:
            client = await self._get_client(session_file)
            dialogs = await client.get_dialogs()
            
            chats = []
            for dialog in dialogs:
                entity = dialog.entity
                if isinstance(entity, (Chat, User)):
                    chat_data = {
                        "id": entity.id,
                        "title": getattr(entity, "title", None) or f"{entity.first_name} {entity.last_name or ''}",
                        "type": "channel" if getattr(entity, "broadcast", False) else "group" if getattr(entity, "megagroup", False) else "private"
                    }
                    chats.append(chat_data)
            
            return chats
        except Exception as e:
            logger.error(f"Error getting user chats: {str(e)}")
            raise

    async def index_chat(self, user_id: int, chat_id: int, db: AsyncSession) -> None:
        """Index messages from a chat for the user."""
        try:
            # Get user's session file
            user = await db.execute(select(User).where(User.id == user_id))
            user = user.scalar_one()
            client = await self._get_client(user.session_file)
            
            # Get or create chat in database
            db_chat = await db.execute(select(DBChat).where(DBChat.chat_id == chat_id))
            db_chat = db_chat.scalar_one_or_none()
            
            if not db_chat:
                chat_entity = await client.get_entity(chat_id)
                db_chat = DBChat(
                    chat_id=chat_id,
                    title=getattr(chat_entity, "title", None) or f"{chat_entity.first_name} {chat_entity.last_name or ''}",
                    type="channel" if getattr(chat_entity, "broadcast", False) else "group" if getattr(chat_entity, "megagroup", False) else "private"
                )
                db.add(db_chat)
                await db.commit()
            
            # Get messages
            messages = await client.get_messages(chat_id, limit=None)
            
            for msg in messages:
                if not isinstance(msg, Message):
                    continue
                
                # Check if message already exists
                existing_msg = await db.execute(
                    select(DBMessage).where(
                        DBMessage.chat_id == db_chat.id,
                        DBMessage.msg_id == msg.id
                    )
                )
                if existing_msg.scalar_one_or_none():
                    continue
                
                # Create message record
                db_message = DBMessage(
                    chat_id=db_chat.id,
                    msg_id=msg.id,
                    sender_id=msg.sender_id,
                    sender_name=getattr(msg.sender, "first_name", "") + " " + getattr(msg.sender, "last_name", ""),
                    text=msg.text or msg.raw_text or "",
                    date=msg.date,
                    reply_to_msg_id=msg.reply_to_msg_id,
                    has_media=bool(msg.media),
                    media_type=msg.media.__class__.__name__ if msg.media else None
                )
                db.add(db_message)
                await db.commit()
                
                # Create user-message association
                user_message = UserMessage(
                    user_id=user_id,
                    message_id=db_message.id
                )
                db.add(user_message)
                
                # Handle media if present
                if msg.media:
                    # TODO: Implement media handling (images, documents, etc.)
                    pass
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error indexing chat: {str(e)}")
            raise 