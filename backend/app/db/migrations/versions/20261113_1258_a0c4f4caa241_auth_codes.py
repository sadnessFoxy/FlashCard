"""Create auth_codes for email verification and password reset (F4).

Revision ID: a0c4f4caa241
Revises: a6420755f3e9
Create Date: 2026-11-13 12:58:49.211743+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a0c4f4caa241"
down_revision: str | None = "a6420755f3e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "auth_codes",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("purpose", sa.String(length=16), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
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
            "purpose IN ('verify_email', 'reset_password')", name=op.f("ck_auth_codes_purpose")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_auth_codes_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_codes")),
    )
    op.create_index(
        "ix_auth_codes_user_id_purpose", "auth_codes", ["user_id", "purpose"], unique=False
    )


def downgrade() -> None:

    op.drop_index("ix_auth_codes_user_id_purpose", table_name="auth_codes")
    op.drop_table("auth_codes")
