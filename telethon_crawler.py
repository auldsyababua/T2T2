#!/usr/bin/env python3
"""
Telethon crawler for T2T2 bot - crawls Telegram chat history
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.supabase_bot")

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")


class TelethonCrawler:
    """Crawl Telegram chat history using Telethon"""

    def __init__(self, session_string: Optional[str] = None):
        """Initialize crawler with optional session string"""
        self.session = (
            StringSession(session_string) if session_string else StringSession()
        )
        self.client = TelegramClient(self.session, API_ID, API_HASH)
        self.messages_batch = []
        self.batch_size = 100

        logger.info("Initialized Telethon crawler")

    async def connect(self) -> bool:
        """Connect to Telegram"""
        try:
            await self.client.connect()
            if await self.client.is_user_authorized():
                logger.info("✅ Connected and authorized")
                return True
            else:
                logger.warning("❌ Connected but not authorized")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def authenticate_phone(self, phone_number: str) -> str:
        """Authenticate with phone number"""
        logger.info(f"Starting authentication for {phone_number}")

        try:
            await self.client.send_code_request(phone_number)
            logger.info("✅ Code sent to phone")
            return "CODE_SENT"
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return f"ERROR: {e}"

    async def verify_code(self, phone_number: str, code: str) -> str:
        """Verify the code"""
        try:
            await self.client.sign_in(phone_number, code)
            session_string = self.client.session.save()
            logger.info("✅ Authentication successful")
            return session_string
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return f"ERROR: {e}"

    async def get_dialogs(self, limit: int = 50) -> List[Dict]:
        """Get list of chats/dialogs"""
        logger.info(f"Fetching dialogs (limit: {limit})")

        dialogs = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            dialog_info = {
                "id": dialog.id,
                "title": dialog.title,
                "name": dialog.name,
                "is_user": dialog.is_user,
                "is_group": dialog.is_group,
                "is_channel": dialog.is_channel,
                "unread_count": dialog.unread_count,
                "last_message_date": dialog.date.isoformat() if dialog.date else None,
            }
            dialogs.append(dialog_info)
            logger.info(f"  - {dialog.title or dialog.name} (ID: {dialog.id})")

        logger.info(f"✅ Found {len(dialogs)} dialogs")
        return dialogs

    async def crawl_chat(
        self,
        chat_id: int,
        limit: int = 1000,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """Crawl messages from a specific chat"""
        logger.info(f"Crawling chat {chat_id} (limit: {limit})")

        messages = []
        message_count = 0

        try:
            # Get chat entity
            entity = await self.client.get_entity(chat_id)
            chat_title = (
                getattr(entity, "title", None)
                or getattr(entity, "username", None)
                or str(chat_id)
            )

            logger.info(f"Crawling '{chat_title}'...")

            # Iterate through messages
            async for message in self.client.iter_messages(
                entity,
                limit=limit,
                min_date=min_date,
                max_date=max_date,
                reverse=False,  # Get oldest first
            ):
                message_count += 1

                # Extract message data
                msg_data = await self._extract_message_data(message, chat_title)
                messages.append(msg_data)

                # Log progress
                if message_count % 100 == 0:
                    logger.info(f"  Processed {message_count} messages...")

                # Add to batch
                self.messages_batch.append(msg_data)

                # Process batch if full
                if len(self.messages_batch) >= self.batch_size:
                    await self._process_message_batch()

            # Process remaining messages
            if self.messages_batch:
                await self._process_message_batch()

            logger.info(f"✅ Crawled {message_count} messages from '{chat_title}'")

        except Exception as e:
            logger.error(f"Error crawling chat {chat_id}: {e}")

        return messages

    async def _extract_message_data(self, message: Message, chat_title: str) -> Dict:
        """Extract relevant data from a message"""
        # Get sender info
        sender_id = message.sender_id if message.sender_id else "unknown"
        sender_name = "Unknown"

        if message.sender:
            if hasattr(message.sender, "first_name"):
                sender_name = message.sender.first_name or ""
                if hasattr(message.sender, "last_name") and message.sender.last_name:
                    sender_name += f" {message.sender.last_name}"
            elif hasattr(message.sender, "title"):
                sender_name = message.sender.title

        # Build message data
        msg_data = {
            "message_id": message.id,
            "chat_id": message.chat_id,
            "chat_title": chat_title,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "date": message.date.isoformat() if message.date else None,
            "text": message.text or "",
            "has_media": bool(message.media),
            "media_type": self._get_media_type(message) if message.media else None,
            "reply_to_msg_id": message.reply_to_msg_id,
            "forward_from": message.forward.sender_id if message.forward else None,
            "views": message.views,
            "is_pinned": message.pinned,
            "raw_text": message.raw_text or "",
        }

        # Handle media
        if message.media:
            msg_data["media_info"] = await self._extract_media_info(message)

        return msg_data

    def _get_media_type(self, message: Message) -> Optional[str]:
        """Determine media type"""
        if not message.media:
            return None

        media = message.media
        if hasattr(media, "photo"):
            return "photo"
        elif hasattr(media, "document"):
            doc = media.document
            if doc.mime_type.startswith("image/"):
                return "image"
            elif doc.mime_type.startswith("video/"):
                return "video"
            elif doc.mime_type.startswith("audio/"):
                return "audio"
            else:
                return "document"
        else:
            return "other"

    async def _extract_media_info(self, message: Message) -> Dict:
        """Extract media information"""
        media_info = {
            "type": self._get_media_type(message),
            "telegram_file_id": None,
            "file_size": None,
            "mime_type": None,
            "filename": None,
        }

        try:
            if hasattr(message.media, "photo"):
                # Photo
                media_info["telegram_file_id"] = str(message.media.photo.id)
                media_info["file_size"] = (
                    message.media.photo.sizes[-1].size
                    if message.media.photo.sizes
                    else None
                )
                media_info["mime_type"] = "image/jpeg"
            elif hasattr(message.media, "document"):
                # Document/Video/Audio
                doc = message.media.document
                media_info["telegram_file_id"] = str(doc.id)
                media_info["file_size"] = doc.size
                media_info["mime_type"] = doc.mime_type

                # Get filename from attributes
                for attr in doc.attributes:
                    if hasattr(attr, "file_name"):
                        media_info["filename"] = attr.file_name
                        break

        except Exception as e:
            logger.warning(f"Error extracting media info: {e}")

        return media_info

    async def _process_message_batch(self):
        """Process a batch of messages (override in subclass)"""
        logger.info(f"Processing batch of {len(self.messages_batch)} messages")
        # This will be overridden to save to Supabase
        self.messages_batch = []

    async def download_media(
        self, message: Message, download_path: str = "./downloads"
    ) -> Optional[str]:
        """Download media from a message"""
        if not message.media:
            return None

        try:
            Path(download_path).mkdir(parents=True, exist_ok=True)

            # Download the file
            path = await message.download_media(file=download_path)
            logger.info(f"✅ Downloaded media to: {path}")
            return path

        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None

    async def close(self):
        """Close the client connection"""
        await self.client.disconnect()
        logger.info("Disconnected from Telegram")


async def main():
    """Test the crawler"""
    crawler = TelethonCrawler()

    if await crawler.connect():
        # Get dialogs
        dialogs = await crawler.get_dialogs(limit=10)

        # Save dialogs for reference
        with open("dialogs.json", "w") as f:
            json.dump(dialogs, f, indent=2)

        logger.info(f"Saved {len(dialogs)} dialogs to dialogs.json")
    else:
        logger.error("Not authorized. Run authentication first.")

    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
