"""Shared helpers for chat tests: topic-based fake embeddings, seeded documents, SSE parsing."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import pytest_asyncio
from httpx import AsyncClient, Response

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.main import app
from app.modules.ai.providers.fake import FakeProvider
from app.modules.documents.models import Document, DocumentChunk
from app.modules.documents.states import READY
from tests.api.test_documents import new_space, sign_up
from tests.contract_schema import assert_component_matches, assert_response_matches_contract

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
    storage_key: str | None = None,
) -> uuid.UUID:
    """Insert a document with one chunk per (page, text), embedded by topic."""
    provider = TopicProvider()
    async with AsyncSessionLocal() as s:
        doc = Document(
            owner_id=reader.user_id,
            space_id=uuid.UUID(space_id or reader.space_id),
            filename=name,
            storage_key=storage_key or f"test/{uuid.uuid4()}",
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
