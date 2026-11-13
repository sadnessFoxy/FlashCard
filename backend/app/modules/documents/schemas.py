"""Documents I/O schemas (contract tag `documents`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

DocumentStatus = Literal[
    "UPLOADED", "QUEUED", "PROCESSING", "READY", "FAILED", "PAUSED_QUOTA", "DELETING"
]
DocumentErrorCode = Literal["NO_TEXT_LAYER", "EXTRACTION_FAILED", "PROCESSING_FAILED"]


class DocumentOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    space_id: uuid.UUID
    filename: str
    size_bytes: int
    page_count: int
    status: DocumentStatus
    error_code: DocumentErrorCode | None
    created_at: datetime
    updated_at: datetime


class DocumentListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentOut]
    total_documents: int
    max_documents: int


class MoveDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    space_id: uuid.UUID
