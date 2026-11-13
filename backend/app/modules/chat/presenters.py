"""Turn chat models into API schemas."""

from __future__ import annotations

from app.modules.chat.citations import mark_deleted
from app.modules.chat.models import Message
from app.modules.chat.schemas import MessageOut


def message_out(message: Message, live_document_ids: set[str] | None = None) -> MessageOut:
    """`live_document_ids` given: citations of deleted documents get `document_id = null`."""
    citations = message.citations or []
    if live_document_ids is not None:
        citations = mark_deleted(citations, live_document_ids)
    return MessageOut.model_validate(
        {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "mode": message.mode,
            "status": message.status,
            "error_code": message.error_code,
            "citations": citations,
            "document_ids": message.document_ids,
            "created_at": message.created_at,
        }
    )
