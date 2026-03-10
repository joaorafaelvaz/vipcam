import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import analytics_service

router = APIRouter()


@router.get("/occupancy")
async def get_occupancy(
    start: datetime,
    end: datetime,
    camera_id: uuid.UUID | None = None,
    bucket_minutes: int = Query(15, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_occupancy_timeline(
        db, start=start, end=end, camera_id=camera_id, bucket_minutes=bucket_minutes
    )


@router.get("/daily")
async def get_daily_summary(
    day: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    if day is None:
        day = date.today()
    return await analytics_service.get_daily_summary(db, day)
