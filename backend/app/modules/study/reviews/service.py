"""
Due cards and graded reviews (docs/specs/f10-reviews.md). No AI is involved, so this
keeps working when AI is down (U8).

Reviews may arrive late and more than once (offline queue): the client's review id makes
a retry a no-op, and a review older than the card's latest one is logged as stale
without changing the schedule.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.spaces.service import SpaceService
from app.modules.study.flashcards.models import Flashcard
from app.modules.study.flashcards.presenters import card_out
from app.modules.study.flashcards.repository import FlashcardRepository
from app.modules.study.reviews.models import ReviewLog
from app.modules.study.reviews.repository import ReviewRepository
from app.modules.study.reviews.schemas import DueCardsOut, ReviewIn, ReviewResultOut
from app.modules.study.reviews.sm2 import Schedule, schedule

# A device clock ahead of ours must not push reviews into the future.
CLOCK_SKEW = timedelta(minutes=5)


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReviewRepository(session)

    async def due(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, deck_id: uuid.UUID | None, limit: int
    ) -> DueCardsOut:
        await SpaceService(self._session).get(owner_id, space_id)  # 404 if not the owner's
        cards, total = await self._repo.due_cards(
            owner_id, space_id, deck_id, datetime.now(UTC), limit
        )
        ids = {c.source_document_id for c in cards if c.source_document_id}
        live = {
            str(d) for d in await FlashcardRepository(self._session).owned_documents(owner_id, ids)
        }
        return DueCardsOut(items=[card_out(c, live) for c in cards], total_due=total)

    async def submit(self, owner_id: uuid.UUID, reviews: list[ReviewIn]) -> list[ReviewResultOut]:
        known = await self._repo.existing_logs(owner_id, {r.id for r in reviews})
        cards = await self._repo.cards_for_update(owner_id, {r.card_id for r in reviews})
        results = []
        # Oldest first, so a batch replayed from an offline queue applies in order.
        for review in sorted(reviews, key=lambda r: r.reviewed_at):
            results.append(await self._apply(owner_id, review, known, cards))
        order = {r.id: i for i, r in enumerate(reviews)}
        return sorted(results, key=lambda r: order[r.id])

    async def _apply(
        self,
        owner_id: uuid.UUID,
        review: ReviewIn,
        known: dict[uuid.UUID, ReviewLog],
        cards: dict[uuid.UUID, Flashcard],
    ) -> ReviewResultOut:
        if review.id in known:
            log = known[review.id]
            return _result(review, "duplicate", log.due_at_after, log.interval_days_after)
        card = cards.get(review.card_id)
        if card is None:
            return _result(review, "not_found", None, None)

        reviewed_at = min(review.reviewed_at, datetime.now(UTC) + CLOCK_SKEW)
        log = ReviewLog(
            id=review.id,
            owner_id=owner_id,
            flashcard_id=card.id,
            grade=review.grade,
            reviewed_at=reviewed_at,
        )
        known[review.id] = log  # the same id twice in one batch is a duplicate too
        if card.last_reviewed_at and reviewed_at <= card.last_reviewed_at:
            await self._repo.add(log)
            return _result(review, "stale", card.due_at, card.interval_days)

        after = schedule(_current(card), review.grade, reviewed_at)
        card.ease_factor = after.ease_factor
        card.interval_days = after.interval_days
        card.repetitions = after.repetitions
        card.due_at = after.due_at
        card.last_reviewed_at = reviewed_at
        log.ease_after = after.ease_factor
        log.interval_days_after = after.interval_days
        log.due_at_after = after.due_at
        await self._repo.add(log)
        return _result(review, "applied", after.due_at, after.interval_days)


def _current(card: Flashcard) -> Schedule:
    return Schedule(card.ease_factor, card.interval_days, card.repetitions, card.due_at)


def _result(
    review: ReviewIn, status: str, due_at: datetime | None, interval_days: int | None
) -> ReviewResultOut:
    return ReviewResultOut(
        id=review.id,
        card_id=review.card_id,
        status=status,  # type: ignore[arg-type]
        due_at=due_at,
        interval_days=interval_days,
    )
