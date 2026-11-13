"""F5 upload API (spec f5 section 9, criteria 2-8). Storage and queue are in-memory fakes."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response
from sqlalchemy import update

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.object_storage import get_storage
from app.main import app
from app.modules.documents.queue import get_job_queue
from app.modules.users.models import User
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.fakes import InMemoryStorage, RecordingQueue
from tests.fixtures.pdfs import make_blank_pdf, make_encrypted_pdf, make_pdf

pytestmark = pytest.mark.usefixtures("clean_db")

PDF = make_pdf(["Chapter 1\n\nSome text about derivatives.", "Page two."])


@pytest_asyncio.fixture
async def fakes() -> AsyncGenerator[tuple[InMemoryStorage, RecordingQueue], None]:
    storage, queue = InMemoryStorage(), RecordingQueue()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_job_queue] = lambda: queue
    yield storage, queue


async def sign_up(
    client: AsyncClient, email: str = "reader@example.com", *, verified: bool = True
) -> dict[str, str]:
    """Register; `verified` marks the email verified as if the emailed code was entered."""
    body = (
        await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "a long enough passphrase"},
            headers={"X-Client-Platform": "native"},
        )
    ).json()
    if verified:
        async with AsyncSessionLocal() as s:
            await s.execute(
                update(User).where(User.email == email).values(email_verified_at=datetime.now(UTC))
            )
            await s.commit()
    return {"Authorization": f"Bearer {body['access_token']}"}


async def consent(client: AsyncClient, auth: dict[str, str]) -> Response:
    return await client.post(
        "/v1/me/consents",
        json={"kind": "ai_processing", "version": settings.AI_CONSENT_VERSION},
        headers=auth,
    )


async def new_space(client: AsyncClient, auth: dict[str, str], name: str = "Giải tích") -> str:
    return str((await client.post("/v1/spaces", json={"name": name}, headers=auth)).json()["id"])


async def upload(
    client: AsyncClient,
    auth: dict[str, str],
    data: bytes = PDF,
    *,
    space_id: str | None = None,
    key: str | None = None,
    filename: str = "Giáo trình.pdf",
) -> Response:
    form = {"space_id": space_id} if space_id else {}
    response = await client.post(
        "/v1/documents",
        files={"file": (filename, data, "application/pdf")},
        data=form,
        headers=auth | {"Idempotency-Key": key or str(uuid.uuid4())},
    )
    assert_response_matches_contract(response)
    return response


@pytest_asyncio.fixture
async def reader(client: AsyncClient) -> dict[str, str]:
    auth = await sign_up(client)
    assert (await consent(client, auth)).status_code == 201
    return auth


# ------------------------------------------------------------- consent


async def test_upload_requires_consent(client: AsyncClient, fakes: object) -> None:
    auth = await sign_up(client)
    space = await new_space(client, auth)

    response = await upload(client, auth, space_id=space)

    assert (response.status_code, response.json()["code"]) == (403, "CONSENT_REQUIRED")
    assert response.json()["version"] == settings.AI_CONSENT_VERSION


async def test_consent_is_idempotent_and_versioned(client: AsyncClient) -> None:
    auth = await sign_up(client)

    first, second = await consent(client, auth), await consent(client, auth)
    stale = await client.post(
        "/v1/me/consents", json={"kind": "ai_processing", "version": "old"}, headers=auth
    )
    listed = await client.get("/v1/me/consents", headers=auth)

    assert (first.status_code, second.status_code, stale.status_code) == (201, 200, 422)
    assert stale.json()["current_version"] == settings.AI_CONSENT_VERSION
    assert listed.json()["current_versions"] == {"ai_processing": settings.AI_CONSENT_VERSION}
    assert len(listed.json()["items"]) == 1
    for r in (first, second, stale, listed):
        assert_response_matches_contract(r)


# -------------------------------------------------------------- upload


async def test_upload_queues_and_stores(
    client: AsyncClient, reader: dict[str, str], fakes: tuple[InMemoryStorage, RecordingQueue]
) -> None:
    storage, queue = fakes
    space = await new_space(client, reader)

    response = await upload(client, reader, space_id=space)

    assert response.status_code == 202
    doc = response.json()
    assert doc["status"] == "QUEUED" and doc["page_count"] == 2
    assert doc["filename"] == "Giáo trình.pdf" and doc["space_id"] == space
    assert queue.jobs == [(uuid.UUID(doc["id"]), 0)]
    [key] = storage.objects
    assert key.endswith(f"{doc['id']}.pdf") and "Giáo" not in key
    assert storage.objects[key] == PDF


async def test_listing_and_detail(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    space = await new_space(client, reader)
    other_space = await new_space(client, reader, "Hóa")
    doc = (await upload(client, reader, space_id=space)).json()
    await upload(client, reader, space_id=other_space)

    listed = await client.get("/v1/documents", params={"space_id": space}, headers=reader)
    detail = await client.get(f"/v1/documents/{doc['id']}", headers=reader)

    assert [d["id"] for d in listed.json()["items"]] == [doc["id"]]
    assert listed.json()["total_documents"] == 2
    assert listed.json()["max_documents"] == settings.MAX_DOCUMENTS_PER_USER
    assert detail.json() == doc
    for r in (listed, detail):
        assert_response_matches_contract(r)


@pytest.mark.parametrize(
    ("data", "status", "code"),
    [
        (b"PK\x03\x04 not a pdf at all", 415, "FILE_TYPE_NOT_SUPPORTED"),
        (b"%PDF-1.4 truncated nonsense", 415, "FILE_TYPE_NOT_SUPPORTED"),
        (make_encrypted_pdf(), 422, "PDF_ENCRYPTED"),
    ],
)
async def test_rejected_files_store_nothing(
    client: AsyncClient,
    reader: dict[str, str],
    fakes: tuple[InMemoryStorage, RecordingQueue],
    data: bytes,
    status: int,
    code: str,
) -> None:
    space = await new_space(client, reader)

    response = await upload(client, reader, data, space_id=space)

    assert (response.status_code, response.json()["code"]) == (status, code)
    assert fakes[0].objects == {} and fakes[1].jobs == []


async def test_too_large(
    client: AsyncClient, reader: dict[str, str], fakes: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 1)
    space = await new_space(client, reader)
    big = PDF + b"\n%" + b"x" * (1024 * 1024)

    response = await upload(client, reader, big, space_id=space)

    assert (response.status_code, response.json()["code"]) == (413, "FILE_TOO_LARGE")
    assert response.json()["max_size_mb"] == 1


async def test_too_many_pages(
    client: AsyncClient, reader: dict[str, str], fakes: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MAX_PAGES", 2)
    space = await new_space(client, reader)

    response = await upload(client, reader, make_pdf(["a", "b", "c"]), space_id=space)

    assert (response.status_code, response.json()["code"]) == (422, "TOO_MANY_PAGES")


async def test_document_limit(
    client: AsyncClient, reader: dict[str, str], fakes: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MAX_DOCUMENTS_PER_USER", 2)
    space = await new_space(client, reader)
    for _ in range(2):
        assert (await upload(client, reader, space_id=space)).status_code == 202

    response = await upload(client, reader, space_id=space)

    assert (response.status_code, response.json()["code"]) == (409, "DOCUMENT_LIMIT_REACHED")
    assert response.json()["max_documents"] == 2


async def test_scanned_pdf_is_accepted_at_upload(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    space = await new_space(client, reader)

    response = await upload(client, reader, make_blank_pdf(2), space_id=space)

    assert response.status_code == 202  # detected by the worker (NO_TEXT_LAYER)


# --------------------------------------------------------- idempotency


async def test_same_key_and_file_returns_original(
    client: AsyncClient, reader: dict[str, str], fakes: tuple[InMemoryStorage, RecordingQueue]
) -> None:
    space = await new_space(client, reader)
    key = str(uuid.uuid4())

    first = await upload(client, reader, space_id=space, key=key)
    again = await upload(client, reader, space_id=space, key=key)

    assert (first.status_code, again.status_code) == (202, 200)
    assert again.json()["id"] == first.json()["id"]
    assert len(fakes[0].objects) == 1 and len(fakes[1].jobs) == 1


async def test_same_key_different_file_conflicts(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    space = await new_space(client, reader)
    key = str(uuid.uuid4())
    await upload(client, reader, space_id=space, key=key)

    response = await upload(client, reader, make_pdf(["other"]), space_id=space, key=key)

    assert (response.status_code, response.json()["code"]) == (409, "IDEMPOTENCY_KEY_REUSED")


async def test_idempotency_key_is_required(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    space = await new_space(client, reader)

    response = await client.post(
        "/v1/documents",
        files={"file": ("a.pdf", PDF, "application/pdf")},
        data={"space_id": space},
        headers=reader,
    )

    assert response.status_code == 422
    assert {"field": "Idempotency-Key", "type": "missing"} in response.json()["errors"]


# --------------------------------------------------------------- spaces


async def test_first_upload_without_space_creates_default(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    doc = (await upload(client, reader, filename="Giải tích 1.pdf")).json()

    spaces = (await client.get("/v1/spaces", headers=reader)).json()["items"]

    assert [s["name"] for s in spaces] == ["Giải tích 1"]
    assert doc["space_id"] == spaces[0]["id"]


async def test_space_required_once_user_has_spaces(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    await new_space(client, reader)

    response = await upload(client, reader)

    assert (response.status_code, response.json()["code"]) == (422, "SPACE_REQUIRED")


async def test_other_users_space_and_documents_are_404(
    client: AsyncClient, reader: dict[str, str], fakes: object
) -> None:
    space = await new_space(client, reader)
    doc = (await upload(client, reader, space_id=space)).json()
    intruder = await sign_up(client, "intruder@example.com")
    await consent(client, intruder)

    responses = [
        await upload(client, intruder, space_id=space),
        await client.get("/v1/documents", params={"space_id": space}, headers=intruder),
        await client.get(f"/v1/documents/{doc['id']}", headers=intruder),
    ]

    for r in responses:
        assert (r.status_code, r.json()["code"]) == (404, "NOT_FOUND")
        assert "Giáo" not in r.text
