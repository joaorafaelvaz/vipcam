import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    event_type: str
    person_count: int
    client_count: int | None
    employee_count: int | None
    avg_sentiment: str | None
    avg_satisfaction: float | None
    details: dict | None
    captured_at: datetime
    created_at: datetime
