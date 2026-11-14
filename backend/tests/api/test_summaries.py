"""F12 acceptance criteria (docs/specs/f12-summaries.md section 9)."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response

from app.core.config import settings
from app.core.exceptions import AiQuotaExhaustedError
from app.core.redis import get_redis
from app.integrations.object_storage import get_storage
from app.main import app
from app.modules.documents.states import PROCESSING
from app.modules.usage.quota import SummaryQuota
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import Reader, TopicProvider, ai, new_reader, seed_document
from tests.fixtures.fakes import InMemoryStorage
from tests.fixtures.pdfs import make_pdf

__all__ = ["ai"]  # pytest fixture, imported for use by the tests below

pytestmark = pytest.mark.usefixtures("clean_db")

PAGES = [
    "Chapter 1 Limits\n\nA limit describes where a function goes.",
    "Chapter 2 Derivatives\n\nA derivative measures change.",
    "More on derivatives: the slope of the tangent.",
]
CHUNKS = [
    (1, "A limit describes where a function goes."),
    (2, "A derivative measures change."),
    (3, "The slope of the tangent."),
]


@pytest_asyncio.fixture
async def storage() -> AsyncGenerator[InMemoryStorage, None]:
    store = InMemoryStorage()
    store.objects["k1"] = make_pdf(PAGES)
    app.dependency_overrides[get_storage] = lambda: store
    yield store


async def call(client: AsyncClient, method: str, url: str, reader: Reader, **kw: Any) -> Response:
    response = await client.request(method, url, headers=reader.auth, **kw)
    assert_response_matches_contract(response)
    return response


def points_json(*items: tuple[str, int]) -> str:
    return json.dumps({"points": [{"text": text, "source": source} for text, source in items]})


async def sections(client: AsyncClient, reader: Reader, doc: object) -> list[dict[str, Any]]:
    response = await call(client, "GET", f"/v1/documents/{doc}/sections", reader)
    assert response.status_code == 200
    return response.json()["items"]  # type: ignore[no-any-return]


async def summarize(client: AsyncClient, reader: Reader, doc: object, section: str) -> Response:
    return await call(client, "POST", f"/v1/documents/{doc}/sections/{section}/summary", reader)


# 1. Chapters come from the headings and are found only once.
async def test_sections_from_headings(client: AsyncClient, storage: InMemoryStorage) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "Giải tích.pdf", CHUNKS, storage_key="k1")

    first = await sections(client, reader, doc)
    assert [(s["title"], s["page_start"], s["page_end"], s["summary"]) for s in first] == [
        ("Chapter 1 Limits", 1, 1, None),
        ("Chapter 2 Derivatives", 2, 3, None),
    ]
    again = await sections(client, reader, doc)
    assert [s["id"] for s in again] == [s["id"] for s in first]
    assert storage.downloads == 1


# 2. Summarizing uses only that chapter's text, saves the result, and never recomputes it.
async def test_summary_is_made_once(
    client: AsyncClient, storage: InMemoryStorage, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "Giải tích.pdf", CHUNKS, storage_key="k1")
    chapter_two = (await sections(client, reader, doc))[1]["id"]
    ai.generate_script = [
        points_json(("Derivatives measure change.", 1), ("Slope of the tangent.", 2))
    ]

    made = await summarize(client, reader, doc, chapter_two)

    assert made.status_code == 201
    assert [(p["text"], p["page"]) for p in made.json()["points"]] == [
        ("Derivatives measure change.", 2),
        ("Slope of the tangent.", 3),
    ]
    prompt = ai.generate_calls[0]["prompt"]
    assert "A derivative measures change." in prompt and "A limit" not in prompt
    saved = await summarize(client, reader, doc, chapter_two)
    assert saved.status_code == 200 and saved.json() == made.json()
    assert len(ai.generate_calls) == 1
    listed = await sections(client, reader, doc)
    assert listed[1]["summary"]["points"] == made.json()["points"]
    usage = (await call(client, "GET", "/v1/usage/me", reader)).json()
    assert usage["summaries"]["used_today"] == 1


# 3. Other users, unknown sections, documents not READY.
async def test_access(client: AsyncClient, storage: InMemoryStorage) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    doc = await seed_document(reader, "A.pdf", CHUNKS, storage_key="k1")
    pending = await seed_document(reader, "P.pdf", CHUNKS, status=PROCESSING)
    section = (await sections(client, reader, doc))[0]["id"]

    assert (await call(client, "GET", f"/v1/documents/{doc}/sections", other)).status_code == 404
    assert (await summarize(client, other, doc, section)).status_code == 404
    unknown = "00000000-0000-0000-0000-000000000000"
    assert (await summarize(client, reader, doc, unknown)).status_code == 404
    response = await call(client, "GET", f"/v1/documents/{pending}/sections", reader)
    assert response.status_code == 409


# 4. AI failures give the quota back; no quota left: 429 without AI; saved ones still show.
async def test_quota_and_failures(
    client: AsyncClient, storage: InMemoryStorage, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "A.pdf", CHUNKS, storage_key="k1")
    first, second = [s["id"] for s in await sections(client, reader, doc)]
    ai.generate_script = ["garbage", points_json(("Point.", 1)), AiQuotaExhaustedError()]

    assert (await summarize(client, reader, doc, first)).status_code == 503  # unusable output
    assert (await summarize(client, reader, doc, first)).status_code == 201
    assert (await summarize(client, reader, doc, second)).status_code == 503  # AI quota gone
    usage = (await call(client, "GET", "/v1/usage/me", reader)).json()
    assert usage["summaries"]["used_today"] == 1  # failures gave the quota back

    key, _ = SummaryQuota()._key(reader.user_id)
    await get_redis().set(key, settings.SUMMARY_DAILY_LIMIT)
    calls = len(ai.generate_calls)
    assert (await summarize(client, reader, doc, second)).status_code == 429
    assert (await summarize(client, reader, doc, first)).status_code == 200  # saved: still shown
    assert len(ai.generate_calls) == calls


# 5. A document without headings is split into page ranges.
async def test_page_range_parts(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    store = InMemoryStorage()
    store.objects["plain"] = make_pdf(["Plain text one.", "Plain text two.", "Plain text three."])
    app.dependency_overrides[get_storage] = lambda: store
    monkeypatch.setattr(settings, "SUMMARY_PAGES_PER_PART", 2)
    reader = await new_reader(client)
    doc = await seed_document(reader, "Plain.pdf", [(1, "a"), (3, "b")], storage_key="plain")

    parts = await sections(client, reader, doc)
    assert [(s["title"], s["page_start"], s["page_end"]) for s in parts] == [
        (None, 1, 2),
        (None, 3, 3),
    ]
