"""Service for intelligent message chunking with context preservation."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.models import Message, Chat
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class SmartChunkingService:
    """Handles intelligent message grouping and chunking for embeddings."""

    def __init__(
        self,
        max_chunk_size: int = 400,
        group_time_window_seconds: int = 120,
        likely_response_window_seconds: int = 30,
    ):
        self.max_chunk_size = max_chunk_size
        self.group_time_window = timedelta(seconds=group_time_window_seconds)
        self.likely_response_window = timedelta(seconds=likely_response_window_seconds)

    async def group_messages_for_chunking(
        self, messages: List[Message], db: AsyncSession
    ) -> List[Dict]:
        """
        Group messages intelligently for chunking.
        Returns a list of chunk dictionaries with metadata.
        """
        if not messages:
            return []

        # Sort messages by date
        sorted_messages = sorted(messages, key=lambda m: m.date)

        # Get chat information
        chat_ids = list(set(m.chat_id for m in messages))
        chats_result = await db.execute(select(Chat).where(Chat.id.in_(chat_ids)))
        chats = {chat.id: chat for chat in chats_result.scalars().all()}

        chunks = []
        current_group = []
        current_group_text = ""

        for i, msg in enumerate(sorted_messages):
            chat = chats.get(msg.chat_id)

            # Check if we should start a new chunk
            should_break = False

            if current_group:
                last_msg = current_group[-1]

                # Different user
                if msg.sender_id != last_msg.sender_id:
                    should_break = True

                # Too much time passed
                elif (msg.date - last_msg.date) > self.group_time_window:
                    should_break = True

                # Message is a reply (break the group)
                elif msg.reply_to_msg_id:
                    should_break = True

                # Combined length would exceed limit
                elif (
                    len(current_group_text) + len(msg.text or "") + 10
                    > self.max_chunk_size
                ):
                    should_break = True

            if should_break and current_group:
                # Create chunk from current group
                chunk = await self._create_chunk_from_group(
                    current_group, chats, sorted_messages, chunks
                )
                chunks.append(chunk)
                current_group = []
                current_group_text = ""

            # Add message to current group or create new chunk
            if msg.reply_to_msg_id or len(msg.text or "") > self.max_chunk_size:
                # This message needs its own chunk
                if current_group:
                    # First save current group
                    chunk = await self._create_chunk_from_group(
                        current_group, chats, sorted_messages, chunks
                    )
                    chunks.append(chunk)
                    current_group = []
                    current_group_text = ""

                # Create individual chunk
                chunk = await self._create_chunk_from_message(
                    msg, chat, sorted_messages, chunks
                )
                chunks.append(chunk)
            else:
                # Add to group
                current_group.append(msg)
                if current_group_text:
                    current_group_text += " "
                current_group_text += msg.text or ""

        # Don't forget the last group
        if current_group:
            chunk = await self._create_chunk_from_group(
                current_group, chats, sorted_messages, chunks
            )
            chunks.append(chunk)

        return chunks

    async def _create_chunk_from_group(
        self,
        messages: List[Message],
        chats: Dict[int, Chat],
        all_messages: List[Message],
        previous_chunks: List[Dict],
    ) -> Dict:
        """Create a chunk from a group of messages."""
        first_msg = messages[0]
        last_msg = messages[-1]
        chat = chats.get(first_msg.chat_id)

        # Combine text
        combined_text = " ".join(msg.text or "" for msg in messages)

        # Check if this might be a response to a recent question
        likely_response_to = await self._find_likely_question(
            first_msg, all_messages, previous_chunks
        )

        metadata = {
            "timestamp": first_msg.date.isoformat() + "Z",
            "chat_name": chat.title if chat else "Unknown",
            "chat_id": first_msg.chat_id,
            "msg_ids": [msg.msg_id for msg in messages],
            "message_links": [
                f"https://t.me/c/{msg.chat_id}/{msg.msg_id}" for msg in messages
            ],
            "sender_name": first_msg.sender_name,
            "sender_id": first_msg.sender_id,
            "is_grouped": True,
            "message_count": len(messages),
            "time_span_seconds": (last_msg.date - first_msg.date).total_seconds(),
        }

        if likely_response_to:
            metadata["likely_response_to"] = likely_response_to

        return {"chunk_text": combined_text, "metadata": metadata, "messages": messages}

    async def _create_chunk_from_message(
        self,
        msg: Message,
        chat: Optional[Chat],
        all_messages: List[Message],
        previous_chunks: List[Dict],
    ) -> Dict:
        """Create a chunk from a single message."""
        chunk_text = msg.text or ""

        metadata = {
            "timestamp": msg.date.isoformat() + "Z",
            "chat_name": chat.title if chat else "Unknown",
            "chat_id": msg.chat_id,
            "msg_id": msg.msg_id,
            "message_link": f"https://t.me/c/{msg.chat_id}/{msg.msg_id}",
            "sender_name": msg.sender_name,
            "sender_id": msg.sender_id,
            "is_grouped": False,
        }

        # If this is a reply, get context
        if msg.reply_to_msg_id:
            metadata["reply_to_msg_id"] = msg.reply_to_msg_id

            # Find the message being replied to
            replied_msg = next(
                (
                    m
                    for m in all_messages
                    if m.msg_id == msg.reply_to_msg_id and m.chat_id == msg.chat_id
                ),
                None,
            )
            if replied_msg:
                metadata["reply_to_text"] = replied_msg.text
                metadata["reply_to_sender"] = replied_msg.sender_name

                # For very short replies, include context in chunk
                if len(chunk_text) < 50 and replied_msg.text:
                    chunk_text = f"{msg.sender_name} replied '{chunk_text}' to '{replied_msg.text[:100]}'"

        # Check if this might be a response to a recent question
        elif len(chunk_text) < 50:  # Short message, might be answer
            likely_response_to = await self._find_likely_question(
                msg, all_messages, previous_chunks
            )
            if likely_response_to:
                metadata["likely_response_to"] = likely_response_to

        # Tag questions and answers
        if chunk_text.strip().endswith("?"):
            metadata["is_question"] = True
        elif len(chunk_text) < 50 and chunk_text.lower() in [
            "yes",
            "no",
            "yeah",
            "nope",
            "yep",
            "done",
            "fixed",
            "completed",
            "not yet",
            "will do",
        ]:
            metadata["is_answer"] = True

        return {"chunk_text": chunk_text, "metadata": metadata, "messages": [msg]}

    async def _find_likely_question(
        self, msg: Message, all_messages: List[Message], previous_chunks: List[Dict]
    ) -> Optional[Dict]:
        """Find a likely question this message is responding to."""
        # Look for questions in the last minute
        cutoff_time = msg.date - self.likely_response_window

        for prev_msg in reversed(all_messages):
            if prev_msg.date < cutoff_time:
                break

            if (
                prev_msg.date < msg.date
                and prev_msg.sender_id != msg.sender_id
                and prev_msg.text
                and prev_msg.text.strip().endswith("?")
            ):
                return {
                    "msg_id": prev_msg.msg_id,
                    "text": prev_msg.text[:100],
                    "sender": prev_msg.sender_name,
                    "time_diff_seconds": (msg.date - prev_msg.date).total_seconds(),
                }

        return None
