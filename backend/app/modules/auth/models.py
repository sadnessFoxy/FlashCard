"""Auth models: sign-in identities and refresh tokens."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

AUTH_PROVIDERS = ("email", "google")
CODE_PURPOSES = ("verify_email", "reset_password")


class AuthIdentity(Base):
    """One way a user signs in (email or Google); a user may have several."""

    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_subject", name="uq_auth_identities_provider_subject"
        ),
        CheckConstraint("provider IN ('email', 'google')", name="provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    # email: normalized address; google: the ID token `sub`.
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )


class RefreshToken(Base):
    """
    Rotating refresh token, stored hashed (R15).

    Each sign-in starts a family. Refreshing revokes the token and links `replaced_by_id`
    to its successor; reusing a replaced token revokes the whole family (likely theft).
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_family_id", "family_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # Sign-in time of the family, for SESSION_MAX_LIFETIME_DAYS.
    session_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refresh_tokens.id", ondelete="SET NULL")
    )
    user_agent: Mapped[str | None] = mapped_column(String(200))


class AuthCode(Base):
    """
    One-time code sent by email (R15): stored as an HMAC keyed with SECRET_KEY, single use,
    short-lived, and dead after AUTH_CODE_MAX_ATTEMPTS wrong entries.
    """

    __tablename__ = "auth_codes"
    __table_args__ = (
        CheckConstraint("purpose IN ('verify_email', 'reset_password')", name="purpose"),
        Index("ix_auth_codes_user_id_purpose", "user_id", "purpose"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
