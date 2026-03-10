import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class WSPersonData(BaseModel):
    person_id: uuid.UUID
    display_name: str | None
    person_type: str
    dominant_emotion: str
    satisfaction_score: float | None
    valence: float | None
    emotions: dict[str, float]
    bbox: list[float]
    age: int | None
    gender: str | None
    is_new: bool
    visit_count: int


class WSAggregate(BaseModel):
    avg_satisfaction: float | None
    avg_valence: float | None
    dominant_sentiment: str
    occupancy_level: str


class WSAnalysisUpdate(BaseModel):
    type: Literal["analysis_update"] = "analysis_update"
    camera_id: uuid.UUID
    camera_name: str
    timestamp: datetime
    person_count: int
    faces_detected: int
    persons: list[WSPersonData]
    aggregate: WSAggregate
    processing_time_ms: float


class WSSubscribe(BaseModel):
    action: Literal["subscribe"]
    cameras: list[str]


class WSUnsubscribe(BaseModel):
    action: Literal["unsubscribe"]
    cameras: list[str]
