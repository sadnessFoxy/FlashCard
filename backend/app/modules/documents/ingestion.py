"""
Background ingestion: QUEUED -> PROCESSING -> extract -> chunk -> embed -> READY.

- Every status change is a conditional update (R6); a document moved to DELETING mid-run
  makes the job stop without overwriting it.
- Chunks are stored before embedding, and only chunks without a vector are embedded, so a
  paused or retried job resumes where it stopped.
- Quota exhaustion or an open circuit -> PAUSED_QUOTA, not counted as an attempt (R8).
- Other failures -> attempts + 1; back to QUEUED with a delay, FAILED after the limit.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AiCircuitOpenError,
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
)
from app.core.logging import get_logger
from app.integrations.llm_gateway.gateway import LLMGateway
from app.integrations.object_storage import ObjectStorage, StorageError
from app.modules.ai.usage import estimate_tokens
from app.modules.documents.chunking import chunk_pages
from app.modules.documents.models import DocumentChunk
from app.modules.documents.pdf import NotAPdfError, extract_pages, looks_scanned
from app.modules.documents.queue import JobQueue
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.states import (
    FAILED,
    PAUSED_QUOTA,
    PROCESSING,
    QUEUED,
    READY,
)

logger = get_logger(__name__)

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]

RETRY_DELAYS_SECONDS = (30, 120, 600)


class _StoppedError(Exception):
    """The document left PROCESSING (e.g. deleted); abandon quietly."""


class IngestionPipeline:
    def __init__(
        self,
        session_factory: SessionFactory,
        storage: ObjectStorage,
        gateway: LLMGateway,
        queue: JobQueue,
    ) -> None:
        self._sessions = session_factory
        self._storage = storage
        self._gateway = gateway
        self._queue = queue

    async def process(self, document_id: uuid.UUID) -> str | None:
        """Run one attempt. Returns the final status of this run, or None if nothing to do."""
        async with self._sessions() as session:
            repo = DocumentRepository(session)
            if not await repo.transition(document_id, PROCESSING, sources=[QUEUED]):
                return None  # already taken, deleted, or not queued
            document = await repo.get(document_id)
            job = await repo.latest_job(document_id)
            assert document is not None
            if job is not None:
                job.status = "running"
                job.started_at = datetime.now(UTC)
            await session.commit()
            owner_id, storage_key = document.owner_id, document.storage_key

        try:
            await self._ensure_chunks(document_id, owner_id, storage_key)
            await self._embed_all(document_id, owner_id)
            return await self._finish(document_id, READY, job_status="succeeded")
        except _StoppedError:
            logger.info("Ingestion stopped: document left PROCESSING (document_id=%s)", document_id)
            return None
        except _NoTextLayerError:
            return await self._finish(document_id, FAILED, "NO_TEXT_LAYER", job_status="failed")
        except NotAPdfError:
            return await self._finish(document_id, FAILED, "EXTRACTION_FAILED", job_status="failed")
        except (AiQuotaExhaustedError, AiCircuitOpenError):
            logger.warning("AI quota unavailable, pausing (document_id=%s)", document_id)
            return await self._finish(document_id, PAUSED_QUOTA, job_status="paused")
        except (AiTemporarilyUnavailableError, AiRateLimitedError, StorageError) as exc:
            return await self._retry_or_fail(document_id, type(exc).__name__)

    # ------------------------------------------------------------- stages

    async def _ensure_chunks(
        self, document_id: uuid.UUID, owner_id: uuid.UUID, storage_key: str
    ) -> None:
        async with self._sessions() as session:
            if await DocumentRepository(session).chunk_count(document_id):
                return  # resumed run: chunks already stored
        data = await self._storage.download_file(storage_key)
        pages = extract_pages(data)
        if looks_scanned(pages, settings.SCANNED_MIN_CHARS_PER_PAGE):
            raise _NoTextLayerError
        chunks = chunk_pages(
            pages,
            target_chars=settings.CHUNK_TARGET_CHARS,
            overlap_chars=settings.CHUNK_OVERLAP_CHARS,
            max_chars=settings.CHUNK_MAX_CHARS,
        )
        if not chunks:
            raise _NoTextLayerError
        async with self._sessions() as session:
            repo = DocumentRepository(session)
            await self._still_processing(repo, document_id)
            repo.add_chunks(
                [
                    DocumentChunk(
                        document_id=document_id,
                        owner_id=owner_id,
                        chunk_index=i,
                        page_start=c.page_start,
                        page_end=c.page_end,
                        content=c.content,
                        token_estimate=estimate_tokens(c.content),
                    )
                    for i, c in enumerate(chunks)
                ]
            )
            await session.commit()
        logger.info("Document chunked (document_id=%s, chunks=%d)", document_id, len(chunks))

    async def _embed_all(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        while True:
            async with self._sessions() as session:
                repo = DocumentRepository(session)
                await self._still_processing(repo, document_id)
                batch = await repo.unembedded(document_id, settings.EMBED_BATCH_SIZE)
                if not batch:
                    return
                vectors = await self._gateway.embed(
                    [c.content for c in batch], "document", user_id=str(owner_id)
                )
                # Re-check after the slow call: a delete during it must win (R6).
                await self._still_processing(repo, document_id)
                for chunk, vector in zip(batch, vectors, strict=True):
                    chunk.embedding = vector
                await session.commit()

    async def _finish(
        self,
        document_id: uuid.UUID,
        status: str,
        error_code: str | None = None,
        *,
        job_status: str,
    ) -> str | None:
        async with self._sessions() as session:
            repo = DocumentRepository(session)
            extra = (
                {
                    "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
                    "embedding_dims": settings.EMBEDDING_DIMENSIONS,
                }
                if status == READY
                else {}
            )
            moved = await repo.transition(
                document_id, status, sources=[PROCESSING], error_code=error_code, **extra
            )
            job = await repo.latest_job(document_id)
            if job is not None and moved:
                job.status = job_status
                job.last_error_code = error_code
                job.finished_at = datetime.now(UTC)
            await session.commit()
        if moved:
            logger.info("Ingestion finished (document_id=%s, status=%s)", document_id, status)
        return status if moved else None

    async def _retry_or_fail(self, document_id: uuid.UUID, reason: str) -> str | None:
        async with self._sessions() as session:
            repo = DocumentRepository(session)
            job = await repo.latest_job(document_id)
            attempts = (job.attempts if job else 0) + 1
            give_up = attempts >= settings.INGEST_MAX_ATTEMPTS
            target = FAILED if give_up else QUEUED
            moved = await repo.transition(
                document_id,
                target,
                sources=[PROCESSING],
                error_code="PROCESSING_FAILED" if give_up else None,
            )
            if job is not None and moved:
                job.attempts = attempts
                job.status = "failed" if give_up else "retrying"
                job.last_error_code = reason
                if give_up:
                    job.finished_at = datetime.now(UTC)
            await session.commit()
        if not moved:
            return None
        if give_up:
            logger.warning(
                "Ingestion failed after %d attempts (document_id=%s)", attempts, document_id
            )
            return FAILED
        delay = RETRY_DELAYS_SECONDS[min(attempts - 1, len(RETRY_DELAYS_SECONDS) - 1)]
        await self._queue.enqueue_ingest(document_id, defer_seconds=delay)
        logger.info("Ingestion retry %d in %ds (document_id=%s)", attempts, delay, document_id)
        return QUEUED

    @staticmethod
    async def _still_processing(repo: DocumentRepository, document_id: uuid.UUID) -> None:
        document = await repo.get(document_id)
        if document is None or document.status != PROCESSING:
            raise _StoppedError

    # --------------------------------------------------------------- purge

    async def purge(self, document_id: uuid.UUID, storage_key: str) -> bool:
        """Delete the stored file, then the row if it is still DELETING. Idempotent.
        False when storage failed (the caller retries later)."""
        try:
            await self._storage.delete_file(storage_key)
        except StorageError:
            logger.warning("Purge: storage delete failed (document_id=%s)", document_id)
            return False
        async with self._sessions() as session:
            removed = await DocumentRepository(session).delete_if_deleting(document_id)
            await session.commit()
        logger.info("Document purged (document_id=%s, row_removed=%s)", document_id, removed)
        return True

    # ------------------------------------------------------------ recovery

    async def resume_stalled(self) -> list[uuid.UUID]:
        """Periodic sweep: PAUSED_QUOTA and stuck QUEUED/PROCESSING documents go back to QUEUED."""
        now = datetime.now(UTC)
        resumed: list[uuid.UUID] = []
        async with self._sessions() as session:
            repo = DocumentRepository(session)
            candidates = (
                await repo.stale(PAUSED_QUOTA, now)
                + await repo.stale(QUEUED, now - timedelta(minutes=5))
                + await repo.stale(PROCESSING, now - timedelta(minutes=30))
            )
            for document_id in candidates:
                current = await repo.get(document_id)
                if current is None:
                    continue
                if current.status == QUEUED or await repo.transition(document_id, QUEUED):
                    resumed.append(document_id)
            await session.commit()
            stale_deleting = await repo.stale_deleting(now - timedelta(minutes=10))
        for document_id in resumed:
            await self._queue.enqueue_ingest(document_id)
        for document_id, key in stale_deleting:
            await self._queue.enqueue_purge(document_id, key)
        if resumed:
            logger.info("Resumed %d documents", len(resumed))
        return resumed


class _NoTextLayerError(Exception):
    """The PDF has no usable text layer (scanned); handled by F14."""
