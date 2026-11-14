"""Add documents.text_source (text layer or AI-read scan) (F14).

Revision ID: 20358ab66019
Revises: fdf2714f5545
Create Date: 2026-11-14 17:00:11.202449+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20358ab66019"
down_revision: str | None = "fdf2714f5545"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.add_column("documents", sa.Column("text_source", sa.String(length=16), nullable=True))


def downgrade() -> None:

    op.drop_column("documents", "text_source")
