import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    display_name: Mapped[str | None] = mapped_column(String(200))
    person_type: Mapped[str] = mapped_column(
        String(20), default="unknown", server_default="unknown",
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    total_visits: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    avg_satisfaction: Mapped[float | None] = mapped_column(Float)
    estimated_age: Mapped[int | None] = mapped_column(Integer)
    estimated_gender: Mapped[str | None] = mapped_column(String(10))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[dict | None] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    embeddings = relationship("FaceEmbedding", back_populates="person", lazy="noload")
    emotion_records = relationship("EmotionRecord", back_populates="person", lazy="noload")
