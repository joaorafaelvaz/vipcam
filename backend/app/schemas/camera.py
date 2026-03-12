import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CameraCreate(BaseModel):
    name: str
    location: str | None = None
    rtsp_url: str
    rtsp_protocol: str = "rtsp"
    resolution: str = "1920x1080"
    fps_target: int = 5
    franchise_unit_id: int | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    rtsp_url: str | None = None
    rtsp_protocol: str | None = None
    resolution: str | None = None
    fps_target: int | None = None
    is_active: bool | None = None
    franchise_unit_id: int | None = None


class CameraRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location: str | None
    rtsp_url: str
    rtsp_protocol: str
    franchise_unit_id: int | None
    is_active: bool
    resolution: str
    fps_target: int
    created_at: datetime
    updated_at: datetime


class CameraStatus(BaseModel):
    id: uuid.UUID
    name: str
    is_online: bool
    current_fps: float
    person_count: int
    last_frame_at: datetime | None
