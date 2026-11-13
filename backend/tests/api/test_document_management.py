"""F6 acceptance criteria (docs/specs/f6-document-management.md section 9)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select, text

from app.db.session import AsyncSessionLocal, engine
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker
from app.integrations.llm_gateway.gateway import LLMGateway
from app.integrations.object_storage import get_storage
from app.main import app
from app.modules.ai.providers.fake import FakeProvider
from app.modules.documents.ingestion import IngestionPipeline
from app.modules.documents.models import Document, DocumentChunk, DocumentJob
from app.modules.documents.queue import get_job_queue
from tests.api.test_documents import consent, new_space, sign_up, upload
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.fakes import InMemoryStorage, RecordingQueue
from tests.fixtures.pdfs import lorem, make_pdf

pytestmark = pytest.mark.usefixtures("clean_db")


async def _noop(*_: object, **__: object) -> None:
    return None


class World:
    def __init__(self) -> None:
        self.storage = InMemoryStorage()
        self.queue = RecordingQueue()
        self.pipeline = IngestionPipeline(
            AsyncSessionLocal,
            self.storage,  # type: ignore[arg-type]
            LLMGateway(FakeProvider(), breaker=CircuitBreaker(), sleep=_noop, recorder=_noop),  # type: ignore[arg-type]
            self.queue,
        )

    async def ingest_all(self) -> None:
        while self.queue.jobs:
            document_id, _ = self.queue.jobs.pop(0)
            await self.pipeline.process(document_id)

    async def purge_all(self) -> None:
        while self.queue.purges:
            document_id, key = self.queue.purges.pop(0)
            assert await self.pipeline.purge(document_id, key)


@pytest_asyncio.fixture
async def world() -> AsyncGenerator[World, None]:
    w = World()
    app.dependency_overrides[get_storage] = lambda: w.storage
    app.dependency_overrides[get_job_queue] = lambda: w.queue
    yield w


@pytest_asyncio.fixture
async def reader(client: AsyncClient) -> dict[str, str]:
    auth = await sign_up(client)
    await consent(client, auth)
    return auth


PDF = make_pdf([lorem(4), lorem(3, seed="x")])


async def counts(document_id: str) -> tuple[int, int, int]:
    doc_id = uuid.UUID(document_id)
    async with AsyncSessionLocal() as s:
        docs = await s.scalar(
            select(func.count()).select_from(Document).where(Document.id == doc_id)
        )
        chunks = await s.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == doc_id)
        )
        jobs = await s.scalar(
            select(func.count()).select_from(DocumentJob).where(DocumentJob.document_id == doc_id)
        )
    return int(docs or 0), int(chunks or 0), int(jobs or 0)


async def test_delete_hides_now_and_purges_everything(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, PDF, space_id=space)).json()
    await world.ingest_all()
    assert (await counts(doc["id"]))[1] > 0

    deleted = await client.delete(f"/v1/documents/{doc['id']}", headers=reader)
    assert_response_matches_contract(deleted)

    assert deleted.status_code == 204
    listed = await client.get("/v1/documents", params={"space_id": space}, headers=reader)
    assert listed.json()["items"] == [] and listed.json()["total_documents"] == 0
    assert (await client.get(f"/v1/documents/{doc['id']}", headers=reader)).status_code == 404
    assert (await client.delete(f"/v1/documents/{doc['id']}", headers=reader)).status_code == 404

    await world.purge_all()
    assert world.storage.objects == {}
    assert await counts(doc["id"]) == (0, 0, 0)


async def test_delete_during_processing_is_not_overwritten(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, PDF, space_id=space)).json()
    await client.delete(f"/v1/documents/{doc['id']}", headers=reader)

    await world.ingest_all()  # job queued before the delete: must be a no-op now

    async with AsyncSessionLocal() as s:
        status = await s.scalar(select(Document.status).where(Document.id == uuid.UUID(doc["id"])))
    assert status == "DELETING"
    await world.purge_all()
    assert await counts(doc["id"]) == (0, 0, 0)


async def test_retry_failed_document(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, PDF, space_id=space)).json()
    world.queue.jobs.clear()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE documents SET status='FAILED', error_code='PROCESSING_FAILED' WHERE id=:id"
            ),
            {"id": doc["id"]},
        )

    retried = await client.post(f"/v1/documents/{doc['id']}/retry", headers=reader)
    assert_response_matches_contract(retried)

    assert retried.status_code == 200
    assert (retried.json()["status"], retried.json()["error_code"]) == ("QUEUED", None)
    assert [j for j, _ in world.queue.jobs] == [uuid.UUID(doc["id"])]
    assert (await counts(doc["id"]))[2] == 2  # a fresh job row
    await world.ingest_all()
    assert (await client.get(f"/v1/documents/{doc['id']}", headers=reader)).json()[
        "status"
    ] == "READY"


async def test_retry_ready_document_conflicts(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, PDF, space_id=space)).json()
    await world.ingest_all()

    response = await client.post(f"/v1/documents/{doc['id']}/retry", headers=reader)
    assert_response_matches_contract(response)

    assert (response.status_code, response.json()["code"]) == (409, "DOCUMENT_NOT_RETRYABLE")
    assert response.json()["status"] == "READY"


async def test_move_between_own_spaces(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    source = await new_space(client, reader, "Nguồn")
    target = await new_space(client, reader, "Đích")
    doc = (await upload(client, reader, PDF, space_id=source)).json()

    moved = await client.post(
        f"/v1/documents/{doc['id']}/move", json={"space_id": target}, headers=reader
    )
    assert_response_matches_contract(moved)

    assert moved.json()["space_id"] == target
    in_source = await client.get("/v1/documents", params={"space_id": source}, headers=reader)
    in_target = await client.get("/v1/documents", params={"space_id": target}, headers=reader)
    assert in_source.json()["items"] == []
    assert [d["id"] for d in in_target.json()["items"]] == [doc["id"]]


async def test_deleting_a_space_purges_its_files(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    keep = await new_space(client, reader, "Giữ lại")
    doomed = [(await upload(client, reader, PDF, space_id=space)).json() for _ in range(2)]
    kept = (await upload(client, reader, make_pdf(["kept"]), space_id=keep)).json()
    await world.ingest_all()
    assert len(world.storage.objects) == 3

    assert (await client.delete(f"/v1/spaces/{space}", headers=reader)).status_code == 204
    await world.purge_all()

    assert len(world.storage.objects) == 1
    for d in doomed:
        assert await counts(d["id"]) == (0, 0, 0)
    assert (await counts(kept["id"]))[0] == 1


async def test_sweep_requeues_stale_deletions(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, PDF, space_id=space)).json()
    await client.delete(f"/v1/documents/{doc['id']}", headers=reader)
    world.queue.purges.clear()  # the worker never got the job
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE documents SET updated_at = now() - interval '11 minutes' WHERE id=:id"),
            {"id": doc["id"]},
        )

    await world.pipeline.resume_stalled()

    assert [d for d, _ in world.queue.purges] == [uuid.UUID(doc["id"])]


async def test_purge_is_idempotent(world: World) -> None:
    missing = uuid.uuid4()
    assert await world.pipeline.purge(missing, "documents/x/y.pdf")
    assert await world.pipeline.purge(missing, "documents/x/y.pdf")


async def test_other_users_cannot_manage_documents(
    client: AsyncClient, reader: dict[str, str], world: World
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, PDF, space_id=space)).json()
    intruder = await sign_up(client, "intruder@example.com")
    their_space = await new_space(client, intruder, "Của tôi")

    attempts = [
        await client.delete(f"/v1/documents/{doc['id']}", headers=intruder),
        await client.post(f"/v1/documents/{doc['id']}/retry", headers=intruder),
        await client.post(
            f"/v1/documents/{doc['id']}/move", json={"space_id": their_space}, headers=intruder
        ),
        # owner moving into someone else's space
        await client.post(
            f"/v1/documents/{doc['id']}/move", json={"space_id": their_space}, headers=reader
        ),
    ]

    for r in attempts:
        assert (r.status_code, r.json()["code"]) == (404, "NOT_FOUND")
    after = (await client.get(f"/v1/documents/{doc['id']}", headers=reader)).json()
    assert (after["status"], after["space_id"]) == ("QUEUED", space)
    assert world.queue.purges == []
