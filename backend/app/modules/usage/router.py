"""Router for usage (contract tag `usage`)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.modules.auth.dependencies import get_current_user
from app.modules.usage.quota import QuestionQuota, get_question_quota
from app.modules.users.models import User

router = APIRouter()


class UsageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_limit: int
    used_today: int
    remaining: int
    resets_at: datetime


@router.get("/me", response_model=UsageOut, operation_id="getMyUsage")
async def get_my_usage(
    user: Annotated[User, Depends(get_current_user)],
    quota: Annotated[QuestionQuota, Depends(get_question_quota)],
) -> UsageOut:
    status = await quota.status(user.id)
    return UsageOut(
        daily_limit=status.daily_limit,
        used_today=status.used_today,
        remaining=status.remaining,
        resets_at=status.resets_at,
    )
