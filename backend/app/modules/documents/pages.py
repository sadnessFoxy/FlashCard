"""
Read one page of a document as paragraphs for the citation view
(docs/specs/f8-citations-history.md).

Text comes from the stored file (PDF or Word), so it is exactly what the page says.
Extracted pages are cached in Redis under a key that includes the owner (R4); cache
errors never fail the request.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.integrations.object_storage import ObjectStorage
from app.modules.documents.access import ready_document
from app.modules.documents.chunking import split_paragraphs
from app.modules.documents.formats import UnsupportedFileError, extract_page
from app.modules.documents.models import Document

logger = get_logger(__name__)


@dataclass(frozen=True)
class DocumentPage:
    document: Document
    page: int
    paragraphs: list[str]


class PageReader:
    def __init__(
        self, session: AsyncSession, storage: ObjectStorage, redis: Redis | None = None
    ) -> None:
        self._session = session
        self._storage = storage
        self._redis = redis

    async def read(self, owner_id: uuid.UUID, document_id: uuid.UUID, page: int) -> DocumentPage:
        document = await ready_document(self._session, owner_id, document_id)
        if not 1 <= page <= document.page_count:
            raise NotFoundError("Page")
        key = f"doc-page:{owner_id}:{document_id}:{page}"
        paragraphs = await self._cached(key)
        if paragraphs is None:
            paragraphs = await self._extract(document, page)
            await self._store(key, paragraphs)
        return DocumentPage(document=document, page=page, paragraphs=paragraphs)

    async def _extract(self, document: Document, page: int) -> list[str]:
        data = await self._storage.download_file(document.storage_key)
        try:
            text = extract_page(data, document.file_kind, page)
        except UnsupportedFileError:
            logger.warning("Page extraction failed (document_id=%s)", document.id)
            return []
        return [paragraph for paragraph, _heading in split_paragraphs(text)]

    @property
    def _client(self) -> Redis:
        return self._redis or get_redis()

    async def _cached(self, key: str) -> list[str] | None:
        try:
            raw = await self._client.get(key)
        except RedisError as exc:
            logger.warning("Page cache read failed (%s)", type(exc).__name__)
            return None
        return None if raw is None else list(json.loads(raw))

    async def _store(self, key: str, paragraphs: list[str]) -> None:
        try:
            await self._client.set(
                key,
                json.dumps(paragraphs, ensure_ascii=False),
                ex=settings.DOCUMENT_PAGE_CACHE_SECONDS,
            )
        except RedisError as exc:
            logger.warning("Page cache write failed (%s)", type(exc).__name__)
