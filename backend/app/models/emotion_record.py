import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmotionRecord(Base):
    __tablename__ = "emotion_records"
    __table_args__ = (
        Index("idx_emotion_records_person_time", "person_id", "captured_at"),
        Index("idx_emotion_records_camera_time", "camera_id", "captured_at"),
        Index("idx_emotion_records_dominant", "dominant_emotion", "captured_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False,
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False,
    )

    # 8 emotion probabilities (0.0 to 1.0)
    anger: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    contempt: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    disgust: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    fear: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    happiness: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    neutral: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    sadness: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    surprise: Mapped[float] = mapped_column(Float, default=0, server_default="0")

    # Derived metrics
    dominant_emotion: Mapped[str] = mapped_column(String(20), nullable=False)
    valence: Mapped[float | None] = mapped_column(Float)
    arousal: Mapped[float | None] = mapped_column(Float)
    satisfaction_score: Mapped[float | None] = mapped_column(Float)

    # Context
    face_confidence: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )

    person = relationship("Person", back_populates="emotion_records")
    camera = relationship("Camera", back_populates="emotion_records")
