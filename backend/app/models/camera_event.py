import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CameraEvent(Base):
    __tablename__ = "camera_events"
    __table_args__ = (
        Index("idx_camera_events_cam_time", "camera_id", "captured_at"),
        Index("idx_camera_events_type", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    person_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    client_count: Mapped[int | None] = mapped_column(Integer)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    avg_sentiment: Mapped[str | None] = mapped_column(String(20))
    avg_satisfaction: Mapped[float | None] = mapped_column(Float)
    snapshot_path: Mapped[str | None] = mapped_column(String(500))
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, server_default="{}")
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    camera = relationship("Camera", back_populates="events")
