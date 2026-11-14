"""Summary I/O schemas (contract tag `summaries`)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SummaryPointOut(_Strict):
    text: str
    page: int | None


class SummaryOut(_Strict):
    points: list[SummaryPointOut]
    created_at: datetime


class SectionOut(_Strict):
    id: uuid.UUID
    position: int
    title: str | None
    page_start: int
    page_end: int
    summary: SummaryOut | None


class SectionListOut(_Strict):
    document_id: uuid.UUID
    filename: str
    items: list[SectionOut]
