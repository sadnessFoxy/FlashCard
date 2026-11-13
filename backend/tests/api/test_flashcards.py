"""F9 acceptance criteria (docs/specs/f9-flashcards.md section 9)."""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import delete

from app.core.config import settings
from app.core.exceptions import AiQuotaExhaustedError
from app.core.redis import get_redis
from app.db.session import AsyncSessionLocal
from app.modules.documents.models import Document
from app.modules.documents.states import PROCESSING
from app.modules.usage.quota import CardSuggestionQuota
from tests.api.test_documents import new_space
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import (
    Reader,
    TopicProvider,
    ai,
    ask,
    final,
    new_conversation,
    new_reader,
    seed_document,
)

__all__ = ["ai"]  # pytest fixture, imported for use by the tests below

pytestmark = pytest.mark.usefixtures("clean_db")


async def call(client: AsyncClient, method: str, url: str, reader: Reader, **kw: Any) -> Response:
    response = await client.request(method, url, headers=reader.auth, **kw)
    assert_response_matches_contract(response)
    return response


async def new_deck(client: AsyncClient, reader: Reader, name: str = "Đạo hàm") -> str:
    response = await call(
        client, "POST", "/v1/decks", reader, json={"space_id": reader.space_id, "name": name}
    )
    assert response.status_code == 201
    return str(response.json()["id"])


async def add_cards(
    client: AsyncClient, reader: Reader, deck_id: str, cards: list[dict[str, Any]]
) -> Response:
    return await call(
        client, "POST", "/v1/flashcards", reader, json={"deck_id": deck_id, "cards": cards}
    )


async def suggest(client: AsyncClient, reader: Reader, source: dict[str, Any], count: int = 5):  # noqa: ANN201
    return await call(
        client,
        "POST",
        "/v1/flashcards/suggestions",
        reader,
        json={"space_id": reader.space_id, "source": source, "count": count},
    )


def cards_json(*cards: tuple[str, str, int]) -> str:
    return json.dumps({"cards": [{"front": f, "back": b, "source": s} for f, b, s in cards]})


async def card_suggestions_used(client: AsyncClient, reader: Reader) -> int:
    body = (await call(client, "GET", "/v1/usage/me", reader)).json()
    return int(body["card_suggestions"]["used_today"])


# 1. Deck lifecycle with counts; deleting a deck deletes its cards.
async def test_deck_crud_and_counts(client: AsyncClient) -> None:
    reader = await new_reader(client)
    deck = await new_deck(client, reader, "  Đạo   hàm ")
    await add_cards(
        client, reader, deck, [{"front": "f1", "back": "b1"}, {"front": "f2", "back": "b2"}]
    )

    listed = (
        await call(client, "GET", "/v1/decks", reader, params={"space_id": reader.space_id})
    ).json()["items"]
    assert [(d["name"], d["card_count"], d["due_count"]) for d in listed] == [("Đạo hàm", 2, 2)]

    renamed = await call(client, "PATCH", f"/v1/decks/{deck}", reader, json={"name": "Giới hạn"})
    assert renamed.json()["name"] == "Giới hạn"

    assert (await call(client, "DELETE", f"/v1/decks/{deck}", reader)).status_code == 204
    assert (await call(client, "GET", f"/v1/decks/{deck}", reader)).status_code == 404


# 2. Cards: create by hand, edit, delete; sources are snapshots of the owner's documents.
async def test_cards_with_sources(client: AsyncClient) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    doc = await seed_document(reader, "Giải tích.pdf", [(1, "a"), (3, "b")])
    foreign = await seed_document(other, "Theirs.pdf", [(1, "x")])
    deck = await new_deck(client, reader)

    response = await add_cards(
        client,
        reader,
        deck,
        [
            {
                "front": " Đạo hàm? ",
                "back": "Hệ số góc",
                "source": {"document_id": str(doc), "page": 3},
            },
            {"front": "Q2", "back": "A2", "source": {"document_id": str(doc), "page": 99}},
            {"front": "Q3", "back": "A3", "source": {"document_id": str(foreign), "page": 1}},
        ],
    )
    assert response.status_code == 201
    first, second, third = response.json()["items"]
    assert first["front"] == "Đạo hàm?" and first["origin"] == "manual"
    assert first["source"] == {"document_id": str(doc), "document_name": "Giải tích.pdf", "page": 3}
    assert second["source"]["page"] is None  # page beyond the document is dropped
    assert third["source"] is None  # someone else's document is dropped silently (R4)

    edited = await call(
        client, "PATCH", f"/v1/flashcards/{first['id']}", reader, json={"back": "Slope"}
    )
    assert edited.json()["back"] == "Slope" and edited.json()["front"] == "Đạo hàm?"
    assert (
        await call(client, "DELETE", f"/v1/flashcards/{second['id']}", reader)
    ).status_code == 204

    async with AsyncSessionLocal() as s:
        await s.execute(delete(Document).where(Document.id == doc))
        await s.commit()
    detail = (await call(client, "GET", f"/v1/decks/{deck}", reader)).json()
    assert [c["front"] for c in detail["cards"]] == ["Đạo hàm?", "Q3"]
    assert detail["cards"][0]["source"] == {
        "document_id": None,
        "document_name": "Giải tích.pdf",
        "page": 3,
    }


# 3. Other users' decks and cards: 404 everywhere.
async def test_other_users_decks_and_cards_are_404(client: AsyncClient) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    deck = await new_deck(client, reader)
    [card] = (await add_cards(client, reader, deck, [{"front": "f", "back": "b"}])).json()["items"]

    assert (await call(client, "GET", f"/v1/decks/{deck}", other)).status_code == 404
    assert (await call(client, "DELETE", f"/v1/decks/{deck}", other)).status_code == 404
    assert (await add_cards(client, other, deck, [{"front": "f", "back": "b"}])).status_code == 404
    assert (
        await call(client, "PATCH", f"/v1/flashcards/{card['id']}", other, json={"front": "x"})
    ).status_code == 404
    assert (await call(client, "DELETE", f"/v1/flashcards/{card['id']}", other)).status_code == 404
    response = await call(
        client, "POST", "/v1/decks", other, json={"space_id": reader.space_id, "name": "x"}
    )
    assert response.status_code == 404


# 4. Limits and validation.
async def test_deck_limit_and_validation(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = await new_reader(client)
    deck = await new_deck(client, reader)
    monkeypatch.setattr(settings, "MAX_CARDS_PER_DECK", 2)

    response = await add_cards(client, reader, deck, [{"front": "f", "back": "b"}] * 3)
    assert response.status_code == 409
    assert response.json() == {
        "code": "DECK_FULL",
        "message": "This deck has reached its card limit",
        "max_cards": 2,
    }
    assert (
        await add_cards(client, reader, deck, [{"front": "  ", "back": "b"}])
    ).status_code == 422
    assert (await add_cards(client, reader, deck, [])).status_code == 422


# 5. Suggestions from a page range: only that text reaches the AI; nothing is saved.
async def test_suggestions_from_document_pages(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(
        reader,
        "Giải tích.pdf",
        [(1, "Limits intro."), (2, "Derivative is slope."), (3, "Integrals.")],
    )
    ai.generate_script = [
        cards_json(("What is a derivative?", "The slope.", 1), ("Bad source", "x", 9))
    ]

    response = await suggest(
        client,
        reader,
        {"type": "document", "document_id": str(doc), "page_start": 2, "page_end": 2},
    )

    assert response.status_code == 200
    first, second = response.json()["items"]
    assert first["source"] == {"document_id": str(doc), "document_name": "Giải tích.pdf", "page": 2}
    assert second["source"] is None
    prompt = ai.generate_calls[0]["prompt"]
    assert "Derivative is slope." in prompt and "Limits intro." not in prompt
    assert "reader@example.com" not in prompt  # R10
    assert "untrusted" in ai.generate_calls[0]["system_prompt"]
    assert await card_suggestions_used(client, reader) == 1
    usage = (await call(client, "GET", "/v1/usage/me", reader)).json()
    assert usage["used_today"] == 0  # questions are counted separately


# 6. Suggestions from a Q&A answer use its cited passages.
async def test_suggestions_from_answer(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    doc = await seed_document(reader, "Giải tích.pdf", [(4, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = ["It measures change [1]."]
    _, events = await ask(client, reader, conversation, "What is a derivative?")
    message_id = final(events)["id"]
    ai.generate_script = [cards_json(("Derivative?", "Measures change.", 1))]

    response = await suggest(client, reader, {"type": "message", "message_id": message_id})

    [card] = response.json()["items"]
    assert card["source"] == {"document_id": str(doc), "document_name": "Giải tích.pdf", "page": 4}
    assert "It measures change [1]." in ai.generate_calls[0]["prompt"]
    other_space = await new_space(client, other.auth, "Khác")
    response = await call(
        client,
        "POST",
        "/v1/flashcards/suggestions",
        other,
        json={"space_id": other_space, "source": {"type": "message", "message_id": message_id}},
    )
    assert response.status_code == 404


# 7. AI down or unusable output: 503 and the quota is given back.
async def test_suggestion_failures_refund_quota(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "A.pdf", [(1, "Derivative is slope.")])
    ai.generate_script = [AiQuotaExhaustedError(), "not json at all"]
    source = {"type": "document", "document_id": str(doc)}

    assert (await suggest(client, reader, source)).status_code == 503
    assert (await suggest(client, reader, source)).status_code == 503
    assert await card_suggestions_used(client, reader) == 0


# 8. Quota used up: 429 without calling the AI.
async def test_suggestion_quota_exceeded(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "A.pdf", [(1, "x")])
    key, _ = CardSuggestionQuota()._key(reader.user_id)
    await get_redis().set(key, settings.CARD_SUGGESTION_DAILY_LIMIT)

    response = await suggest(client, reader, {"type": "document", "document_id": str(doc)})

    assert response.status_code == 429
    assert response.json()["code"] == "USER_QUOTA_EXCEEDED"
    assert ai.generate_calls == []


# 9. Source checks: not READY, outside the space, empty page range.
async def test_suggestion_source_checks(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    pending = await seed_document(reader, "P.pdf", [(1, "x")], status=PROCESSING)
    elsewhere_space = await new_space(client, reader.auth, "Khác")
    elsewhere = await seed_document(reader, "E.pdf", [(1, "x")], space_id=elsewhere_space)
    doc = await seed_document(reader, "A.pdf", [(1, "x")])

    response = await suggest(client, reader, {"type": "document", "document_id": str(pending)})
    assert response.status_code == 409
    response = await suggest(client, reader, {"type": "document", "document_id": str(elsewhere)})
    assert response.status_code == 404
    response = await suggest(
        client, reader, {"type": "document", "document_id": str(doc), "page_start": 5}
    )
    assert response.status_code == 422 and response.json()["code"] == "SOURCE_EMPTY"
    response = await suggest(client, reader, {"type": "document", "document_id": str(uuid.uuid4())})
    assert response.status_code == 404
    assert ai.generate_calls == []


# 10. Deleting the space deletes its decks.
async def test_space_deletion_removes_decks(client: AsyncClient) -> None:
    reader = await new_reader(client)
    deck = await new_deck(client, reader)
    assert (
        await call(client, "DELETE", f"/v1/spaces/{reader.space_id}", reader)
    ).status_code == 204
    assert (await call(client, "GET", f"/v1/decks/{deck}", reader)).status_code == 404
