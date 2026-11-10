"""Router cho module users."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut, operation_id="getMe")
async def get_me(user: User = Depends(get_current_user)) -> UserOut:
    """The signed-in user."""
    return UserOut.from_model(user)
