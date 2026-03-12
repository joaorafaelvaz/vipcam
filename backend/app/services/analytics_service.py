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


async def get_dashboard_summary(db: AsyncSession) -> dict:
    """Real-time dashboard summary: per-camera stats + global unique person count."""
    today_start = datetime.combine(date.today(), datetime.min.time())

    # Unique persons seen today
    unique_result = (await db.execute(
        text("SELECT COUNT(DISTINCT person_id) as cnt FROM emotion_records WHERE captured_at >= :t"),
        {"t": today_start},
    )).first()
    unique_persons_today = unique_result.cnt if unique_result else 0

    # Total persons in DB
    total_result = (await db.execute(text("SELECT COUNT(*) as cnt FROM persons"))).first()
    total_persons = total_result.cnt if total_result else 0

    # Per-camera stats (last 5 minutes of emotion_records + latest occupancy)
    per_camera_query = text("""
        SELECT
            c.id as camera_id,
            c.name as camera_name,
            c.location as camera_location,
            (SELECT person_count FROM camera_events
             WHERE camera_id = c.id AND event_type = 'occupancy_update'
             ORDER BY captured_at DESC LIMIT 1
            ) as last_person_count,
            (SELECT AVG(satisfaction_score) FROM emotion_records
             WHERE camera_id = c.id AND captured_at >= NOW() - INTERVAL '5 minutes'
            ) as avg_satisfaction,
            (SELECT COUNT(DISTINCT person_id) FROM emotion_records
             WHERE camera_id = c.id AND captured_at >= NOW() - INTERVAL '5 minutes'
            ) as unique_persons,
            (SELECT dominant_emotion FROM emotion_records
             WHERE camera_id = c.id AND captured_at >= NOW() - INTERVAL '5 minutes'
             GROUP BY dominant_emotion ORDER BY COUNT(*) DESC LIMIT 1
            ) as dominant_emotion
        FROM cameras c
        WHERE c.is_active = true
        ORDER BY c.name
    """)
    camera_rows = (await db.execute(per_camera_query)).fetchall()

    cameras = [
        {
            "camera_id": str(row.camera_id),
            "camera_name": row.camera_name,
            "camera_location": row.camera_location,
            "person_count": row.last_person_count or 0,
            "avg_satisfaction": round(float(row.avg_satisfaction or 0), 1),
            "unique_persons": row.unique_persons or 0,
            "dominant_emotion": row.dominant_emotion or "neutral",
        }
        for row in camera_rows
    ]

    # Global avg satisfaction today
    sat_result = (await db.execute(
        text("SELECT AVG(satisfaction_score) as avg FROM emotion_records WHERE captured_at >= :t"),
        {"t": today_start},
    )).first()

    return {
        "unique_persons_today": unique_persons_today,
        "total_persons": total_persons,
        "avg_satisfaction_today": round(float(sat_result.avg), 1) if sat_result and sat_result.avg else None,
        "cameras": cameras,
    }


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
