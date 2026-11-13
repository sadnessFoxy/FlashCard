"""Turn flashcard models into API schemas."""

from __future__ import annotations

from app.modules.study.flashcards.models import Flashcard, FlashcardDeck
from app.modules.study.flashcards.repository import DeckStats
from app.modules.study.flashcards.schemas import CardOut, CardSourceOut, DeckOut


def deck_out(deck: FlashcardDeck, stats: DeckStats) -> DeckOut:
    return DeckOut(
        id=deck.id,
        space_id=deck.space_id,
        name=deck.name,
        card_count=stats.card_count,
        due_count=stats.due_count,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


def card_out(card: Flashcard, live_document_ids: set[str]) -> CardOut:
    """`live_document_ids`: sources outside it are shown as deleted (document_id = null)."""
    source = None
    if card.source_document_name:
        live = card.source_document_id and str(card.source_document_id) in live_document_ids
        source = CardSourceOut(
            document_id=card.source_document_id if live else None,
            document_name=card.source_document_name,
            page=card.source_page,
        )
    return CardOut(
        id=card.id,
        deck_id=card.deck_id,
        front=card.front,
        back=card.back,
        origin=card.origin,  # type: ignore[arg-type]
        source=source,
        due_at=card.due_at,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )
