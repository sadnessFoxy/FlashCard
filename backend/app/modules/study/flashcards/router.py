"""Routers for decks (/v1/decks) and cards (/v1/flashcards), contract tag `flashcards`."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.auth.dependencies import get_current_user
from app.modules.study.flashcards.schemas import (
    CardListOut,
    CardOut,
    CreateCardsRequest,
    CreateDeckRequest,
    DeckDetailOut,
    DeckListOut,
    DeckNameRequest,
    DeckOut,
    SuggestionListOut,
    SuggestionRequest,
    UpdateCardRequest,
)
from app.modules.study.flashcards.service import FlashcardService
from app.modules.study.flashcards.suggestions import SuggestionService
from app.modules.usage.quota import CardSuggestionQuota, get_card_suggestion_quota
from app.modules.users.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]


def get_flashcard_service(db: Db) -> FlashcardService:
    return FlashcardService(db)


def get_suggestion_service(
    db: Db,
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
    quota: Annotated[CardSuggestionQuota, Depends(get_card_suggestion_quota)],
) -> SuggestionService:
    return SuggestionService(db, gateway, quota)


Service = Annotated[FlashcardService, Depends(get_flashcard_service)]
Suggestions = Annotated[SuggestionService, Depends(get_suggestion_service)]

decks_router = APIRouter()
cards_router = APIRouter()


# ---------- decks ----------


@decks_router.get("", response_model=DeckListOut, operation_id="listDecks")
async def list_decks(
    user: CurrentUser, service: Service, space_id: Annotated[uuid.UUID, Query()]
) -> DeckListOut:
    return DeckListOut(items=await service.list_decks(user.id, space_id))


@decks_router.post(
    "", response_model=DeckOut, status_code=status.HTTP_201_CREATED, operation_id="createDeck"
)
async def create_deck(body: CreateDeckRequest, user: CurrentUser, service: Service) -> DeckOut:
    return await service.create_deck(user.id, body.space_id, body.name)


@decks_router.get("/{deck_id}", response_model=DeckDetailOut, operation_id="getDeck")
async def get_deck(deck_id: uuid.UUID, user: CurrentUser, service: Service) -> DeckDetailOut:
    return await service.get_deck(user.id, deck_id)


@decks_router.patch("/{deck_id}", response_model=DeckOut, operation_id="renameDeck")
async def rename_deck(
    deck_id: uuid.UUID, body: DeckNameRequest, user: CurrentUser, service: Service
) -> DeckOut:
    return await service.rename_deck(user.id, deck_id, body.name)


@decks_router.delete(
    "/{deck_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteDeck"
)
async def delete_deck(deck_id: uuid.UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete_deck(user.id, deck_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- cards ----------


@cards_router.post(
    "",
    response_model=CardListOut,
    status_code=status.HTTP_201_CREATED,
    operation_id="createFlashcards",
)
async def create_cards(
    body: CreateCardsRequest, user: CurrentUser, service: Service
) -> CardListOut:
    return CardListOut(items=await service.add_cards(user.id, body.deck_id, body.cards))


@cards_router.post(
    "/suggestions", response_model=SuggestionListOut, operation_id="suggestFlashcards"
)
async def suggest_cards(
    body: SuggestionRequest, user: CurrentUser, suggestions: Suggestions
) -> SuggestionListOut:
    return SuggestionListOut(items=await suggestions.suggest(user.id, body))


@cards_router.patch("/{card_id}", response_model=CardOut, operation_id="updateFlashcard")
async def update_card(
    card_id: uuid.UUID, body: UpdateCardRequest, user: CurrentUser, service: Service
) -> CardOut:
    return await service.update_card(user.id, card_id, body)


@cards_router.delete(
    "/{card_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteFlashcard"
)
async def delete_card(card_id: uuid.UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete_card(user.id, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
