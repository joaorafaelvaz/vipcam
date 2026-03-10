import uuid
from datetime import date, datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera_event import CameraEvent


async def get_occupancy_timeline(
    db: AsyncSession,
    start: datetime,
    end: datetime,
    camera_id: uuid.UUID | None = None,
    bucket_minutes: int = 15,
) -> list[dict]:
    query = text("""
        SELECT
            date_trunc('hour', captured_at) +
            (EXTRACT(minute FROM captured_at)::int / :bucket * interval '1 minute' * :bucket)
                AS bucket_time,
            AVG(person_count) as avg_count,
            MAX(person_count) as max_count,
            MIN(person_count) as min_count
        FROM camera_events
        WHERE event_type = 'occupancy_update'
            AND captured_at BETWEEN :start AND :end
            AND (:camera_id IS NULL OR camera_id = :camera_id)
        GROUP BY bucket_time
        ORDER BY bucket_time
    """)

    result = await db.execute(
        query,
        {
            "bucket": bucket_minutes,
            "start": start,
            "end": end,
            "camera_id": str(camera_id) if camera_id else None,
        },
    )

    return [
        {
            "timestamp": row.bucket_time.isoformat(),
            "avg_count": float(row.avg_count or 0),
            "max_count": row.max_count or 0,
            "min_count": row.min_count or 0,
        }
        for row in result.fetchall()
    ]


async def get_daily_summary(db: AsyncSession, day: date) -> dict:
    start = datetime.combine(day, datetime.min.time())
    end = datetime.combine(day, datetime.max.time())

    # Total unique person count (from events)
    occupancy_query = select(
        func.avg(CameraEvent.person_count).label("avg_occupancy"),
        func.max(CameraEvent.person_count).label("peak_occupancy"),
    ).where(
        CameraEvent.event_type == "occupancy_update",
        CameraEvent.captured_at.between(start, end),
    )
    occupancy = (await db.execute(occupancy_query)).one()

    # Peak hour
    peak_hour_query = text("""
        SELECT EXTRACT(hour FROM captured_at)::int as hour,
               AVG(person_count) as avg_count
        FROM camera_events
        WHERE event_type = 'occupancy_update'
            AND captured_at BETWEEN :start AND :end
        GROUP BY hour
        ORDER BY avg_count DESC
        LIMIT 1
    """)
    peak_hour_result = (await db.execute(peak_hour_query, {"start": start, "end": end})).first()

    return {
        "date": day.isoformat(),
        "avg_occupancy": float(occupancy.avg_occupancy or 0),
        "peak_occupancy": occupancy.peak_occupancy or 0,
        "peak_hour": peak_hour_result[0] if peak_hour_result else None,
    }
