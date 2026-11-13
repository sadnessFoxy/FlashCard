"""Flashcard I/O schemas (contract tag `flashcards`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings
from app.modules.spaces.names import validate_name

FRONT_MAX = 500
BACK_MAX = 2000
CARDS_PER_REQUEST = 50


def _not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


Front = Annotated[str, Field(min_length=1, max_length=FRONT_MAX), AfterValidator(_not_blank)]
Back = Annotated[str, Field(min_length=1, max_length=BACK_MAX), AfterValidator(_not_blank)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------- decks ----------


class DeckNameRequest(_Strict):
    name: str = Field(max_length=200)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return validate_name(value)


class CreateDeckRequest(DeckNameRequest):
    space_id: uuid.UUID


class DeckOut(_Strict):
    id: uuid.UUID
    space_id: uuid.UUID
    name: str
    card_count: int
    due_count: int
    created_at: datetime
    updated_at: datetime


class DeckListOut(_Strict):
    items: list[DeckOut]


# ---------- cards ----------


class CardSourceIn(_Strict):
    document_id: uuid.UUID
    page: int | None = Field(default=None, ge=1)


class CardSourceOut(_Strict):
    document_id: uuid.UUID | None  # null once the document is deleted
    document_name: str
    page: int | None


class NewCard(_Strict):
    front: Front
    back: Back
    origin: Literal["ai", "manual"] = "manual"
    source: CardSourceIn | None = None


class CreateCardsRequest(_Strict):
    deck_id: uuid.UUID
    cards: list[NewCard] = Field(min_length=1, max_length=CARDS_PER_REQUEST)


class UpdateCardRequest(_Strict):
    front: Front | None = None
    back: Back | None = None


class CardOut(_Strict):
    id: uuid.UUID
    deck_id: uuid.UUID
    front: str
    back: str
    origin: Literal["ai", "manual"]
    source: CardSourceOut | None
    due_at: datetime
    created_at: datetime
    updated_at: datetime


class CardListOut(_Strict):
    items: list[CardOut]


class DeckDetailOut(DeckOut):
    cards: list[CardOut]


# ---------- AI suggestions ----------


class DocumentSuggestionSource(_Strict):
    type: Literal["document"]
    document_id: uuid.UUID
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)


class MessageSuggestionSource(_Strict):
    type: Literal["message"]
    message_id: uuid.UUID


class SuggestionRequest(_Strict):
    space_id: uuid.UUID
    source: DocumentSuggestionSource | MessageSuggestionSource = Field(discriminator="type")
    count: int = Field(default=10, ge=1, le=settings.CARD_SUGGESTION_MAX_CARDS)


class SuggestionOut(_Strict):
    front: str
    back: str
    source: CardSourceOut | None


class SuggestionListOut(_Strict):
    items: list[SuggestionOut]
