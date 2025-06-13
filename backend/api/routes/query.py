from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from db.database import get_db
from models.models import User
from services.rag_service import RAGService

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    max_results: int = 10
    include_images: bool = True


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: float


class Source(BaseModel):
    text: str
    url: str
    date: str
    chat_name: str
    relevance_score: float


@router.post("/", response_model=QueryResponse)
async def query_messages(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query user's indexed messages using RAG"""

    rag_service = RAGService(db)

    # Set user context for RLS (PostgreSQL only)
    if not db.bind.url.drivername.startswith("sqlite"):
        await db.execute(
            text("SET app.user_id = :user_id"), {"user_id": current_user.id}
        )

    try:
        # Pass db to RAG service
        rag_service.db = db

        result = await rag_service.query(
            user_id=current_user.id,
            query=request.query,
            max_results=request.max_results,
            include_images=request.include_images,
        )

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def find_similar_messages(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Find messages similar to the query without generating an answer"""

    rag_service = RAGService(db)

    # Set user context for RLS (PostgreSQL only)
    if not db.bind.url.drivername.startswith("sqlite"):
        await db.execute(
            text("SET app.user_id = :user_id"), {"user_id": current_user.id}
        )

    try:
        # Pass db to RAG service
        rag_service.db = db

        similar_messages = await rag_service.find_similar(
            user_id=current_user.id,
            query=request.query,
            max_results=request.max_results,
        )

        return {"query": request.query, "results": similar_messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
