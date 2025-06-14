"""Service for generating and managing embeddings for messages."""
import os
from typing import List, Optional, Dict

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.models import Message, MessageEmbedding
from backend.services.smart_chunking_service import SmartChunkingService
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = "text-embedding-3-large"
        
        # Use smart chunking service instead of simple text splitter
        self.chunking_service = SmartChunkingService()

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text chunk."""
        try:
            response = await self.client.embeddings.create(model=self.model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def chunk_and_embed_message(
        self, message: Message, db: AsyncSession, additional_text: Optional[str] = None
    ) -> List[MessageEmbedding]:
        """Chunk a message and generate embeddings for each chunk."""
        try:
            # Combine message text with any additional text (e.g., OCR results)
            full_text = message.text or ""
            if additional_text:
                full_text = f"{full_text}\n\n{additional_text}"

            if not full_text.strip():
                logger.debug(f"Message {message.id} has no text to embed")
                return []

            # Split text into chunks
            chunks = self.text_splitter.split_text(full_text)

            embeddings = []
            for i, chunk in enumerate(chunks):
                # Check if chunk already exists
                existing = await db.execute(
                    select(MessageEmbedding).where(
                        MessageEmbedding.message_id == message.id,
                        MessageEmbedding.chunk_index == i,
                    )
                )
                if existing.scalar_one_or_none():
                    logger.debug(
                        f"Chunk {i} for message {message.id} already exists, skipping"
                    )
                    continue

                # Generate embedding
                embedding_vector = await self.generate_embedding(chunk)

                # Create embedding record
                embedding = MessageEmbedding(
                    message_id=message.id,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=embedding_vector,
                )
                db.add(embedding)
                embeddings.append(embedding)

            await db.commit()
            logger.info(
                f"Created {len(embeddings)} embeddings for message {message.id}"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Error chunking and embedding message {message.id}: {str(e)}")
            raise

    async def embed_messages_batch(
        self, messages: List[Message], db: AsyncSession, progress_callback=None
    ) -> int:
        """Embed multiple messages in batch with optional progress callback."""
        total_embedded = 0

        for i, message in enumerate(messages):
            try:
                embeddings = await self.chunk_and_embed_message(message, db)
                total_embedded += len(embeddings)

                if progress_callback and (i + 1) % 10 == 0:
                    await progress_callback(i + 1, len(messages))

            except Exception as e:
                logger.error(f"Failed to embed message {message.id}: {str(e)}")
                # Continue with other messages

        return total_embedded
