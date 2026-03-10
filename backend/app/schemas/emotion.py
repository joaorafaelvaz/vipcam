import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    camera_id: uuid.UUID
    anger: float
    contempt: float
    disgust: float
    fear: float
    happiness: float
    neutral: float
    sadness: float
    surprise: float
    dominant_emotion: str
    valence: float | None
    arousal: float | None
    satisfaction_score: float | None
    face_confidence: float | None
    captured_at: datetime


class EmotionAggregation(BaseModel):
    period_start: datetime
    period_end: datetime
    sample_count: int
    avg_satisfaction: float | None
    avg_valence: float | None
    dominant_emotion: str | None
    emotion_distribution: dict[str, float]


class EmotionTimelinePoint(BaseModel):
    timestamp: datetime
    anger: float
    contempt: float
    disgust: float
    fear: float
    happiness: float
    neutral: float
    sadness: float
    surprise: float
    avg_satisfaction: float | None
