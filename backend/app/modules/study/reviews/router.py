"""Router for reviews (/v1/reviews), contract tag `reviews`."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.study.reviews.schemas import DueCardsOut, SubmitReviewsOut, SubmitReviewsRequest
from app.modules.study.reviews.service import ReviewService
from app.modules.users.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]

router = APIRouter()


def get_review_service(db: Db) -> ReviewService:
    return ReviewService(db)


Service = Annotated[ReviewService, Depends(get_review_service)]


@router.get("/due", response_model=DueCardsOut, operation_id="listDueCards")
async def list_due_cards(
    user: CurrentUser,
    service: Service,
    space_id: Annotated[uuid.UUID, Query()],
    deck_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> DueCardsOut:
    return await service.due(user.id, space_id, deck_id, limit)


@router.post("", response_model=SubmitReviewsOut, operation_id="submitReviews")
async def submit_reviews(
    body: SubmitReviewsRequest, user: CurrentUser, service: Service
) -> SubmitReviewsOut:
    return SubmitReviewsOut(results=await service.submit(user.id, body.reviews))
