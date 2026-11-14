"""Create quizzes, quiz_questions and quiz_attempts (F11).

Revision ID: 720e88664574
Revises: a0c4f4caa241
Create Date: 2026-11-14 05:44:48.731174+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "720e88664574"
down_revision: str | None = "a0c4f4caa241"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "quizzes",
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("space_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("source_document_id", sa.UUID(), nullable=True),
        sa.Column("source_document_name", sa.String(length=255), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
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
            ["owner_id"], ["users.id"], name=op.f("fk_quizzes_owner_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["documents.id"],
            name=op.f("fk_quizzes_source_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["space_id"], ["spaces.id"], name=op.f("fk_quizzes_space_id_spaces"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quizzes")),
    )
    op.create_index(op.f("ix_quizzes_owner_id"), "quizzes", ["owner_id"], unique=False)
    op.create_index(
        "ix_quizzes_space_id_created_at", "quizzes", ["space_id", "created_at"], unique=False
    )
    op.create_table(
        "quiz_attempts",
        sa.Column("quiz_id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
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
            name=op.f("fk_quiz_attempts_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["quiz_id"],
            ["quizzes.id"],
            name=op.f("fk_quiz_attempts_quiz_id_quizzes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quiz_attempts")),
    )
    op.create_index(
        "ix_quiz_attempts_quiz_id_created_at",
        "quiz_attempts",
        ["quiz_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "quiz_questions",
        sa.Column("quiz_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
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
            ["quiz_id"],
            ["quizzes.id"],
            name=op.f("fk_quiz_questions_quiz_id_quizzes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quiz_questions")),
    )
    op.create_index(
        "ix_quiz_questions_quiz_id_position",
        "quiz_questions",
        ["quiz_id", "position"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index("ix_quiz_questions_quiz_id_position", table_name="quiz_questions")
    op.drop_table("quiz_questions")
    op.drop_index("ix_quiz_attempts_quiz_id_created_at", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index("ix_quizzes_space_id_created_at", table_name="quizzes")
    op.drop_index(op.f("ix_quizzes_owner_id"), table_name="quizzes")
    op.drop_table("quizzes")
