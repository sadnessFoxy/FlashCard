"""
AI flashcard suggestions (U11). The AI only proposes cards; nothing is saved here.
The learner reviews, edits and picks cards, then saves them with POST /v1/flashcards.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AiTemporarilyUnavailableError,
    AppError,
    DocumentNotReadyError,
    NotFoundError,
    SourceEmptyError,
    UserQuotaExceededError,
)
from app.core.logging import get_logger
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.chat.repository import ChatRepository
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.retrieval import document_passages
from app.modules.documents.states import DELETING, READY
from app.modules.spaces.service import SpaceService
from app.modules.study.flashcards.prompts import (
    SYSTEM_PROMPT,
    DraftCard,
    build_request,
    parse_cards,
)
from app.modules.study.flashcards.schemas import (
    CardSourceOut,
    DocumentSuggestionSource,
    MessageSuggestionSource,
    SuggestionOut,
    SuggestionRequest,
)
from app.modules.usage.quota import CardSuggestionQuota

logger = get_logger(__name__)

SUGGESTION_TEMPERATURE = 0.3


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
    focus: str | None = None


class SuggestionService:
    def __init__(
        self, session: AsyncSession, gateway: LLMGateway, quota: CardSuggestionQuota
    ) -> None:
        self._session = session
        self._gateway = gateway
        self._quota = quota

    async def suggest(self, owner_id: uuid.UUID, request: SuggestionRequest) -> list[SuggestionOut]:
        await SpaceService(self._session).get(owner_id, request.space_id)
        status = await self._quota.status(owner_id)
        if status.remaining <= 0:
            raise UserQuotaExceededError(0, status.resets_at.isoformat())

        material = await self._material(owner_id, request)
        if not material.passages:
            raise SourceEmptyError()
        if not await self._quota.reserve(owner_id):
            raise UserQuotaExceededError(0, status.resets_at.isoformat())

        try:
            drafts = await self._generate(owner_id, material, request.count)
        except AppError:
            await self._quota.refund(owner_id)
            raise
        return [self._suggestion(d, material.passages) for d in drafts]

    async def _generate(
        self, owner_id: uuid.UUID, material: SourceMaterial, count: int
    ) -> list[DraftCard]:
        raw = await self._gateway.generate(
            build_request(material.passages, count, material.focus),
            system_prompt=SYSTEM_PROMPT,
            max_tokens=settings.CARD_SUGGESTION_MAX_OUTPUT_TOKENS,
            temperature=SUGGESTION_TEMPERATURE,
            response_format={"type": "json_object"},
            user_id=str(owner_id),
        )
        drafts = parse_cards(raw, len(material.passages), count)
        if not drafts:
            logger.warning("Card suggestion output was unusable (%d chars)", len(raw))
            raise AiTemporarilyUnavailableError()
        return drafts

    # ---------- source material ----------

    async def _material(self, owner_id: uuid.UUID, request: SuggestionRequest) -> SourceMaterial:
        source = request.source
        if isinstance(source, DocumentSuggestionSource):
            return await self._from_document(owner_id, request.space_id, source)
        return await self._from_answer(owner_id, request.space_id, source)

    async def _from_document(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, source: DocumentSuggestionSource
    ) -> SourceMaterial:
        document = await self._document_in_space(owner_id, space_id, source.document_id)
        chunks = await document_passages(
            self._session,
            owner_id=owner_id,
            document_id=document.id,
            page_start=source.page_start,
            page_end=source.page_end,
        )
        passages = [
            Passage(c.document_id, c.document_name, c.page_start, c.page_end, c.content)
            for c in chunks
        ]
        return SourceMaterial(_within_budget(passages))

    async def _from_answer(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, source: MessageSuggestionSource
    ) -> SourceMaterial:
        message = await ChatRepository(self._session).get_answer_in_space(
            owner_id, source.message_id, space_id
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
        return SourceMaterial(_within_budget(passages), focus=message.content or None)

    async def _document_in_space(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, document_id: uuid.UUID
    ) -> Document:
        document = await DocumentRepository(self._session).get_for_owner(owner_id, document_id)
        if document is None or document.status == DELETING or document.space_id != space_id:
            raise NotFoundError("Document")
        if document.status != READY:
            raise DocumentNotReadyError()
        return document

    @staticmethod
    def _suggestion(draft: DraftCard, passages: list[Passage]) -> SuggestionOut:
        passage = passages[draft.source_index - 1] if draft.source_index else None
        source = (
            CardSourceOut(
                document_id=passage.document_id,
                document_name=passage.document_name,
                page=passage.page_start,
            )
            if passage
            else None
        )
        return SuggestionOut(front=draft.front, back=draft.back, source=source)


def _within_budget(passages: list[Passage]) -> list[Passage]:
    """Leading passages that fit in CARD_SUGGESTION_SOURCE_CHARS (keeps reading order)."""
    kept: list[Passage] = []
    used = 0
    for passage in passages:
        used += len(passage.content)
        if kept and used > settings.CARD_SUGGESTION_SOURCE_CHARS:
            break
        kept.append(passage)
    return kept
