"""F10 acceptance criteria (docs/specs/f10-reviews.md section 9)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient, Response

from app.core.exceptions import AiQuotaExhaustedError
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.main import app
from app.modules.ai.providers.fake import FakeProvider
from tests.api.test_documents import new_space
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import Reader, new_reader

pytestmark = pytest.mark.usefixtures("clean_db")


async def call(client: AsyncClient, method: str, url: str, reader: Reader, **kw: Any) -> Response:
    response = await client.request(method, url, headers=reader.auth, **kw)
    assert_response_matches_contract(response)
    return response


async def deck_with_cards(
    client: AsyncClient, reader: Reader, n: int, space_id: str | None = None
) -> tuple[str, list[str]]:
    deck = await call(
        client,
        "POST",
        "/v1/decks",
        reader,
        json={"space_id": space_id or reader.space_id, "name": "Bộ"},
    )
    deck_id = deck.json()["id"]
    cards = await call(
        client,
        "POST",
        "/v1/flashcards",
        reader,
        json={"deck_id": deck_id, "cards": [{"front": f"Q{i}", "back": f"A{i}"} for i in range(n)]},
    )
    return deck_id, [c["id"] for c in cards.json()["items"]]


async def due(client: AsyncClient, reader: Reader, **params: str) -> dict[str, Any]:
    response = await call(
        client, "GET", "/v1/reviews/due", reader, params={"space_id": reader.space_id, **params}
    )
    assert response.status_code == 200
    return response.json()  # type: ignore[no-any-return]


def review(
    card_id: str, grade: str, at: datetime | None = None, review_id: str | None = None
) -> dict[str, str]:
    return {
        "id": review_id or str(uuid.uuid4()),
        "card_id": card_id,
        "grade": grade,
        "reviewed_at": (at or datetime.now(UTC)).isoformat(),
    }


async def submit(
    client: AsyncClient, reader: Reader, *reviews: dict[str, str]
) -> list[dict[str, Any]]:
    response = await call(client, "POST", "/v1/reviews", reader, json={"reviews": list(reviews)})
    assert response.status_code == 200
    return response.json()["results"]  # type: ignore[no-any-return]


# 1. New cards are due; grading reschedules them by SM-2 and they leave the due list.
async def test_grading_reschedules_cards(client: AsyncClient) -> None:
    reader = await new_reader(client)
    deck, (good, again) = await deck_with_cards(client, reader, 2)
    assert (await due(client, reader))["total_due"] == 2

    results = await submit(client, reader, review(good, "good"), review(again, "again"))

    assert [(r["status"], r["interval_days"]) for r in results] == [("applied", 1), ("applied", 0)]
    good_due = datetime.fromisoformat(results[0]["due_at"])
    assert timedelta(hours=23) < good_due - datetime.now(UTC) <= timedelta(days=1)
    again_due = datetime.fromisoformat(results[1]["due_at"])
    assert again_due - datetime.now(UTC) <= timedelta(minutes=10)
    assert (await due(client, reader))["total_due"] == 0
    deck_info = (await call(client, "GET", f"/v1/decks/{deck}", reader)).json()
    assert deck_info["due_count"] == 0


# 2. Resending a review (offline retry) changes nothing.
async def test_resent_review_is_a_noop(client: AsyncClient) -> None:
    reader = await new_reader(client)
    _, [card] = await deck_with_cards(client, reader, 1)
    first = review(card, "good")

    [applied] = await submit(client, reader, first)
    [again] = await submit(client, reader, first)
    [twice] = await submit(
        client,
        reader,
        {**first, "id": str(uuid.uuid4())},
    )

    assert again["status"] == "duplicate" and again["due_at"] == applied["due_at"]
    assert twice["status"] == "stale"  # same moment as the applied review: not newer


# 3. A batch from an offline queue applies oldest first; an older late review is stale.
async def test_offline_batch_order_and_stale_reviews(client: AsyncClient) -> None:
    reader = await new_reader(client)
    _, [card] = await deck_with_cards(client, reader, 1)
    now = datetime.now(UTC)
    later = review(card, "good", now - timedelta(minutes=1))
    earlier = review(card, "good", now - timedelta(minutes=5))

    results = await submit(client, reader, later, earlier)  # sent out of order

    assert [r["status"] for r in results] == ["applied", "applied"]
    assert results[0]["interval_days"] == 6  # second repetition
    [old] = await submit(client, reader, review(card, "again", now - timedelta(hours=1)))
    assert old["status"] == "stale" and old["interval_days"] == 6


# 4. Other users' cards are never touched; due lists stay in the space and deck.
async def test_ownership_and_filters(client: AsyncClient) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    _, [mine] = await deck_with_cards(client, reader, 1)
    second_deck, _ = await deck_with_cards(client, reader, 2)
    elsewhere = await new_space(client, reader.auth, "Khác")
    await deck_with_cards(client, reader, 3, space_id=elsewhere)

    [result] = await submit(client, other, review(mine, "easy"))
    assert result["status"] == "not_found"
    assert (await due(client, reader))["total_due"] == 3
    assert (await due(client, reader, deck_id=second_deck))["total_due"] == 2
    assert len((await due(client, reader, limit="1"))["items"]) == 1
    response = await call(
        client, "GET", "/v1/reviews/due", other, params={"space_id": reader.space_id}
    )
    assert response.status_code == 404


# 5. A device clock in the future cannot push a card far ahead.
async def test_future_review_time_is_clamped(client: AsyncClient) -> None:
    reader = await new_reader(client)
    _, [card] = await deck_with_cards(client, reader, 1)
    [result] = await submit(
        client, reader, review(card, "good", datetime.now(UTC) + timedelta(days=30))
    )
    assert datetime.fromisoformat(result["due_at"]) - datetime.now(UTC) < timedelta(
        days=1, minutes=10
    )


# 6. Reviews work while AI is down (U8).
async def test_reviews_work_when_ai_is_down(client: AsyncClient) -> None:
    provider = FakeProvider()
    gateway = LLMGateway(provider, breaker=CircuitBreaker())
    gateway.breaker.trip()
    provider.embed_script = [AiQuotaExhaustedError()]
    app.dependency_overrides[get_gateway] = lambda: gateway
    reader = await new_reader(client)
    _, [card] = await deck_with_cards(client, reader, 1)

    assert (await due(client, reader))["total_due"] == 1
    [result] = await submit(client, reader, review(card, "good"))
    assert result["status"] == "applied"


# 7. Validation: unknown grade, empty batch.
async def test_validation(client: AsyncClient) -> None:
    reader = await new_reader(client)
    _, [card] = await deck_with_cards(client, reader, 1)
    response = await call(
        client, "POST", "/v1/reviews", reader, json={"reviews": [review(card, "perfect")]}
    )
    assert response.status_code == 422
    response = await call(client, "POST", "/v1/reviews", reader, json={"reviews": []})
    assert response.status_code == 422
