"""Enhanced embedding service with smart chunking for timeline support."""
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
        
        # Use smart chunking service
        self.chunking_service = SmartChunkingService()

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text chunk."""
        try:
            response = await self.client.embeddings.create(
                model=self.model, 
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def embed_messages_batch(
        self, 
        messages: List[Message], 
        db: AsyncSession, 
        progress_callback=None
    ) -> int:
        """
        Embed multiple messages using smart chunking.
        Returns total number of embeddings created.
        """
        try:
            # Use smart chunking to group messages
            chunks = await self.chunking_service.group_messages_for_chunking(
                messages, db
            )
            
            total_embedded = 0
            
            for i, chunk_data in enumerate(chunks):
                try:
                    # Check if we've already embedded these messages
                    message_ids = [msg.id for msg in chunk_data["messages"]]
                    
                    # For grouped messages, check if we've already created the group
                    if chunk_data["metadata"]["is_grouped"]:
                        # Check first message in group
                        existing = await db.execute(
                            select(MessageEmbedding).where(
                                MessageEmbedding.message_id == message_ids[0],
                                MessageEmbedding.chunk_index == 0
                            )
                        )
                        if existing.scalar_one_or_none():
                            logger.debug(
                                f"Group starting with message {message_ids[0]} already embedded"
                            )
                            continue
                    
                    # Generate embedding for the chunk text
                    embedding_vector = await self.generate_embedding(
                        chunk_data["chunk_text"]
                    )
                    
                    # Create embedding record
                    # For grouped messages, associate with the first message
                    primary_message_id = message_ids[0]
                    
                    embedding = MessageEmbedding(
                        message_id=primary_message_id,
                        chunk_index=0,  # Always 0 for smart chunks
                        chunk_text=chunk_data["chunk_text"],
                        chunk_metadata=chunk_data["metadata"],
                        embedding=embedding_vector,
                    )
                    db.add(embedding)
                    total_embedded += 1
                    
                    # For very short messages that might be answers,
                    # also create a reverse reference
                    if (chunk_data["metadata"].get("is_answer") and 
                        chunk_data["metadata"].get("likely_response_to")):
                        
                        # This helps find the answer when searching for the question
                        response_ref = chunk_data["metadata"]["likely_response_to"]
                        logger.info(
                            f"Tagged answer '{chunk_data['chunk_text'][:50]}' "
                            f"as response to question msg_id {response_ref['msg_id']}"
                        )
                    
                    if progress_callback and (i + 1) % 10 == 0:
                        await progress_callback(i + 1, len(chunks))
                        
                except Exception as e:
                    logger.error(
                        f"Failed to embed chunk {i}: {str(e)}"
                    )
                    # Continue with other chunks
            
            await db.commit()
            logger.info(f"Created {total_embedded} embeddings from {len(messages)} messages")
            
            return total_embedded
            
        except Exception as e:
            logger.error(f"Error in batch embedding: {str(e)}")
            raise

    async def chunk_and_embed_message(
        self, 
        message: Message, 
        db: AsyncSession, 
        additional_text: Optional[str] = None
    ) -> List[MessageEmbedding]:
        """
        Legacy method for single message embedding.
        Now uses smart chunking under the hood.
        """
        # Add any additional text (like OCR results) to the message
        if additional_text and message.text:
            message.text = f"{message.text}\n\n{additional_text}"
        elif additional_text:
            message.text = additional_text
            
        # Use batch method with single message
        await self.embed_messages_batch([message], db)
        
        # Return the created embeddings
        result = await db.execute(
            select(MessageEmbedding).where(
                MessageEmbedding.message_id == message.id
            )
        )
        return list(result.scalars().all())