"""Add rtsp_protocol column and update default resolution to 1920x1080

Revision ID: 002
Revises: 001
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cameras",
        sa.Column("rtsp_protocol", sa.String(10), server_default="rtsp", nullable=False),
    )
    # Update default resolution for new cameras
    op.alter_column(
        "cameras",
        "resolution",
        server_default="1920x1080",
    )


def downgrade() -> None:
    op.alter_column(
        "cameras",
        "resolution",
        server_default="1280x720",
    )
    op.drop_column("cameras", "rtsp_protocol")
