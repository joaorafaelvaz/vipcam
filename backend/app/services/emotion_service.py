import uuid
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emotion_record import EmotionRecord
from app.schemas.emotion import EmotionAggregation, EmotionTimelinePoint


async def get_recent_emotions(
    db: AsyncSession,
    camera_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[EmotionRecord]:
    query = select(EmotionRecord).order_by(EmotionRecord.captured_at.desc())
    if camera_id:
        query = query.where(EmotionRecord.camera_id == camera_id)
    if person_id:
        query = query.where(EmotionRecord.person_id == person_id)
    result = await db.execute(query.limit(limit))
    return list(result.scalars().all())


async def get_emotion_timeline(
    db: AsyncSession,
    start: datetime,
    end: datetime,
    camera_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    bucket_minutes: int = 15,
) -> list[EmotionTimelinePoint]:
    bucket_interval = f"{bucket_minutes} minutes"

    query = text("""
        SELECT
            date_trunc('hour', captured_at) +
            (EXTRACT(minute FROM captured_at)::int / :bucket * interval '1 minute' * :bucket)
                AS bucket_time,
            AVG(anger) as anger,
            AVG(contempt) as contempt,
            AVG(disgust) as disgust,
            AVG(fear) as fear,
            AVG(happiness) as happiness,
            AVG(neutral) as neutral,
            AVG(sadness) as sadness,
            AVG(surprise) as surprise,
            AVG(satisfaction_score) as avg_satisfaction
        FROM emotion_records
        WHERE captured_at BETWEEN :start AND :end
            AND (:camera_id IS NULL OR camera_id = :camera_id)
            AND (:person_id IS NULL OR person_id = :person_id)
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
            "person_id": str(person_id) if person_id else None,
        },
    )

    return [
        EmotionTimelinePoint(
            timestamp=row.bucket_time,
            anger=row.anger or 0,
            contempt=row.contempt or 0,
            disgust=row.disgust or 0,
            fear=row.fear or 0,
            happiness=row.happiness or 0,
            neutral=row.neutral or 0,
            sadness=row.sadness or 0,
            surprise=row.surprise or 0,
            avg_satisfaction=row.avg_satisfaction,
        )
        for row in result.fetchall()
    ]


async def get_satisfaction_summary(
    db: AsyncSession,
    start: datetime,
    end: datetime,
    camera_id: uuid.UUID | None = None,
) -> EmotionAggregation:
    query = select(
        func.count(EmotionRecord.id).label("count"),
        func.avg(EmotionRecord.satisfaction_score).label("avg_satisfaction"),
        func.avg(EmotionRecord.valence).label("avg_valence"),
    ).where(EmotionRecord.captured_at.between(start, end))

    if camera_id:
        query = query.where(EmotionRecord.camera_id == camera_id)

    result = (await db.execute(query)).one()

    # Get dominant emotion
    dominant_query = (
        select(EmotionRecord.dominant_emotion, func.count().label("cnt"))
        .where(EmotionRecord.captured_at.between(start, end))
        .group_by(EmotionRecord.dominant_emotion)
        .order_by(text("cnt DESC"))
        .limit(1)
    )
    if camera_id:
        dominant_query = dominant_query.where(EmotionRecord.camera_id == camera_id)
    dominant_result = (await db.execute(dominant_query)).first()

    return EmotionAggregation(
        period_start=start,
        period_end=end,
        sample_count=result.count or 0,
        avg_satisfaction=float(result.avg_satisfaction) if result.avg_satisfaction else None,
        avg_valence=float(result.avg_valence) if result.avg_valence else None,
        dominant_emotion=dominant_result[0] if dominant_result else None,
        emotion_distribution={},
    )
