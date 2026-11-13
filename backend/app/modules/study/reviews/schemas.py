"""Review I/O schemas (contract tag `reviews`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.study.flashcards.schemas import CardOut

Grade = Literal["again", "hard", "good", "easy"]
ReviewStatus = Literal["applied", "duplicate", "stale", "not_found"]
REVIEWS_PER_REQUEST = 100


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReviewIn(_Strict):
    id: uuid.UUID = Field(description="Made by the client; sending it again is a no-op.")
    card_id: uuid.UUID
    grade: Grade
    reviewed_at: datetime


class SubmitReviewsRequest(_Strict):
    reviews: list[ReviewIn] = Field(min_length=1, max_length=REVIEWS_PER_REQUEST)


class ReviewResultOut(_Strict):
    id: uuid.UUID
    card_id: uuid.UUID
    status: ReviewStatus
    due_at: datetime | None
    interval_days: int | None


class SubmitReviewsOut(_Strict):
    results: list[ReviewResultOut]


class DueCardsOut(_Strict):
    items: list[CardOut]
    total_due: int
