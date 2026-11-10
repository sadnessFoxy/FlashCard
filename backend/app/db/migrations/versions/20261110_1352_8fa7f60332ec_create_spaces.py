"""Create spaces (F4b).

Revision ID: 8fa7f60332ec
Revises: 31eaf72e0e13
Create Date: 2026-11-10 13:52:41.852596+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8fa7f60332ec"
down_revision: str | None = "31eaf72e0e13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("owner_id", sa.UUID(), nullable=False),
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
            ["owner_id"], ["users.id"], name=op.f("fk_spaces_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spaces")),
    )
    op.create_index(
        "ix_spaces_owner_id_updated_at", "spaces", ["owner_id", "updated_at"], unique=False
    )
    op.create_index(
        "uq_spaces_owner_id_lower_name",
        "spaces",
        ["owner_id", sa.literal_column("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_spaces_owner_id_lower_name", table_name="spaces")
    op.drop_index("ix_spaces_owner_id_updated_at", table_name="spaces")
    op.drop_table("spaces")
