"""Data access for due cards and review logs, always scoped to the owner (R4)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study.flashcards.models import Flashcard, FlashcardDeck
from app.modules.study.reviews.models import ReviewLog


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def due_cards(
        self,
        owner_id: uuid.UUID,
        space_id: uuid.UUID,
        deck_id: uuid.UUID | None,
        now: datetime,
        limit: int,
    ) -> tuple[list[Flashcard], int]:
        """Most overdue first, plus how many are due in total."""
        conditions = [
            Flashcard.owner_id == owner_id,
            FlashcardDeck.owner_id == owner_id,
            FlashcardDeck.space_id == space_id,
            Flashcard.due_at <= now,
        ]
        if deck_id is not None:
            conditions.append(Flashcard.deck_id == deck_id)
        in_space = (FlashcardDeck, FlashcardDeck.id == Flashcard.deck_id)

        cards = await self._session.execute(
            select(Flashcard)
            .join(*in_space)
            .where(*conditions)
            .order_by(Flashcard.due_at, Flashcard.position)
            .limit(limit)
        )
        total = await self._session.execute(
            select(func.count(Flashcard.id)).join(*in_space).where(*conditions)
        )
        return list(cards.scalars()), int(total.scalar_one())

    async def cards_for_update(
        self, owner_id: uuid.UUID, card_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, Flashcard]:
        """Locks the rows so two devices syncing at once apply reviews one after another."""
        result = await self._session.execute(
            select(Flashcard)
            .where(Flashcard.owner_id == owner_id, Flashcard.id.in_(card_ids))
            .with_for_update()
        )
        return {c.id: c for c in result.scalars()}

    async def existing_logs(
        self, owner_id: uuid.UUID, review_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, ReviewLog]:
        result = await self._session.execute(
            select(ReviewLog).where(ReviewLog.owner_id == owner_id, ReviewLog.id.in_(review_ids))
        )
        return {r.id: r for r in result.scalars()}

    async def add(self, log: ReviewLog) -> None:
        self._session.add(log)
        await self._session.flush()
