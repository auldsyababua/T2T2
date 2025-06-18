"""
Query service for searching indexed messages.
This is a simplified version for the bot integration.
"""
import os
from typing import Dict, List, Any
from datetime import datetime

from backend.utils.logging import setup_logger
from backend.db.database import get_db
from backend.models.models import Message, Chat, UserMessage
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

logger = setup_logger(__name__)


class QueryService:
    """Service for querying indexed messages"""
    
    def __init__(self):
        """Initialize query service"""
        logger.info("[QUERY_SERVICE] Initialized")
    
    async def query_messages(self, user_id: int, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Query messages for a user.
        This is a simplified version - in production you'd use vector search.
        """
        logger.info(f"[QUERY_SERVICE] Query from user {user_id}: {query[:50]}...")
        
        async with get_db() as db:
            # For now, just do a simple text search
            # In production, this would use vector similarity search
            result = await db.execute(
                select(Message)
                .join(UserMessage, UserMessage.message_id == Message.id)
                .join(Chat, Chat.id == Message.chat_id)
                .where(UserMessage.user_id == user_id)
                .where(Message.text.ilike(f"%{query}%"))
                .order_by(Message.date.desc())
                .limit(limit)
                .options(joinedload(Message.chat))
            )
            
            messages = result.scalars().all()
            
            logger.info(f"[QUERY_SERVICE] Found {len(messages)} messages")
            
            if not messages:
                return {
                    "answer": "I couldn't find any messages matching your query.",
                    "sources": []
                }
            
            # Format results
            sources = []
            for msg in messages:
                sources.append({
                    "message_id": str(msg.id),
                    "content": msg.text[:200] + "..." if len(msg.text) > 200 else msg.text,
                    "chat_title": msg.chat.title if msg.chat else "Unknown Chat",
                    "timestamp": msg.date.isoformat(),
                    "sender_name": msg.sender_name,
                    "score": 1.0  # Placeholder for vector similarity score
                })
            
            # Generate a simple answer
            answer = f"I found {len(messages)} messages related to '{query}'. "
            if messages:
                answer += f"The most recent was from {messages[0].sender_name} in {messages[0].chat.title}."
            
            return {
                "answer": answer,
                "sources": sources
            }