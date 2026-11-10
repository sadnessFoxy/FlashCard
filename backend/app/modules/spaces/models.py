"""Space model: groups documents, chats, decks and quizzes by subject."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

NAME_MAX_LENGTH = 100


class Space(Base):
    __tablename__ = "spaces"
    __table_args__ = (
        Index("ix_spaces_owner_id_updated_at", "owner_id", "updated_at"),
        # Names are unique per owner, case-insensitively (spec f4b Q1).
        Index("uq_spaces_owner_id_lower_name", "owner_id", text("lower(name)"), unique=True),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
