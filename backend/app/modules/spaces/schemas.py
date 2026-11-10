"""Spaces I/O schemas (contract tag `spaces`)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.spaces.names import validate_name


class SpaceNameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Raw input may carry extra whitespace; the normalized name is checked for 1-100 chars.
    name: str = Field(max_length=200)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return validate_name(value)


class SpaceOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class SpaceListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SpaceOut]
