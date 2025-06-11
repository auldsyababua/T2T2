from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from db.database import get_db
from api.routes.auth import get_current_user
from models.models import User, Timeline
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
    db: AsyncSession = Depends(get_db)
):
    """Generate a timeline of events based on query"""
    
    rag_service = RAGService(db)
    
    # Set user context for RLS
    await db.execute(f"SET app.user_id = {current_user.id}")
    
    try:
        timeline_data = await rag_service.generate_timeline(
            user_id=current_user.id,
            query=request.query,
            start_date=request.start_date,
            end_date=request.end_date,
            max_items=request.max_items
        )
        
        # Save timeline to database
        timeline = Timeline(
            user_id=current_user.id,
            query=request.query,
            result=timeline_data
        )
        db.add(timeline)
        await db.commit()
        
        return TimelineResponse(
            query=request.query,
            items=timeline_data["items"],
            total_items=len(timeline_data["items"])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved")
async def get_saved_timelines(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
                "item_count": len(t.result.get("items", []))
            }
            for t in timelines
        ]
    }


@router.get("/{timeline_id}")
async def get_timeline(
    timeline_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
        "result": timeline.result
    }