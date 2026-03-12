from pydantic import BaseModel
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


class SettingsRead(BaseModel):
    face_match_threshold: float
    emotion_ema_alpha: float
    processing_fps_target: int
    enable_pipeline: bool
    yolo_conf: float
    yolo_imgsz: int


class SettingsUpdate(BaseModel):
    face_match_threshold: float | None = None
    emotion_ema_alpha: float | None = None
    processing_fps_target: int | None = None
    enable_pipeline: bool | None = None
    yolo_conf: float | None = None
    yolo_imgsz: int | None = None


@router.get("", response_model=SettingsRead)
async def get_settings():
    return SettingsRead(
        face_match_threshold=settings.face_match_threshold,
        emotion_ema_alpha=settings.emotion_ema_alpha,
        processing_fps_target=settings.processing_fps_target,
        enable_pipeline=settings.enable_pipeline,
        yolo_conf=settings.yolo_conf,
        yolo_imgsz=settings.yolo_imgsz,
    )


@router.patch("", response_model=SettingsRead)
async def update_settings(data: SettingsUpdate):
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(settings, key, value)
    return await get_settings()
