"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Cameras
    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("rtsp_url", sa.String(500), nullable=False),
        sa.Column("franchise_unit_id", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("resolution", sa.String(20), server_default="1280x720"),
        sa.Column("fps_target", sa.Integer(), server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Persons
    op.create_table(
        "persons",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("display_name", sa.String(200)),
        sa.Column("person_type", sa.String(20), server_default="unknown"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("total_visits", sa.Integer(), server_default="1"),
        sa.Column("avg_satisfaction", sa.Float()),
        sa.Column("estimated_age", sa.Integer()),
        sa.Column("estimated_gender", sa.String(10)),
        sa.Column("thumbnail_path", sa.String(500)),
        sa.Column("notes", sa.Text()),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_persons_last_seen", "persons", ["last_seen_at"])
    op.create_index("idx_persons_type", "persons", ["person_type"])

    # Face Embeddings (using raw SQL for pgvector column type)
    op.execute("""
        CREATE TABLE face_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            person_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
            embedding vector(512) NOT NULL,
            quality_score FLOAT,
            face_bbox JSONB,
            source_camera_id UUID REFERENCES cameras(id),
            captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            image_path VARCHAR(500),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.create_index("idx_face_embeddings_person", "face_embeddings", ["person_id"])
    op.create_index("idx_face_embeddings_captured", "face_embeddings", ["captured_at"])
    op.execute("""
        CREATE INDEX idx_face_embeddings_vector
        ON face_embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)

    # Emotion Records
    op.create_table(
        "emotion_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("anger", sa.Float(), server_default="0", nullable=False),
        sa.Column("contempt", sa.Float(), server_default="0", nullable=False),
        sa.Column("disgust", sa.Float(), server_default="0", nullable=False),
        sa.Column("fear", sa.Float(), server_default="0", nullable=False),
        sa.Column("happiness", sa.Float(), server_default="0", nullable=False),
        sa.Column("neutral", sa.Float(), server_default="0", nullable=False),
        sa.Column("sadness", sa.Float(), server_default="0", nullable=False),
        sa.Column("surprise", sa.Float(), server_default="0", nullable=False),
        sa.Column("dominant_emotion", sa.String(20), nullable=False),
        sa.Column("valence", sa.Float()),
        sa.Column("arousal", sa.Float()),
        sa.Column("satisfaction_score", sa.Float()),
        sa.Column("face_confidence", sa.Float()),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_emotion_records_person_time", "emotion_records", ["person_id", "captured_at"])
    op.create_index("idx_emotion_records_camera_time", "emotion_records", ["camera_id", "captured_at"])
    op.create_index("idx_emotion_records_dominant", "emotion_records", ["dominant_emotion", "captured_at"])

    # Camera Events
    op.create_table(
        "camera_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("person_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("client_count", sa.Integer()),
        sa.Column("employee_count", sa.Integer()),
        sa.Column("avg_sentiment", sa.String(20)),
        sa.Column("avg_satisfaction", sa.Float()),
        sa.Column("snapshot_path", sa.String(500)),
        sa.Column("details", postgresql.JSONB(), server_default="{}"),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_camera_events_cam_time", "camera_events", ["camera_id", "captured_at"])
    op.create_index("idx_camera_events_type", "camera_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("camera_events")
    op.drop_table("emotion_records")
    op.drop_table("face_embeddings")
    op.drop_table("persons")
    op.drop_table("cameras")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
