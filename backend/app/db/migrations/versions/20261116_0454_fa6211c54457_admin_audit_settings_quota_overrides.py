"""Create admin_audit_logs, app_settings and user_quota_overrides (F16).

Revision ID: fa6211c54457
Revises: 20358ab66019
Create Date: 2026-11-16 04:54:48.065699+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "fa6211c54457"
down_revision: str | None = "20358ab66019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_settings")),
        sa.UniqueConstraint("key", name=op.f("uq_app_settings_key")),
    )
    op.create_table(
        "admin_audit_logs",
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("actor_email", sa.String(length=254), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
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
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_admin_audit_logs_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_audit_logs")),
    )
    op.create_index(
        op.f("ix_admin_audit_logs_action"), "admin_audit_logs", ["action"], unique=False
    )
    op.create_index(
        "ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"], unique=False
    )
    op.create_table(
        "user_quota_overrides",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("daily_limit", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_quota_overrides_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_quota_overrides")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_quota_overrides_user_id")),
    )


def downgrade() -> None:

    op.drop_table("user_quota_overrides")
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_action"), table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_table("app_settings")
