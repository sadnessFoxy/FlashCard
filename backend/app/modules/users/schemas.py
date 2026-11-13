"""Users I/O schemas, matching `User` in the contract."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class ConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["ai_processing"]
    version: str = Field(max_length=64)


class ConsentOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    kind: Literal["ai_processing"]
    version: str
    created_at: datetime


class ConsentListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ConsentOut]
    current_versions: dict[str, str]


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locale: Locale


class DeleteAccountRequest(BaseModel):
    """Password accounts send `password`; Google-only accounts retype `confirm_email`."""

    model_config = ConfigDict(extra="forbid")

    password: str | None = Field(default=None, max_length=1024)
    confirm_email: str | None = Field(default=None, max_length=254)
