"""Admin data: audit log (append only), runtime settings, per-user quota overrides."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdminAuditLog(Base):
    """Who did what to which object, with values before and after (A7). Never updated."""

    __tablename__ = "admin_audit_logs"
    __table_args__ = (Index("ix_admin_audit_logs_created_at", "created_at"),)

    # Kept when the admin account is deleted, so history stays complete.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    actor_email: Mapped[str] = mapped_column(String(254), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(64))
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)


class AppSetting(Base):
    """A setting changed at runtime by an admin (A5); absent keys use the environment."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)


class UserQuotaOverride(Base):
    """A daily question limit for one user, optionally until a date (A3)."""

    __tablename__ = "user_quota_overrides"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
