"""Data access for decks and cards, always scoped to the owner (R4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document
from app.modules.documents.states import DELETING
from app.modules.study.flashcards.models import Flashcard, FlashcardDeck


@dataclass(frozen=True)
class DeckStats:
    card_count: int = 0
    due_count: int = 0


class FlashcardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- decks ----------

    async def list_decks(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> list[FlashcardDeck]:
        result = await self._session.execute(
            select(FlashcardDeck)
            .where(FlashcardDeck.owner_id == owner_id, FlashcardDeck.space_id == space_id)
            .order_by(FlashcardDeck.updated_at.desc())
        )
        return list(result.scalars())

    async def get_deck(self, owner_id: uuid.UUID, deck_id: uuid.UUID) -> FlashcardDeck | None:
        result = await self._session.execute(
            select(FlashcardDeck).where(
                FlashcardDeck.id == deck_id, FlashcardDeck.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def stats(self, deck_ids: list[uuid.UUID]) -> dict[uuid.UUID, DeckStats]:
        """Card and due-now counts per deck; decks without cards are absent."""
        if not deck_ids:
            return {}
        now = datetime.now(UTC)
        due = func.sum(case((Flashcard.due_at <= now, 1), else_=0))
        result = await self._session.execute(
            select(Flashcard.deck_id, func.count(Flashcard.id), due)
            .where(Flashcard.deck_id.in_(deck_ids))
            .group_by(Flashcard.deck_id)
        )
        return {row[0]: DeckStats(int(row[1]), int(row[2] or 0)) for row in result.all()}

    async def delete_deck(self, deck: FlashcardDeck) -> None:
        # Cards go with it (ON DELETE CASCADE).
        await self._session.execute(
            delete(FlashcardDeck).where(
                FlashcardDeck.id == deck.id, FlashcardDeck.owner_id == deck.owner_id
            )
        )

    # ---------- cards ----------

    async def cards(self, deck_id: uuid.UUID) -> list[Flashcard]:
        result = await self._session.execute(
            select(Flashcard).where(Flashcard.deck_id == deck_id).order_by(Flashcard.position)
        )
        return list(result.scalars())

    async def next_position(self, deck_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(Flashcard.position), -1) + 1).where(
                Flashcard.deck_id == deck_id
            )
        )
        return int(result.scalar_one())

    async def count_cards(self, deck_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Flashcard).where(Flashcard.deck_id == deck_id)
        )
        return int(result.scalar_one())

    async def get_card(self, owner_id: uuid.UUID, card_id: uuid.UUID) -> Flashcard | None:
        result = await self._session.execute(
            select(Flashcard).where(Flashcard.id == card_id, Flashcard.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def delete_card(self, card: Flashcard) -> None:
        await self._session.execute(
            delete(Flashcard).where(Flashcard.id == card.id, Flashcard.owner_id == card.owner_id)
        )

    # ---------- documents referenced as card sources ----------

    async def owned_documents(
        self, owner_id: uuid.UUID, document_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, Document]:
        if not document_ids:
            return {}
        result = await self._session.execute(
            select(Document).where(
                Document.owner_id == owner_id,
                Document.id.in_(document_ids),
                Document.status != DELETING,
            )
        )
        return {d.id: d for d in result.scalars()}

    async def add(self, *objects: FlashcardDeck | Flashcard) -> None:
        self._session.add_all(objects)
        await self._session.flush()
