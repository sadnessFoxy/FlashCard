"""F7 acceptance criteria (docs/specs/f7-qa.md section 9)."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response
from sqlalchemy import delete

from app.core.config import settings
from app.core.exceptions import AiQuotaExhaustedError, AiTemporarilyUnavailableError
from app.core.redis import get_redis
from app.db.session import AsyncSessionLocal
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.main import app
from app.modules.ai.providers.fake import FakeProvider
from app.modules.documents.models import Document, DocumentChunk
from app.modules.documents.states import PROCESSING, READY
from app.modules.usage.quota import QuestionQuota
from tests.api.test_documents import new_space, sign_up
from tests.contract_schema import assert_component_matches, assert_response_matches_contract

pytestmark = pytest.mark.usefixtures("clean_db")

DIMS = settings.EMBEDDING_DIMENSIONS
# Topic keywords map to orthogonal axes: same topic -> distance 0, other topic -> distance 1.
TOPICS = ["derivative", "integral", "matrix", "photosynthesis"]
UNRELATED_AXIS = DIMS - 1


def axis(i: int) -> list[float]:
    vec = [0.0] * DIMS
    vec[i] = 1.0
    return vec


class TopicProvider(FakeProvider):
    def _vector(self, text: str) -> list[float]:
        for i, topic in enumerate(TOPICS):
            if topic in text.lower():
                return axis(i)
        return axis(UNRELATED_AXIS)


async def _noop(*_: object, **__: object) -> None:
    return None


@pytest_asyncio.fixture
async def ai() -> AsyncGenerator[TopicProvider, None]:
    provider = TopicProvider()
    gateway = LLMGateway(provider, breaker=CircuitBreaker(), sleep=_noop, recorder=_noop)
    app.dependency_overrides[get_gateway] = lambda: gateway
    yield provider


@dataclass
class Reader:
    auth: dict[str, str]
    user_id: uuid.UUID
    space_id: str


async def new_reader(client: AsyncClient, email: str = "reader@example.com") -> Reader:
    auth = await sign_up(client, email)
    me = (await client.get("/v1/me", headers=auth)).json()
    return Reader(auth, uuid.UUID(me["id"]), await new_space(client, auth))


async def seed_document(
    reader: Reader,
    name: str,
    pages: list[tuple[int, str]],
    status: str = READY,
    space_id: str | None = None,
) -> uuid.UUID:
    """Insert a document with one chunk per (page, text), embedded by topic."""
    provider = TopicProvider()
    async with AsyncSessionLocal() as s:
        doc = Document(
            owner_id=reader.user_id,
            space_id=uuid.UUID(space_id or reader.space_id),
            filename=name,
            storage_key=f"test/{uuid.uuid4()}",
            size_bytes=100,
            page_count=max(p for p, _ in pages),
            sha256="0" * 64,
            status=status,
            idempotency_key=uuid.uuid4(),
        )
        s.add(doc)
        await s.flush()
        for i, (page, text) in enumerate(pages):
            s.add(
                DocumentChunk(
                    document_id=doc.id,
                    owner_id=reader.user_id,
                    chunk_index=i,
                    page_start=page,
                    page_end=page,
                    content=text,
                    token_estimate=len(text) // 4,
                    embedding=provider._vector(text),
                )
            )
        await s.commit()
        return doc.id


async def new_conversation(client: AsyncClient, reader: Reader) -> str:
    response = await client.post(
        "/v1/conversations", json={"space_id": reader.space_id}, headers=reader.auth
    )
    assert response.status_code == 201
    assert_response_matches_contract(response)
    return str(response.json()["id"])


def parse_sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


EVENT_SCHEMAS = {
    "start": "ChatStartEvent",
    "citations": "ChatCitationsEvent",
    "delta": "ChatDeltaEvent",
    "done": "ChatDoneEvent",
    "error": "ChatErrorEvent",
}


async def ask(
    client: AsyncClient,
    reader: Reader,
    conversation_id: str,
    question: str,
    document_ids: list[str] | None = None,
) -> tuple[Response, list[tuple[str, dict[str, Any]]]]:
    body: dict[str, Any] = {"content": question}
    if document_ids is not None:
        body["document_ids"] = document_ids
    response = await client.post(
        f"/v1/conversations/{conversation_id}/messages", json=body, headers=reader.auth
    )
    assert_response_matches_contract(response)
    if response.status_code != 200:
        return response, []
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    for name, data in events:
        assert_component_matches(EVENT_SCHEMAS[name], data)
    return response, events


async def used_today(client: AsyncClient, reader: Reader) -> int:
    response = await client.get("/v1/usage/me", headers=reader.auth)
    assert_response_matches_contract(response)
    return int(response.json()["used_today"])


def names(events: list[tuple[str, dict[str, Any]]]) -> list[str]:
    return [n for n, _ in events]


def final(events: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    name, data = events[-1]
    assert name == "done", events
    return data["message"]  # type: ignore[no-any-return]


# 1. Grounded answer: start, citations, delta..., done; cites the right page; uses one question.
async def test_grounded_answer_streams_with_citations(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    calc = await seed_document(
        reader, "Giải tích.pdf", [(2, "A derivative measures change."), (5, "An integral sums.")]
    )
    await seed_document(reader, "Đại số.pdf", [(1, "A matrix is a table of numbers.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = ["A derivative is the rate of change [1]."]

    response, events = await ask(client, reader, conversation, "What is a derivative?")

    assert response.status_code == 200
    assert names(events)[:2] == ["start", "citations"]
    assert "delta" in names(events) and names(events)[-1] == "done"
    assert events[0][1]["mode"] == "answer"
    text = "".join(d["text"] for n, d in events if n == "delta")
    assert text == "A derivative is the rate of change [1]."
    message = final(events)
    assert message["mode"] == "answer" and message["status"] == "complete"
    assert message["content"] == text
    assert [(c["document_id"], c["page_start"]) for c in message["citations"]] == [(str(calc), 2)]
    assert await used_today(client, reader) == 1

    call = ai.chat_calls[0]
    assert "untrusted" in call["system_prompt"]
    turn = call["messages"][-1]["content"]
    assert "A derivative measures change." in turn and "matrix" not in turn
    assert "reader@example.com" not in json.dumps(call)  # R10

    detail = await client.get(f"/v1/conversations/{conversation}", headers=reader.auth)
    assert_response_matches_contract(detail)
    body = detail.json()
    assert body["title"] == "What is a derivative?"
    assert [(m["role"], m["mode"]) for m in body["messages"]] == [
        ("user", "question"),
        ("assistant", "answer"),
    ]


# 2. Nothing relevant: not_found, Gemini not called, no question used.
async def test_no_relevant_source_is_not_found_without_ai(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(1, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)

    _, events = await ask(client, reader, conversation, "Who won the 1998 world cup?")

    assert names(events) == ["start", "done"]
    assert events[0][1]["mode"] == "not_found"
    message = final(events)
    assert message["mode"] == "not_found" and message["citations"] == []
    assert ai.chat_calls == []
    assert await used_today(client, reader) == 0


async def test_model_not_found_reply_is_not_streamed(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(1, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = ["NOT_FOUND"]

    _, events = await ask(client, reader, conversation, "Who invented the derivative?")

    assert "delta" not in names(events)
    message = final(events)
    assert message["mode"] == "not_found" and message["content"] == ""
    assert await used_today(client, reader) == 0


# 3. Other users' and non-READY documents never reach the sources, even when named.
async def test_foreign_and_unready_documents_never_become_sources(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    mine = await seed_document(reader, "Mine.pdf", [(3, "My derivative notes.")])
    pending = await seed_document(
        reader, "Pending.pdf", [(1, "Derivative draft.")], status=PROCESSING
    )
    foreign = await seed_document(other, "Theirs.pdf", [(1, "Their derivative secrets.")])
    conversation = await new_conversation(client, reader)

    _, events = await ask(
        client,
        reader,
        conversation,
        "Explain the derivative",
        document_ids=[str(mine), str(pending), str(foreign)],
    )
    cited = {c["document_id"] for c in final(events)["citations"]}
    assert cited == {str(mine)}
    assert "secrets" not in json.dumps(ai.chat_calls)

    _, events = await ask(
        client, reader, conversation, "Explain the derivative", document_ids=[str(foreign)]
    )
    assert final(events)["mode"] == "not_found"
    assert events[0][1]["user_message"]["document_ids"] == []


async def test_document_selection_limits_sources(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    first = await seed_document(reader, "A.pdf", [(1, "Derivative in A.")])
    await seed_document(reader, "B.pdf", [(1, "Derivative in B.")])
    conversation = await new_conversation(client, reader)

    _, events = await ask(client, reader, conversation, "Derivative?", document_ids=[str(first)])
    assert {c["document_id"] for c in final(events)["citations"]} == {str(first)}


# 4. Daily quota used up: 429 with remaining 0 and reset time, no AI call.
async def test_quota_exceeded_returns_429_without_ai(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(1, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    key, _ = QuestionQuota()._key(reader.user_id)
    await get_redis().set(key, settings.USER_DAILY_QUERY_LIMIT)

    response, _ = await ask(client, reader, conversation, "What is a derivative?")

    assert response.status_code == 429
    body = response.json()
    assert body["code"] == "USER_QUOTA_EXCEEDED"
    assert body["quota_remaining"] == 0 and body["quota_reset_at"]
    assert ai.embed_calls == [] and ai.chat_calls == []


# 5. AI down: retrieval_only with citations, question refunded.
async def test_ai_quota_exhausted_falls_back_to_retrieval_only(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(4, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = [AiQuotaExhaustedError()]

    _, events = await ask(client, reader, conversation, "What is a derivative?")

    message = final(events)
    assert message["mode"] == "retrieval_only" and message["status"] == "complete"
    assert [c["page_start"] for c in message["citations"]] == [4]
    assert await used_today(client, reader) == 0

    # The breaker is now open: the next question starts in retrieval_only without calling AI.
    calls = len(ai.chat_calls)
    _, events = await ask(client, reader, conversation, "Derivative again?")
    assert events[0][1]["mode"] == "retrieval_only"
    assert final(events)["mode"] == "retrieval_only"
    assert len(ai.chat_calls) == calls


# 6. Stream breaks mid-answer: error event, partial text saved.
async def test_mid_stream_failure_saves_partial(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(1, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = [("A derivative is [1]", AiTemporarilyUnavailableError())]

    _, events = await ask(client, reader, conversation, "What is a derivative?")

    assert names(events)[-1] == "error"
    assert events[-1][1]["code"] == "AI_TEMPORARILY_UNAVAILABLE"
    detail = (await client.get(f"/v1/conversations/{conversation}", headers=reader.auth)).json()
    answer = detail["messages"][-1]
    assert answer["status"] == "partial" and answer["content"] == "A derivative is [1]"
    assert answer["error_code"] == "AI_TEMPORARILY_UNAVAILABLE"


# 7. Deleted document: citation keeps name and pages, document_id becomes null.
async def test_citation_survives_document_deletion(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "Giải tích.pdf", [(7, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = ["Rate of change [1]."]
    await ask(client, reader, conversation, "What is a derivative?")

    async with AsyncSessionLocal() as s:
        await s.execute(delete(Document).where(Document.id == doc))
        await s.commit()

    response = await client.get(f"/v1/conversations/{conversation}", headers=reader.auth)
    assert_response_matches_contract(response)
    [citation] = response.json()["messages"][-1]["citations"]
    assert citation["document_id"] is None
    assert citation["document_name"] == "Giải tích.pdf" and citation["page_start"] == 7


# 8. Other users' conversations and spaces: 404.
async def test_other_users_conversation_is_404(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    conversation = await new_conversation(client, reader)

    response = await client.get(f"/v1/conversations/{conversation}", headers=other.auth)
    assert response.status_code == 404
    assert_response_matches_contract(response)
    response, _ = await ask(client, other, conversation, "Derivative?")
    assert response.status_code == 404
    response = await client.post(
        "/v1/conversations", json={"space_id": reader.space_id}, headers=other.auth
    )
    assert response.status_code == 404
    response = await client.get(
        "/v1/conversations", params={"space_id": reader.space_id}, headers=other.auth
    )
    assert response.status_code == 404


async def test_history_is_sent_and_conversations_are_listed(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(1, "A derivative measures change.")])
    conversation = await new_conversation(client, reader)
    ai.chat_script = ["First answer [1].", "Second answer [1]."]
    await ask(client, reader, conversation, "What is a derivative?")
    await ask(client, reader, conversation, "And its derivative rules?")

    history = ai.chat_calls[1]["messages"]
    assert [m["role"] for m in history] == ["user", "assistant", "user"]
    assert history[0]["content"] == "What is a derivative?"
    assert history[1]["content"] == "First answer [1]."

    response = await client.get(
        "/v1/conversations", params={"space_id": reader.space_id}, headers=reader.auth
    )
    assert_response_matches_contract(response)
    assert [c["id"] for c in response.json()["items"]] == [conversation]


async def test_blank_or_too_long_question_is_rejected(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    conversation = await new_conversation(client, reader)
    response, _ = await ask(client, reader, conversation, "   ")
    assert response.status_code == 422
    response, _ = await ask(client, reader, conversation, "x" * 2001)
    assert response.status_code == 422


async def test_space_deletion_removes_conversations(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    conversation = await new_conversation(client, reader)
    assert (
        await client.delete(f"/v1/spaces/{reader.space_id}", headers=reader.auth)
    ).status_code == 204
    response = await client.get(f"/v1/conversations/{conversation}", headers=reader.auth)
    assert response.status_code == 404


async def test_keyword_fallback_survives_tsquery_syntax(
    client: AsyncClient, ai: TopicProvider
) -> None:
    reader = await new_reader(client)
    await seed_document(reader, "Giải tích.pdf", [(2, "Đạo hàm là tốc độ thay đổi.")])
    conversation = await new_conversation(client, reader)
    ai.embed_script = [AiQuotaExhaustedError()]

    _, events = await ask(client, reader, conversation, "đạo hàm & | ! :* ( là gì?")

    message = final(events)
    assert message["mode"] == "retrieval_only"
    assert [c["page_start"] for c in message["citations"]] == [2]
