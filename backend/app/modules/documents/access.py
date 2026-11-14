"""Shared ownership checks for features that read a document's content (R4)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotReadyError, NotFoundError
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.states import DELETING, READY


async def ready_document(
    session: AsyncSession, owner_id: uuid.UUID, document_id: uuid.UUID
) -> Document:
    """The owner's document if READY; 404 if missing, foreign or deleting; 409 otherwise."""
    document = await DocumentRepository(session).get_for_owner(owner_id, document_id)
    if document is None or document.status == DELETING:
        raise NotFoundError("Document")
    if document.status != READY:
        raise DocumentNotReadyError()
    return document
