import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
import numpy as np

from models.models import User, Message, MessageEmbedding, Timeline
from utils.logging import setup_logger

logger = setup_logger(__name__)

class RAGService:
    def __init__(self, openai_api_key: str):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a text using OpenAI's text-embedding-3-large model."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
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

    async def query(self, user_id: int, query: str, db: AsyncSession, max_results: int = 10) -> dict:
        """Perform semantic search on user's messages."""
        try:
            # Generate query embedding
            query_embedding = await self.embed_text(query)
            
            # Find relevant messages using vector similarity search
            results = await db.execute(
                select(
                    Message,
                    func.cosine_similarity(MessageEmbedding.embedding, query_embedding).label("similarity")
                )
                .join(MessageEmbedding)
                .join(User, Message.id == User.id)
                .where(User.id == user_id)
                .order_by(func.cosine_similarity(MessageEmbedding.embedding, query_embedding).desc())
                .limit(max_results)
            )
            
            messages = []
            for msg, similarity in results:
                messages.append({
                    "id": msg.id,
                    "text": msg.text,
                    "date": msg.date.isoformat(),
                    "chat_id": msg.chat_id,
                    "msg_id": msg.msg_id,
                    "similarity": float(similarity)
                })
            
            return {
                "query": query,
                "results": messages
            }
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            raise

    async def generate_timeline(self, user_id: int, query: str, db: AsyncSession) -> dict:
        """Generate a timeline of messages based on semantic search."""
        try:
            # Perform semantic search
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
                user_id=user_id,
                query=query,
                result={"timeline": timeline}
            )
            db.add(timeline_record)
            await db.commit()
            
            return {
                "query": query,
                "timeline": timeline,
                "timeline_id": timeline_record.id
            }
        except Exception as e:
            logger.error(f"Error generating timeline: {str(e)}")
            raise 