from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Message, MessageEmbedding, Timeline, User
from utils.logging import setup_logger
from utils.security import (
    create_safe_prompt,
    detect_injection_attempt,
    log_security_event,
    sanitize_query,
    validate_timeline_query,
)

logger = setup_logger(__name__)


class RAGService:
    def __init__(self, db: Optional[AsyncSession] = None):
        import os

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large", openai_api_key=openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        self.db = db

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a text using OpenAI's text-embedding-3-large model."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-large", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for processing."""
        try:
            chunks = self.text_splitter.split_text(text)
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    async def query(
        self,
        user_id: int,
        query: str,
        max_results: int = 10,
        include_images: bool = True,
    ) -> dict:
        """Perform semantic search on user's messages with security checks."""
        try:
            # Sanitize query
            query = sanitize_query(query)

            # Check for injection attempts
            injection_pattern = detect_injection_attempt(query)
            if injection_pattern:
                log_security_event(
                    user_id=user_id,
                    event_type="prompt_injection_attempt",
                    details={"pattern": injection_pattern, "query": query[:100]},
                )
                # Continue with search but log the attempt

            # Generate query embedding
            query_embedding = await self.embed_text(query)

            # Find relevant messages using vector similarity search
            # Note: Using pgvector's <-> operator for cosine distance

            sql_query = text(
                """
                SELECT DISTINCT m.*, me.chunk_text, 
                       1 - (me.embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM messages m
                JOIN message_embeddings me ON m.id = me.message_id
                JOIN user_messages um ON m.id = um.message_id
                WHERE um.user_id = :user_id
                ORDER BY me.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """
            )

            results = await self.db.execute(
                sql_query,
                {
                    "query_embedding": query_embedding,
                    "user_id": user_id,
                    "limit": max_results,
                },
            )

            messages = []
            for row in results:
                messages.append(
                    {
                        "id": row.id,
                        "text": row.text,
                        "chunk_text": row.chunk_text,
                        "date": row.date.isoformat(),
                        "chat_id": row.chat_id,
                        "msg_id": row.msg_id,
                        "similarity": float(row.similarity),
                        "sender_name": row.sender_name,
                    }
                )

            # Get chat information for context
            from models.models import Chat

            chat_ids = list(set(msg["chat_id"] for msg in messages))
            chats_result = await self.db.execute(
                select(Chat).where(Chat.id.in_(chat_ids))
            )
            chats = {chat.id: chat for chat in chats_result.scalars().all()}

            # Generate AI response using context
            context_messages = []
            sources = []

            for msg in messages:
                chat = chats.get(msg["chat_id"])
                chat_name = chat.title if chat else "Unknown"

                # Build Telegram URL
                url = f"https://t.me/c/{msg['chat_id']}/{msg['msg_id']}"

                context_messages.append(
                    {
                        "text": msg["text"],
                        "chunk": msg["chunk_text"],
                        "date": msg["date"],
                        "chat": chat_name,
                        "sender": msg["sender_name"],
                    }
                )

                sources.append(
                    {
                        "text": msg["text"][:200] + "..."
                        if len(msg["text"]) > 200
                        else msg["text"],
                        "url": url,
                        "date": msg["date"],
                        "chat_name": chat_name,
                        "relevance_score": msg["similarity"],
                    }
                )

            # Generate AI response
            ai_response = await self.generate_ai_response(
                user_id, query, context_messages, self.db
            )

            return {
                "query": query,
                "answer": ai_response["answer"],
                "sources": sources[:5],  # Top 5 sources
                "confidence": ai_response["confidence"],
            }
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            raise

    async def generate_timeline(
        self,
        user_id: int,
        query: str,
        start_date=None,
        end_date=None,
        max_items: int = 50,
    ) -> dict:
        """Generate a timeline of messages based on semantic search."""
        try:
            # Validate timeline query
            if not validate_timeline_query(query):
                log_security_event(
                    user_id=user_id,
                    event_type="invalid_timeline_query",
                    details={"query": query[:100]},
                )
                raise ValueError("Invalid timeline query format")

            # Find similar messages for timeline
            similar_messages = await self.find_similar(
                user_id, query, max_results=max_items
            )

            # Filter by date range if provided
            if start_date:
                similar_messages = [
                    msg
                    for msg in similar_messages
                    if msg["date"] >= start_date.isoformat()
                ]
            if end_date:
                similar_messages = [
                    msg
                    for msg in similar_messages
                    if msg["date"] <= end_date.isoformat()
                ]

            # Sort messages by date
            messages = sorted(similar_messages, key=lambda x: x["date"])

            # Convert to timeline format as per PRD
            timeline_items = []
            for msg in messages:
                timeline_items.append(
                    {
                        "ts": msg["date"],
                        "text": msg["text"],
                        "url": msg["url"],
                        "chat_name": msg["chat_name"],
                        "sender": msg.get("sender_name", "Unknown"),
                    }
                )

            # Store timeline in database
            timeline_record = Timeline(
                user_id=user_id, query=query, result={"items": timeline_items}
            )
            self.db.add(timeline_record)
            await self.db.commit()

            return {
                "query": query,
                "items": timeline_items,
                "total_items": len(timeline_items),
            }
        except Exception as e:
            logger.error(f"Error generating timeline: {str(e)}")
            raise

    async def generate_ai_response(
        self, user_id: int, query: str, context_messages: List[dict], db: AsyncSession
    ) -> dict:
        """
        Generate AI response based on user's messages (FUTURE IMPLEMENTATION).
        This method includes security measures to prevent prompt injection.
        """
        try:
            # Sanitize query
            query = sanitize_query(query)

            # Detect injection attempts
            injection_pattern = detect_injection_attempt(query)
            if injection_pattern:
                log_security_event(
                    user_id=user_id,
                    event_type="prompt_injection_blocked",
                    details={"pattern": injection_pattern, "query": query[:100]},
                )
                # Return generic response instead of processing suspicious query
                return {
                    "answer": "I can help you search through your messages. Please provide a specific question about your message history.",
                    "confidence": 0.0,
                    "sources": [],
                }

            # Create safe prompt structure
            prompt = create_safe_prompt(query, context_messages)

            # Generate response with OpenAI
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {
                        "role": "user",
                        "content": f"Context:\n{self._format_context(prompt['context'])}\n\nQuestion: {prompt['query']}",
                    },
                ],
                max_tokens=prompt["max_tokens"],
                temperature=prompt["temperature"],
                presence_penalty=0.1,
                frequency_penalty=0.1,
            )

            answer = response.choices[0].message.content

            # Log successful query for monitoring
            logger.info(
                "AI response generated",
                extra={
                    "user_id": user_id,
                    "query_length": len(query),
                    "context_messages": len(context_messages),
                    "response_length": len(answer),
                },
            )

            return {
                "answer": answer,
                "confidence": 0.85,  # Could be calculated based on context relevance
                "sources": context_messages[:5],  # Return top 5 most relevant sources
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise

    def _format_context(self, context: List[dict]) -> str:
        """Format context messages for prompt."""
        formatted = []
        for msg in context:
            formatted.append(
                f"Date: {msg['date']}\n"
                f"Chat: {msg['chat']}\n"
                f"Message: {msg['text']}\n"
            )
        return "\n---\n".join(formatted)

    async def find_similar(
        self, user_id: int, query: str, max_results: int = 10
    ) -> List[dict]:
        """Find messages similar to query without generating AI response."""
        try:
            # Sanitize query
            query = sanitize_query(query)

            # Generate query embedding
            query_embedding = await self.embed_text(query)

            # Find similar messages
            sql_query = text(
                """
                SELECT DISTINCT m.*, me.chunk_text,
                       1 - (me.embedding <=> CAST(:query_embedding AS vector)) as similarity,
                       c.title as chat_title
                FROM messages m
                JOIN message_embeddings me ON m.id = me.message_id
                JOIN user_messages um ON m.id = um.message_id
                JOIN chats c ON m.chat_id = c.id
                WHERE um.user_id = :user_id
                ORDER BY me.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """
            )

            results = await self.db.execute(
                sql_query,
                {
                    "query_embedding": query_embedding,
                    "user_id": user_id,
                    "limit": max_results,
                },
            )

            similar_messages = []
            for row in results:
                similar_messages.append(
                    {
                        "id": row.id,
                        "text": row.text,
                        "date": row.date.isoformat(),
                        "chat_name": row.chat_title,
                        "chat_id": row.chat_id,
                        "msg_id": row.msg_id,
                        "similarity": float(row.similarity),
                        "url": f"https://t.me/c/{row.chat_id}/{row.msg_id}",
                    }
                )

            return similar_messages

        except Exception as e:
            logger.error(f"Error finding similar messages: {str(e)}")
            raise
