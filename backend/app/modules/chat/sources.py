"""
Find the passages a question is answered from (docs/specs/f7-qa.md section 2).

Vector search first; when the question cannot be embedded because AI is down, fall back
to keyword search so the learner still gets passages (U8). Both apply the R4 filters.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
)
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.documents.retrieval import (
    RetrievedChunk,
    keyword_search,
    ready_document_ids,
    search_chunks,
    select_sources,
)

# Errors that switch the answer to retrieval-only mode instead of failing (U8).
AI_DOWN_ERRORS = (AiQuotaExhaustedError, AiTemporarilyUnavailableError, AiRateLimitedError)


@dataclass(frozen=True)
class FoundSources:
    sources: list[RetrievedChunk]
    selected_document_ids: list[uuid.UUID]
    ai_down: bool


class SourceFinder:
    def __init__(self, session: AsyncSession, gateway: LLMGateway) -> None:
        self._session = session
        self._gateway = gateway

    async def find(
        self,
        *,
        owner_id: uuid.UUID,
        space_id: uuid.UUID,
        question: str,
        document_ids: list[uuid.UUID] | None,
    ) -> FoundSources:
        selected = await self._allowed_documents(owner_id, space_id, document_ids)
        if not selected:
            return FoundSources([], selected, ai_down=False)

        try:
            [vector] = await self._gateway.embed([question], "query", user_id=str(owner_id))
        except AI_DOWN_ERRORS:
            candidates = await keyword_search(
                self._session,
                owner_id=owner_id,
                space_id=space_id,
                question=question,
                document_ids=selected,
                limit=settings.CHAT_CANDIDATES,
            )
            return FoundSources(self._select(candidates, max_distance=1.0), selected, True)

        candidates = await search_chunks(
            self._session,
            owner_id=owner_id,
            space_id=space_id,
            query_vector=vector,
            document_ids=selected,
            candidates=settings.CHAT_CANDIDATES,
        )
        return FoundSources(
            self._select(candidates, max_distance=settings.CHAT_MAX_DISTANCE), selected, False
        )

    async def _allowed_documents(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, requested: list[uuid.UUID] | None
    ) -> list[uuid.UUID]:
        """The owner's READY documents in the space; unknown IDs are dropped silently (R4)."""
        ready = await ready_document_ids(self._session, owner_id, space_id)
        if requested is None:
            return ready
        allowed = set(ready)
        return [d for d in requested if d in allowed]

    @staticmethod
    def _select(candidates: list[RetrievedChunk], *, max_distance: float) -> list[RetrievedChunk]:
        return select_sources(
            candidates,
            max_distance=max_distance,
            top_k=settings.CHAT_TOP_K,
            per_document=settings.CHAT_MAX_PER_DOCUMENT,
        )
