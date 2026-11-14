"""
AI flashcard suggestions (U11). The AI only proposes cards; nothing is saved here.
The learner reviews, edits and picks cards, then saves them with POST /v1/flashcards.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AiTemporarilyUnavailableError
from app.core.logging import get_logger
from app.integrations.llm_gateway.gateway import LLMGateway
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
    SuggestionOut,
    SuggestionRequest,
)
from app.modules.study.source_material import Passage, SourceMaterial, SourceMaterialLoader
from app.modules.usage.quota import CardSuggestionQuota

logger = get_logger(__name__)

SUGGESTION_TEMPERATURE = 0.3


class SuggestionService:
    def __init__(
        self, session: AsyncSession, gateway: LLMGateway, quota: CardSuggestionQuota
    ) -> None:
        self._session = session
        self._gateway = gateway
        self._quota = quota
        self._sources = SourceMaterialLoader(session, settings.CARD_SUGGESTION_SOURCE_CHARS)

    async def suggest(self, owner_id: uuid.UUID, request: SuggestionRequest) -> list[SuggestionOut]:
        await SpaceService(self._session).get(owner_id, request.space_id)
        await self._quota.require(owner_id)
        material = await self._material(owner_id, request)
        drafts = await self._quota.spend(
            owner_id, lambda: self._generate(owner_id, material, request.count)
        )
        return [_suggestion(d, material.passages) for d in drafts]

    async def _material(self, owner_id: uuid.UUID, request: SuggestionRequest) -> SourceMaterial:
        source = request.source
        if isinstance(source, DocumentSuggestionSource):
            return await self._sources.from_document(
                owner_id, request.space_id, source.document_id, source.page_start, source.page_end
            )
        return await self._sources.from_answer(owner_id, request.space_id, source.message_id)

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
