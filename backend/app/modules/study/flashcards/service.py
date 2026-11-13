"""Decks and cards: create, list, edit, delete (docs/specs/f9-flashcards.md)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DeckFullError, NotFoundError
from app.modules.spaces.service import SpaceService
from app.modules.study.flashcards.models import Flashcard, FlashcardDeck
from app.modules.study.flashcards.presenters import card_out, deck_out
from app.modules.study.flashcards.repository import DeckStats, FlashcardRepository
from app.modules.study.flashcards.schemas import (
    CardOut,
    DeckDetailOut,
    DeckOut,
    NewCard,
    UpdateCardRequest,
)


class FlashcardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = FlashcardRepository(session)

    # ---------- decks ----------

    async def list_decks(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> list[DeckOut]:
        await SpaceService(self._session).get(owner_id, space_id)  # 404 if not the owner's
        decks = await self._repo.list_decks(owner_id, space_id)
        stats = await self._repo.stats([d.id for d in decks])
        return [deck_out(d, stats.get(d.id, DeckStats())) for d in decks]

    async def create_deck(self, owner_id: uuid.UUID, space_id: uuid.UUID, name: str) -> DeckOut:
        await SpaceService(self._session).get(owner_id, space_id)
        deck = FlashcardDeck(owner_id=owner_id, space_id=space_id, name=name)
        await self._repo.add(deck)
        await self._session.refresh(deck)
        return deck_out(deck, DeckStats())

    async def get_deck(self, owner_id: uuid.UUID, deck_id: uuid.UUID) -> DeckDetailOut:
        deck = await self._require_deck(owner_id, deck_id)
        cards = await self._repo.cards(deck.id)
        stats = await self._repo.stats([deck.id])
        live = await self._live_sources(owner_id, cards)
        return DeckDetailOut(
            **deck_out(deck, stats.get(deck.id, DeckStats())).model_dump(),
            cards=[card_out(c, live) for c in cards],
        )

    async def rename_deck(self, owner_id: uuid.UUID, deck_id: uuid.UUID, name: str) -> DeckOut:
        deck = await self._require_deck(owner_id, deck_id)
        deck.name = name
        deck.updated_at = datetime.now(UTC)
        await self._session.flush()
        stats = await self._repo.stats([deck.id])
        return deck_out(deck, stats.get(deck.id, DeckStats()))

    async def delete_deck(self, owner_id: uuid.UUID, deck_id: uuid.UUID) -> None:
        deck = await self._require_deck(owner_id, deck_id)
        await self._repo.delete_deck(deck)

    # ---------- cards ----------

    async def add_cards(
        self, owner_id: uuid.UUID, deck_id: uuid.UUID, new_cards: list[NewCard]
    ) -> list[CardOut]:
        deck = await self._require_deck(owner_id, deck_id)
        if await self._repo.count_cards(deck.id) + len(new_cards) > settings.MAX_CARDS_PER_DECK:
            raise DeckFullError(settings.MAX_CARDS_PER_DECK)
        # Sources must be the owner's documents; anything else is dropped silently (R4).
        requested = {c.source.document_id for c in new_cards if c.source}
        documents = await self._repo.owned_documents(owner_id, requested)

        start = await self._repo.next_position(deck.id)
        cards = []
        for offset, new in enumerate(new_cards):
            document = documents.get(new.source.document_id) if new.source else None
            cards.append(
                Flashcard(
                    deck_id=deck.id,
                    owner_id=owner_id,
                    position=start + offset,
                    front=new.front,
                    back=new.back,
                    origin=new.origin,
                    source_document_id=document.id if document else None,
                    source_document_name=document.filename if document else None,
                    source_page=self._valid_page(new, document.page_count) if document else None,
                )
            )
        await self._repo.add(*cards)
        deck.updated_at = datetime.now(UTC)
        live = {str(d) for d in documents}
        return [card_out(c, live) for c in cards]

    async def update_card(
        self, owner_id: uuid.UUID, card_id: uuid.UUID, changes: UpdateCardRequest
    ) -> CardOut:
        card = await self._require_card(owner_id, card_id)
        if changes.front is not None:
            card.front = changes.front
        if changes.back is not None:
            card.back = changes.back
        card.updated_at = datetime.now(UTC)
        await self._session.flush()
        return card_out(card, await self._live_sources(owner_id, [card]))

    async def delete_card(self, owner_id: uuid.UUID, card_id: uuid.UUID) -> None:
        card = await self._require_card(owner_id, card_id)
        await self._repo.delete_card(card)

    # ---------- helpers ----------

    async def _require_deck(self, owner_id: uuid.UUID, deck_id: uuid.UUID) -> FlashcardDeck:
        deck = await self._repo.get_deck(owner_id, deck_id)
        if deck is None:
            raise NotFoundError("Deck")
        return deck

    async def _require_card(self, owner_id: uuid.UUID, card_id: uuid.UUID) -> Flashcard:
        card = await self._repo.get_card(owner_id, card_id)
        if card is None:
            raise NotFoundError("Card")
        return card

    async def _live_sources(self, owner_id: uuid.UUID, cards: list[Flashcard]) -> set[str]:
        """Source documents that still exist (one being deleted counts as gone)."""
        ids = {c.source_document_id for c in cards if c.source_document_id}
        return {str(d) for d in await self._repo.owned_documents(owner_id, ids)}

    @staticmethod
    def _valid_page(card: NewCard, page_count: int) -> int | None:
        page = card.source.page if card.source else None
        return page if page is not None and page <= page_count else None
