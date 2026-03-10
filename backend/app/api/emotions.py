import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.emotion import EmotionAggregation, EmotionRead, EmotionTimelinePoint
from app.services import emotion_service

router = APIRouter()


@router.get("/recent", response_model=list[EmotionRead])
async def get_recent_emotions(
    camera_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await emotion_service.get_recent_emotions(
        db, camera_id=camera_id, person_id=person_id, limit=limit
    )


@router.get("/timeline", response_model=list[EmotionTimelinePoint])
async def get_emotion_timeline(
    start: datetime,
    end: datetime,
    camera_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    bucket_minutes: int = Query(15, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
):
    return await emotion_service.get_emotion_timeline(
        db, start=start, end=end,
        camera_id=camera_id, person_id=person_id,
        bucket_minutes=bucket_minutes,
    )


@router.get("/summary", response_model=EmotionAggregation)
async def get_emotion_summary(
    start: datetime,
    end: datetime,
    camera_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await emotion_service.get_satisfaction_summary(
        db, start=start, end=end, camera_id=camera_id
    )
