"""Add ON DELETE CASCADE/SET NULL to camera foreign keys

Revision ID: 003
Revises: 002
Create Date: 2026-03-13

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # emotion_records.camera_id → CASCADE
    op.drop_constraint("emotion_records_camera_id_fkey", "emotion_records", type_="foreignkey")
    op.create_foreign_key(
        "emotion_records_camera_id_fkey", "emotion_records",
        "cameras", ["camera_id"], ["id"], ondelete="CASCADE",
    )

    # camera_events.camera_id → CASCADE
    op.drop_constraint("camera_events_camera_id_fkey", "camera_events", type_="foreignkey")
    op.create_foreign_key(
        "camera_events_camera_id_fkey", "camera_events",
        "cameras", ["camera_id"], ["id"], ondelete="CASCADE",
    )

    # face_embeddings.source_camera_id → SET NULL
    op.drop_constraint("face_embeddings_source_camera_id_fkey", "face_embeddings", type_="foreignkey")
    op.create_foreign_key(
        "face_embeddings_source_camera_id_fkey", "face_embeddings",
        "cameras", ["source_camera_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("emotion_records_camera_id_fkey", "emotion_records", type_="foreignkey")
    op.create_foreign_key(
        "emotion_records_camera_id_fkey", "emotion_records",
        "cameras", ["camera_id"], ["id"],
    )

    op.drop_constraint("camera_events_camera_id_fkey", "camera_events", type_="foreignkey")
    op.create_foreign_key(
        "camera_events_camera_id_fkey", "camera_events",
        "cameras", ["camera_id"], ["id"],
    )

    op.drop_constraint("face_embeddings_source_camera_id_fkey", "face_embeddings", type_="foreignkey")
    op.create_foreign_key(
        "face_embeddings_source_camera_id_fkey", "face_embeddings",
        "cameras", ["source_camera_id"], ["id"],
    )
