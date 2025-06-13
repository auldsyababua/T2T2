from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from db.database import get_db
from models.models import Timeline, User
from services.rag_service import RAGService

router = APIRouter()


class TimelineRequest(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_items: int = 50


class TimelineItem(BaseModel):
    ts: datetime
    text: str
    url: str
    chat_name: str
    sender: Optional[str]


class TimelineResponse(BaseModel):
    query: str
    items: List[TimelineItem]
    total_items: int


@router.post("/", response_model=TimelineResponse)
async def generate_timeline(
    request: TimelineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a timeline of events based on query"""

    rag_service = RAGService(db)

    # Set user context for RLS (PostgreSQL only)
    if not db.bind.url.drivername.startswith("sqlite"):
        await db.execute(
            text("SET app.user_id = :user_id"), {"user_id": current_user.id}
        )

    try:
        # Pass db to RAG service
        rag_service.db = db

        timeline_data = await rag_service.generate_timeline(
            user_id=current_user.id,
            query=request.query,
            start_date=request.start_date,
            end_date=request.end_date,
            max_items=request.max_items,
        )

        # Timeline is already saved in the service, no need to save again

        return TimelineResponse(
            query=request.query,
            items=timeline_data["items"],
            total_items=len(timeline_data["items"]),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved")
async def get_saved_timelines(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get user's saved timelines"""

    result = await db.execute(
        select(Timeline)
        .where(Timeline.user_id == current_user.id)
        .order_by(Timeline.created_at.desc())
        .limit(20)
    )
    timelines = result.scalars().all()

    return {
        "timelines": [
            {
                "id": t.id,
                "query": t.query,
                "created_at": t.created_at,
                "item_count": len(t.result.get("items", [])),
            }
            for t in timelines
        ]
    }


@router.get("/{timeline_id}")
async def get_timeline(
    timeline_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific saved timeline"""

    result = await db.execute(
        select(Timeline)
        .where(Timeline.id == timeline_id)
        .where(Timeline.user_id == current_user.id)
    )
    timeline = result.scalar_one_or_none()

    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")

    return {
        "id": timeline.id,
        "query": timeline.query,
        "created_at": timeline.created_at,
        "result": timeline.result,
    }
