"""Router for usage (contract tag `usage`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_user
from app.modules.usage.quota import (
    CardSuggestionQuota,
    QuestionQuota,
    QuizQuota,
    get_card_suggestion_quota,
    get_question_quota,
    get_quiz_quota,
)
from app.modules.usage.schemas import UsageCounter, UsageOut
from app.modules.users.models import User

router = APIRouter()


@router.get("/me", response_model=UsageOut, operation_id="getMyUsage")
async def get_my_usage(
    user: Annotated[User, Depends(get_current_user)],
    questions: Annotated[QuestionQuota, Depends(get_question_quota)],
    card_suggestions: Annotated[CardSuggestionQuota, Depends(get_card_suggestion_quota)],
    quizzes: Annotated[QuizQuota, Depends(get_quiz_quota)],
) -> UsageOut:
    question_counter = UsageCounter.from_status(await questions.status(user.id))
    return UsageOut(
        **question_counter.model_dump(),
        card_suggestions=UsageCounter.from_status(await card_suggestions.status(user.id)),
        quizzes=UsageCounter.from_status(await quizzes.status(user.id)),
    )
