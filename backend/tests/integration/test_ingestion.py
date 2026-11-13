"""
Ingestion worker against the real test DB (spec f5 criteria 1, 9-13).
Storage is in memory except in the SeaweedFS round-trip test; AI is FakeProvider.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.exceptions import (
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
)
from app.db.session import AsyncSessionLocal, engine
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker
from app.integrations.llm_gateway.gateway import LLMGateway
from app.integrations.object_storage import ObjectStorage
from app.modules.ai.providers.fake import FakeProvider
from app.modules.documents.ingestion import IngestionPipeline
from app.modules.documents.models import Document, DocumentChunk, DocumentJob
from app.modules.documents.service import DocumentService
from app.modules.spaces.service import SpaceService
from app.modules.users.service import UserService
from tests.fixtures.fakes import InMemoryStorage, RecordingQueue
from tests.fixtures.pdfs import lorem, make_blank_pdf, make_pdf

pytestmark = pytest.mark.usefixtures("clean_db")

SECRET_PHRASE = "zebracornflakes"
FILENAME = "Bí mật tuyệt đối.pdf"


async def _no_sleep(_: float) -> None:
    return None


async def _no_record(**_: object) -> None:
    return None


class Harness:
    def __init__(self, storage: InMemoryStorage | ObjectStorage | None = None) -> None:
        self.storage = storage or InMemoryStorage()
        self.queue = RecordingQueue()
        self.provider = FakeProvider()
        self.gateway = LLMGateway(
            self.provider,
            breaker=CircuitBreaker(failure_threshold=5, recovery_timeout=60),
            sleep=_no_sleep,
            recorder=_no_record,
        )
        self.pipeline = IngestionPipeline(
            AsyncSessionLocal,
            self.storage,  # type: ignore[arg-type]
            self.gateway,
            self.queue,
        )

    async def upload(self, data: bytes) -> uuid.UUID:
        async with AsyncSessionLocal() as session:
            users = UserService(session)
            user = await users.create(
                email=f"{uuid.uuid4().hex}@example.com", password_hash=None, locale="vi"
            )
            user.email_verified_at = datetime.now(UTC)  # uploads need a verified email
            await users.give_consent(user.id, "ai_processing", settings.AI_CONSENT_VERSION)
            space = await SpaceService(session).create(user.id, "Space")
            document, _ = await DocumentService(session, self.storage, self.queue).upload(  # type: ignore[arg-type]
                user=user,
                data=data,
                filename=FILENAME,
                space_id=space.id,
                idempotency_key=uuid.uuid4(),
            )
            return document.id


async def doc(document_id: uuid.UUID) -> Document:
    async with AsyncSessionLocal() as session:
        found = await session.get(Document, document_id)
        assert found is not None
        return found


async def embedded_counts(document_id: uuid.UUID) -> tuple[int, int]:
    async with AsyncSessionLocal() as session:
        total = await session.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
        done = await session.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id, DocumentChunk.embedding.is_not(None))
        )
        return int(total or 0), int(done or 0)


async def job(document_id: uuid.UUID) -> DocumentJob:
    async with AsyncSessionLocal() as session:
        found = await session.scalar(
            select(DocumentJob).where(DocumentJob.document_id == document_id)
        )
        assert found is not None
        return found


def big_pdf(pages: int = 4) -> bytes:
    return make_pdf([lorem(8, seed=f"p{i}") for i in range(pages)])


async def test_pdf_reaches_ready_with_768_dim_vectors() -> None:
    h = Harness()
    document_id = await h.upload(make_pdf(["Chapter 1\n\n" + lorem(4), lorem(3, seed="b")]))

    assert await h.pipeline.process(document_id) == "READY"

    document = await doc(document_id)
    assert (document.status, document.embedding_model, document.embedding_dims) == (
        "READY",
        settings.GEMINI_EMBEDDING_MODEL,
        768,
    )
    total, done = await embedded_counts(document_id)
    assert total >= 1 and done == total
    async with AsyncSessionLocal() as session:
        chunks = (
            await session.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
        ).all()
    assert all(1 <= c.page_start <= c.page_end <= 2 for c in chunks)
    assert all(len(c.embedding) == 768 for c in chunks if c.embedding is not None)
    assert (await job(document_id)).status == "succeeded"


async def test_vectors_support_cosine_search() -> None:
    h = Harness()
    document_id = await h.upload(big_pdf(2))
    await h.pipeline.process(document_id)
    async with AsyncSessionLocal() as session:
        first = await session.scalar(
            select(DocumentChunk).where(
                DocumentChunk.document_id == document_id, DocumentChunk.chunk_index == 0
            )
        )
        assert first is not None
        nearest = await session.scalar(
            select(DocumentChunk.chunk_index)
            .where(DocumentChunk.owner_id == first.owner_id)
            .order_by(DocumentChunk.embedding.cosine_distance(first.embedding))
            .limit(1)
        )
    assert nearest == 0


async def test_scanned_pdf_fails_with_no_text_layer() -> None:
    h = Harness()
    document_id = await h.upload(make_blank_pdf(3))

    assert await h.pipeline.process(document_id) == "FAILED"
    assert (await doc(document_id)).error_code == "NO_TEXT_LAYER"


async def test_quota_exhaustion_pauses_and_resume_skips_done_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "EMBED_BATCH_SIZE", 2)
    h = Harness()
    document_id = await h.upload(big_pdf(4))
    h.provider.embed_script = [None, AiQuotaExhaustedError()]  # first batch ok, then quota gone

    assert await h.pipeline.process(document_id) == "PAUSED_QUOTA"
    total, done_before = await embedded_counts(document_id)
    assert done_before == 2 and total > 2
    assert (await job(document_id)).attempts == 0  # pauses are not attempts

    h.gateway.breaker.reset()  # quota restored
    resumed = await h.pipeline.resume_stalled()
    assert resumed == [document_id] and h.queue.jobs[-1] == (document_id, 0)
    calls_before = len(h.provider.embed_calls)

    assert await h.pipeline.process(document_id) == "READY"
    assert await embedded_counts(document_id) == (total, total)
    re_embedded = sum(len(batch) for batch in h.provider.embed_calls[calls_before:])
    assert re_embedded == total - done_before


async def test_rate_limit_is_waited_out_not_failed() -> None:
    h = Harness()
    document_id = await h.upload(big_pdf(1))
    h.provider.embed_script = [AiRateLimitedError(retry_after_seconds=3)]

    assert await h.pipeline.process(document_id) == "READY"


async def test_repeated_failures_open_the_breaker_and_pause() -> None:
    """Six transient failures in a row trip the breaker (threshold 5): pause, keep attempts."""
    h = Harness()
    document_id = await h.upload(big_pdf(1))
    h.provider.embed_script = [AiTemporarilyUnavailableError()] * 6

    assert await h.pipeline.process(document_id) == "QUEUED"  # attempt 1 used
    assert await h.pipeline.process(document_id) == "PAUSED_QUOTA"
    assert (await job(document_id)).attempts == 1


async def test_transient_errors_retry_then_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    h = Harness()
    h.gateway.breaker.failure_threshold = 100  # isolate the attempt counting
    document_id = await h.upload(big_pdf(1))
    # The gateway already retries 3 times per attempt; every attempt fails.
    h.provider.embed_script = [AiTemporarilyUnavailableError()] * 9

    assert await h.pipeline.process(document_id) == "QUEUED"
    assert h.queue.jobs[-1] == (document_id, 30)
    assert await h.pipeline.process(document_id) == "QUEUED"
    assert await h.pipeline.process(document_id) == "FAILED"

    document, failed_job = await doc(document_id), await job(document_id)
    assert document.error_code == "PROCESSING_FAILED"
    assert (failed_job.attempts, failed_job.status) == (settings.INGEST_MAX_ATTEMPTS, "failed")


async def test_delete_during_processing_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    h = Harness()
    document_id = await h.upload(big_pdf(2))
    original_embed = h.provider.embed

    async def embed_then_delete(texts: list[str], task: str = "document") -> list[list[float]]:
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE documents SET status = 'DELETING' WHERE id = :id"), {"id": document_id}
            )
        return await original_embed(texts, task)  # type: ignore[arg-type]

    monkeypatch.setattr(h.provider, "embed", embed_then_delete)

    assert await h.pipeline.process(document_id) is None
    assert (await doc(document_id)).status == "DELETING"


async def test_only_queued_documents_are_picked_up() -> None:
    h = Harness()
    document_id = await h.upload(big_pdf(1))
    assert await h.pipeline.process(document_id) == "READY"

    assert await h.pipeline.process(document_id) is None  # duplicate job: no-op


async def test_logs_have_no_filename_or_content(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    h = Harness()
    document_id = await h.upload(make_pdf([f"Top secret {SECRET_PHRASE} material"]))

    await h.pipeline.process(document_id)

    assert "Ingestion finished" in caplog.text
    assert SECRET_PHRASE not in caplog.text and "Bí mật" not in caplog.text


async def test_round_trip_through_real_object_storage() -> None:
    """Upload and ingestion through SeaweedFS (bucket flashcard-test)."""
    h = Harness(storage=ObjectStorage())
    document_id = await h.upload(make_pdf([lorem(2)]))

    assert await h.pipeline.process(document_id) == "READY"
    await h.storage.delete_file((await doc(document_id)).storage_key)
