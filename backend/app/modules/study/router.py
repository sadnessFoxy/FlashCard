"""Routers of the study features, mounted under /v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.study.flashcards.router import cards_router, decks_router
from app.modules.study.quizzes.router import router as quizzes_router
from app.modules.study.reviews.router import router as reviews_router

router = APIRouter()
router.include_router(decks_router, prefix="/decks", tags=["flashcards"])
router.include_router(cards_router, prefix="/flashcards", tags=["flashcards"])
router.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
router.include_router(quizzes_router, prefix="/quizzes", tags=["quizzes"])
