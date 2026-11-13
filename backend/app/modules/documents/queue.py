"""Enqueue ingestion jobs. The API depends on the JobQueue protocol so tests can capture jobs."""

from __future__ import annotations

import uuid
from typing import Protocol

from arq import ArqRedis, create_pool

from app.core.logging import get_logger
from app.workers.settings import INGEST_FUNCTION, PURGE_FUNCTION, redis_settings

logger = get_logger(__name__)


class JobQueue(Protocol):
    async def enqueue_ingest(self, document_id: uuid.UUID, defer_seconds: float = 0) -> None: ...

    async def enqueue_purge(self, document_id: uuid.UUID, storage_key: str) -> None: ...


class ArqJobQueue:
    def __init__(self) -> None:
        self._pool: ArqRedis | None = None

    async def _get_pool(self) -> ArqRedis:
        if self._pool is None:
            self._pool = await create_pool(redis_settings())
        return self._pool

    async def enqueue_ingest(self, document_id: uuid.UUID, defer_seconds: float = 0) -> None:
        pool = await self._get_pool()
        # Unique job ids: a fixed id would make re-enqueueing a retry a silent no-op while the
        # first job is still running. Duplicates are harmless; QUEUED -> PROCESSING is atomic.
        await pool.enqueue_job(
            INGEST_FUNCTION,
            str(document_id),
            _job_id=f"ingest:{document_id}:{uuid.uuid4().hex[:8]}",
            _defer_by=defer_seconds or None,
        )

    async def enqueue_purge(self, document_id: uuid.UUID, storage_key: str) -> None:
        pool = await self._get_pool()
        await pool.enqueue_job(
            PURGE_FUNCTION,
            str(document_id),
            storage_key,
            _job_id=f"purge:{document_id}:{uuid.uuid4().hex[:8]}",
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None


job_queue = ArqJobQueue()


def get_job_queue() -> JobQueue:
    return job_queue
