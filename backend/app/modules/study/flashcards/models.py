"""Decks and cards. Cards carry SM-2 scheduling columns used by reviews (F10)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

CARD_ORIGINS = ("ai", "manual")
DEFAULT_EASE = 2.5


class FlashcardDeck(Base):
    __tablename__ = "flashcard_decks"
    __table_args__ = (Index("ix_flashcard_decks_space_id_updated_at", "space_id", "updated_at"),)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Flashcard(Base):
    __tablename__ = "flashcards"
    __table_args__ = (
        CheckConstraint("origin IN ('ai', 'manual')", name="origin"),
        Index("ix_flashcards_deck_id_position", "deck_id", "position"),
        Index("ix_flashcards_owner_id_due_at", "owner_id", "due_at"),
    )

    deck_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flashcard_decks.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Order within the deck; timestamps can tie for cards saved together.
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    # Source kept as a snapshot: the card outlives its document (SET NULL on delete).
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL")
    )
    source_document_name: Mapped[str | None] = mapped_column(String(255))
    source_page: Mapped[int | None] = mapped_column(Integer)
    # SM-2 schedule (F10); a new card is due immediately.
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=DEFAULT_EASE)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    # Latest review applied; an older review arriving later (offline sync) must not undo it.
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
