"""Review log: one row per graded card, keyed by the client's id so retries are no-ops."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReviewLog(Base):
    __tablename__ = "review_logs"
    __table_args__ = (
        CheckConstraint("grade IN ('again', 'hard', 'good', 'easy')", name="grade"),
        Index("ix_review_logs_owner_id_reviewed_at", "owner_id", "reviewed_at"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    flashcard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False
    )
    grade: Mapped[str] = mapped_column(String(8), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Schedule after this review; null when the review arrived after a newer one (stale).
    ease_after: Mapped[float | None] = mapped_column(Float)
    interval_days_after: Mapped[int | None] = mapped_column(Integer)
    due_at_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
