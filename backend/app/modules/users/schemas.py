"""Users I/O schemas, matching `User` in the contract."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.modules.users.models import User

Locale = Literal["vi", "en"]


class UserOut(BaseModel):
    """The user as shown to themselves; never includes password_hash or status."""

    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    email: str
    email_verified: bool
    locale: Locale
    role: Literal["user", "admin"]
    created_at: datetime

    @classmethod
    def from_model(cls, user: User) -> UserOut:
        return cls(
            id=user.id,
            email=user.email,
            email_verified=user.email_verified_at is not None,
            locale=user.locale,  # type: ignore[arg-type]  # CHECK constraint trong database
            role=user.role,  # type: ignore[arg-type]
            created_at=user.created_at,
        )
