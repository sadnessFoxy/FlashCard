"""Add documents.file_kind (pdf, docx) for Word support (F13). Existing rows are PDFs.

Revision ID: fdf2714f5545
Revises: 048ab090c266
Create Date: 2026-11-14 16:41:14.922962+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "fdf2714f5545"
down_revision: str | None = "048ab090c266"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.add_column(
        "documents",
        sa.Column("file_kind", sa.String(length=8), server_default="pdf", nullable=False),
    )


def downgrade() -> None:

    op.drop_column("documents", "file_kind")
