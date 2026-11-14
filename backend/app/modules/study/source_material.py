"""
Source text for AI study features (flashcard suggestions, quizzes): a document or page
range, or a Q&A answer with its cited passages. Ownership and space are checked (R4),
and the text is cut to a character budget in reading order.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotReadyError, NotFoundError, SourceEmptyError
from app.modules.chat.repository import ChatRepository
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.retrieval import document_passages
from app.modules.documents.states import DELETING, READY


@dataclass(frozen=True)
class Passage:
    """One numbered source given to the model."""

    document_id: uuid.UUID | None
    document_name: str
    page_start: int
    page_end: int
    content: str


@dataclass(frozen=True)
class SourceMaterial:
    passages: list[Passage]
    focus: str | None = None  # e.g. the Q&A answer the output should concentrate on


class SourceMaterialLoader:
    def __init__(self, session: AsyncSession, budget_chars: int) -> None:
        self._session = session
        self._budget = budget_chars

    async def from_document(
        self,
        owner_id: uuid.UUID,
        space_id: uuid.UUID,
        document_id: uuid.UUID,
        page_start: int | None = None,
        page_end: int | None = None,
    ) -> SourceMaterial:
        document = await self.document_in_space(owner_id, space_id, document_id)
        chunks = await document_passages(
            self._session,
            owner_id=owner_id,
            document_id=document.id,
            page_start=page_start,
            page_end=page_end,
        )
        passages = [
            Passage(c.document_id, c.document_name, c.page_start, c.page_end, c.content)
            for c in chunks
        ]
        return self._checked(SourceMaterial(self._within_budget(passages)))

    async def from_answer(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, message_id: uuid.UUID
    ) -> SourceMaterial:
        message = await ChatRepository(self._session).get_answer_in_space(
            owner_id, message_id, space_id
        )
        if message is None:
            raise NotFoundError("Message")
        passages = [
            Passage(
                uuid.UUID(c["document_id"]) if c.get("document_id") else None,
                c["document_name"],
                c["page_start"],
                c["page_end"],
                c["snippet"],
            )
            for c in message.citations
        ]
        material = SourceMaterial(self._within_budget(passages), focus=message.content or None)
        return self._checked(material)

    async def document_in_space(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, document_id: uuid.UUID
    ) -> Document:
        document = await DocumentRepository(self._session).get_for_owner(owner_id, document_id)
        if document is None or document.status == DELETING or document.space_id != space_id:
            raise NotFoundError("Document")
        if document.status != READY:
            raise DocumentNotReadyError()
        return document

    def _within_budget(self, passages: list[Passage]) -> list[Passage]:
        """Leading passages that fit in the budget (always at least one)."""
        kept: list[Passage] = []
        used = 0
        for passage in passages:
            used += len(passage.content)
            if kept and used > self._budget:
                break
            kept.append(passage)
        return kept

    @staticmethod
    def _checked(material: SourceMaterial) -> SourceMaterial:
        if not material.passages:
            raise SourceEmptyError()
        return material
