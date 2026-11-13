"""Create review_logs; add flashcards.last_reviewed_at (F10).

Revision ID: a6420755f3e9
Revises: 2ace8e1ac404
Create Date: 2026-11-13 12:39:37.603806+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a6420755f3e9"
down_revision: str | None = "2ace8e1ac404"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "review_logs",
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("flashcard_id", sa.UUID(), nullable=False),
        sa.Column("grade", sa.String(length=8), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ease_after", sa.Float(), nullable=True),
        sa.Column("interval_days_after", sa.Integer(), nullable=True),
        sa.Column("due_at_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "grade IN ('again', 'hard', 'good', 'easy')", name=op.f("ck_review_logs_grade")
        ),
        sa.ForeignKeyConstraint(
            ["flashcard_id"],
            ["flashcards.id"],
            name=op.f("fk_review_logs_flashcard_id_flashcards"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_review_logs_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_logs")),
    )
    op.create_index(
        "ix_review_logs_owner_id_reviewed_at",
        "review_logs",
        ["owner_id", "reviewed_at"],
        unique=False,
    )
    op.add_column(
        "flashcards", sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:

    op.drop_column("flashcards", "last_reviewed_at")
    op.drop_index("ix_review_logs_owner_id_reviewed_at", table_name="review_logs")
    op.drop_table("review_logs")
