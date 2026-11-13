"""F8 acceptance criteria (docs/specs/f8-citations-history.md section 9)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response

from app.integrations.object_storage import get_storage
from app.main import app
from app.modules.documents.states import PROCESSING
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import (
    TopicProvider,
    ai,
    ask,
    new_conversation,
    new_reader,
    seed_document,
)
from tests.fixtures.fakes import InMemoryStorage
from tests.fixtures.pdfs import make_pdf

__all__ = ["ai"]  # pytest fixture, imported for use by the tests below

pytestmark = pytest.mark.usefixtures("clean_db")

PAGES = [
    "Chapter 1 Limits\n\nA limit describes where a function goes.",
    "Chapter 2 Derivatives\n\nA derivative measures change.\n\nIt is the slope of the tangent.",
]


@pytest_asyncio.fixture
async def storage() -> AsyncGenerator[InMemoryStorage, None]:
    store = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: store
    yield store


async def page(client: AsyncClient, auth: dict[str, str], document_id: object, n: int) -> Response:
    response = await client.get(f"/v1/documents/{document_id}/pages/{n}", headers=auth)
    assert_response_matches_contract(response)
    return response


# 1. A cited page opens with its exact text, split into paragraphs.
async def test_page_returns_paragraphs_of_that_page(
    client: AsyncClient, storage: InMemoryStorage
) -> None:
    reader = await new_reader(client)
    storage.objects["k1"] = make_pdf(PAGES)
    doc = await seed_document(reader, "Giải tích.pdf", [(2, "derivative")], storage_key="k1")

    response = await page(client, reader.auth, doc, 2)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "Giải tích.pdf" and body["page"] == 2
    text = " ".join(body["paragraphs"])
    assert "A derivative measures change." in text and "limit" not in text


# 2. Page text is cached per owner: the PDF is downloaded once.
async def test_page_is_cached(client: AsyncClient, storage: InMemoryStorage) -> None:
    reader = await new_reader(client)
    storage.objects["k1"] = make_pdf(PAGES)
    doc = await seed_document(reader, "A.pdf", [(2, "x")], storage_key="k1")

    await page(client, reader.auth, doc, 1)
    await page(client, reader.auth, doc, 1)

    assert storage.downloads == 1


# 3. Out of range, someone else's or not READY.
async def test_page_errors(client: AsyncClient, storage: InMemoryStorage) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    storage.objects["k1"] = make_pdf(PAGES)
    doc = await seed_document(reader, "A.pdf", [(2, "x")], storage_key="k1")
    pending = await seed_document(reader, "B.pdf", [(1, "x")], status=PROCESSING)

    assert (await page(client, reader.auth, doc, 3)).status_code == 404
    assert (await page(client, other.auth, doc, 1)).status_code == 404
    response = await page(client, reader.auth, pending, 1)
    assert response.status_code == 409
    assert response.json()["code"] == "DOCUMENT_NOT_READY"
    response = await client.get(f"/v1/documents/{doc}/pages/0", headers=reader.auth)
    assert response.status_code == 422


# 4. History: list newest first, limit, delete removes the conversation and its messages.
async def test_list_limit_and_delete(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "A.pdf", [(1, "A derivative measures change.")])
    first = await new_conversation(client, reader)
    second = await new_conversation(client, reader)
    await ask(client, reader, first, "What is a derivative?")  # makes `first` the newest

    response = await client.get(
        "/v1/conversations", params={"space_id": reader.space_id}, headers=reader.auth
    )
    assert [c["id"] for c in response.json()["items"]] == [first, second]
    response = await client.get(
        "/v1/conversations",
        params={"space_id": reader.space_id, "limit": 1},
        headers=reader.auth,
    )
    assert_response_matches_contract(response)
    assert [c["id"] for c in response.json()["items"]] == [first]

    response = await client.delete(f"/v1/conversations/{first}", headers=reader.auth)
    assert response.status_code == 204
    assert_response_matches_contract(response)
    response = await client.get(f"/v1/conversations/{first}", headers=reader.auth)
    assert response.status_code == 404


# 5. Someone else's conversation cannot be deleted.
async def test_cannot_delete_other_users_conversation(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    conversation = await new_conversation(client, reader)

    response = await client.delete(f"/v1/conversations/{conversation}", headers=other.auth)
    assert response.status_code == 404
    response = await client.get(f"/v1/conversations/{conversation}", headers=reader.auth)
    assert response.status_code == 200
