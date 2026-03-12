import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    rtsp_url: Mapped[str] = mapped_column(String(500), nullable=False)
    franchise_unit_id: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080", server_default="1920x1080")
    rtsp_protocol: Mapped[str] = mapped_column(String(10), default="rtsp", server_default="rtsp")
    fps_target: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    events = relationship("CameraEvent", back_populates="camera", lazy="selectin", cascade="all, delete-orphan")
    emotion_records = relationship("EmotionRecord", back_populates="camera", lazy="noload", cascade="all, delete-orphan")
