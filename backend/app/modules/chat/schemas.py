"""Chat I/O schemas (contract tag `chat`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings

MessageRole = Literal["user", "assistant"]
MessageMode = Literal["question", "answer", "retrieval_only", "not_found"]
MessageStatus = Literal["pending", "complete", "partial", "error"]


class CitationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    document_id: uuid.UUID | None
    document_name: str
    page_start: int
    page_end: int
    snippet: str


class MessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    mode: MessageMode
    status: MessageStatus
    error_code: str | None
    citations: list[CitationOut]
    document_ids: list[uuid.UUID] | None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    space_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut]


class ConversationListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ConversationOut]


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    space_id: uuid.UUID


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=settings.CHAT_QUESTION_MAX_CHARS)
    document_ids: list[uuid.UUID] | None = Field(default=None, max_length=100)

    @field_validator("content")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value
