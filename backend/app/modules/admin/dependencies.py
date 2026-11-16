"""Admin access: the role is checked here, on the server, for every admin endpoint (R13)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.exceptions import ForbiddenError
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise ForbiddenError("Admin only")
    return user
