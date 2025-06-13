from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from sqlalchemy import func, select
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
        self, user_id: int, query: str, db: AsyncSession, max_results: int = 10
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
            results = await db.execute(
                select(
                    Message,
                    func.cosine_similarity(
                        MessageEmbedding.embedding, query_embedding
                    ).label("similarity"),
                )
                .join(MessageEmbedding)
                .join(User, Message.id == User.id)
                .where(User.id == user_id)
                .order_by(
                    func.cosine_similarity(
                        MessageEmbedding.embedding, query_embedding
                    ).desc()
                )
                .limit(max_results)
            )

            messages = []
            for msg, similarity in results:
                messages.append(
                    {
                        "id": msg.id,
                        "text": msg.text,
                        "date": msg.date.isoformat(),
                        "chat_id": msg.chat_id,
                        "msg_id": msg.msg_id,
                        "similarity": float(similarity),
                    }
                )

            return {"query": query, "results": messages}
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            raise

    async def generate_timeline(
        self, user_id: int, query: str, db: AsyncSession
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

            # Perform semantic search (query method already sanitizes)
            search_results = await self.query(user_id, query, max_results=100, db=db)

            # Sort messages by date
            messages = sorted(search_results["results"], key=lambda x: x["date"])

            # Group messages by date
            timeline = {}
            for msg in messages:
                date = msg["date"].split("T")[0]  # Get just the date part
                if date not in timeline:
                    timeline[date] = []
                timeline[date].append(msg)

            # Store timeline in database
            timeline_record = Timeline(
                user_id=user_id, query=query, result={"timeline": timeline}
            )
            db.add(timeline_record)
            await db.commit()

            return {
                "query": query,
                "timeline": timeline,
                "timeline_id": timeline_record.id,
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
