"""Create flashcard decks and cards (F9).

Revision ID: 2ace8e1ac404
Revises: 08956e78564c
Create Date: 2026-11-13 12:07:42.485103+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2ace8e1ac404"
down_revision: str | None = "08956e78564c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "flashcard_decks",
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("space_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_flashcard_decks_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["spaces.id"],
            name=op.f("fk_flashcard_decks_space_id_spaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_flashcard_decks")),
    )
    op.create_index(
        op.f("ix_flashcard_decks_owner_id"), "flashcard_decks", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_flashcard_decks_space_id_updated_at",
        "flashcard_decks",
        ["space_id", "updated_at"],
        unique=False,
    )
    op.create_table(
        "flashcards",
        sa.Column("deck_id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("source_document_id", sa.UUID(), nullable=True),
        sa.Column("source_document_name", sa.String(length=255), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("ease_factor", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.CheckConstraint("origin IN ('ai', 'manual')", name=op.f("ck_flashcards_origin")),
        sa.ForeignKeyConstraint(
            ["deck_id"],
            ["flashcard_decks.id"],
            name=op.f("fk_flashcards_deck_id_flashcard_decks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_flashcards_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["documents.id"],
            name=op.f("fk_flashcards_source_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_flashcards")),
    )
    op.create_index(
        "ix_flashcards_deck_id_position", "flashcards", ["deck_id", "position"], unique=False
    )
    op.create_index(
        "ix_flashcards_owner_id_due_at", "flashcards", ["owner_id", "due_at"], unique=False
    )


def downgrade() -> None:

    op.drop_index("ix_flashcards_owner_id_due_at", table_name="flashcards")
    op.drop_index("ix_flashcards_deck_id_position", table_name="flashcards")
    op.drop_table("flashcards")
    op.drop_index("ix_flashcard_decks_space_id_updated_at", table_name="flashcard_decks")
    op.drop_index(op.f("ix_flashcard_decks_owner_id"), table_name="flashcard_decks")
    op.drop_table("flashcard_decks")
