"""SQLAlchemy models cho module users."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

USER_ROLES = ("user", "admin")
USER_STATUSES = ("active", "blocked")
LOCALES = ("vi", "en")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(_in("role", USER_ROLES), name="role"),
        CheckConstraint(_in("status", USER_STATUSES), name="status"),
        CheckConstraint(_in("locale", LOCALES), name="locale"),
    )

    # Normalized (see auth/email.py) and unique.
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    # Null for Google-only accounts (F3).
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="user", server_default="user"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )
    locale: Mapped[str] = mapped_column(
        String(8), nullable=False, default="vi", server_default="vi"
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.deleted_at is None
