import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PersonCreate(BaseModel):
    display_name: str | None = None
    person_type: str = "unknown"
    notes: str | None = None


class PersonUpdate(BaseModel):
    display_name: str | None = None
    person_type: str | None = None
    notes: str | None = None


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str | None
    person_type: str
    first_seen_at: datetime
    last_seen_at: datetime
    total_visits: int
    avg_satisfaction: float | None
    estimated_age: int | None
    estimated_gender: str | None
    thumbnail_path: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PersonMerge(BaseModel):
    source_id: uuid.UUID
    target_id: uuid.UUID


class PersonSearch(BaseModel):
    embedding: list[float]
    threshold: float = 0.6
    limit: int = 10
