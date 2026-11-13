"""
Q&A over the owner's READY documents (docs/specs/f7-qa.md).

`prepare` runs inside the request (validation, quota peek, retrieval, persisting the
question) so failures there are plain JSON errors. `stream` then yields SSE events and
uses its own short DB sessions, because the request session is gone once streaming starts.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
    AppError,
    NotFoundError,
    UserQuotaExceededError,
)
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.integrations.llm_gateway.circuit_breaker import CircuitState
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.chat.models import Conversation, Message
from app.modules.chat.prompts import (
    NOT_FOUND,
    SYSTEM_PROMPT,
    build_user_turn,
    cited_indexes,
    is_not_found,
)
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import MessageOut
from app.modules.documents.models import Document
from app.modules.documents.retrieval import (
    RetrievedChunk,
    keyword_search,
    ready_document_ids,
    search_chunks,
    select_sources,
)
from app.modules.documents.states import DELETING
from app.modules.spaces.service import SpaceService
from app.modules.usage.quota import QuestionQuota

logger = get_logger(__name__)

SNIPPET_CHARS = 600
TITLE_CHARS = 80
# Errors that switch the answer to retrieval-only mode instead of failing (U8).
AI_DOWN_ERRORS = (AiQuotaExhaustedError, AiTemporarilyUnavailableError, AiRateLimitedError)


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def citation_snapshot(index: int, chunk: RetrievedChunk) -> dict[str, Any]:
    snippet = chunk.content.strip()
    if len(snippet) > SNIPPET_CHARS:
        snippet = snippet[:SNIPPET_CHARS].rstrip() + "…"
    return {
        "index": index,
        "document_id": str(chunk.document_id),
        "document_name": chunk.document_name,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "snippet": snippet,
    }


@dataclass
class PreparedTurn:
    owner_id: uuid.UUID
    conversation_id: uuid.UUID
    user_message: Message
    assistant_message_id: uuid.UUID
    mode: str
    question: str
    sources: list[RetrievedChunk]
    history: list[dict[str, str]] = field(default_factory=list)


class ChatService:
    def __init__(self, session: AsyncSession, gateway: LLMGateway, quota: QuestionQuota) -> None:
        self._session = session
        self._repo = ChatRepository(session)
        self._gateway = gateway
        self._quota = quota

    # ---------- conversations ----------

    async def create_conversation(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> Conversation:
        await SpaceService(self._session).get(owner_id, space_id)  # 404 if not the owner's
        conversation = Conversation(owner_id=owner_id, space_id=space_id)
        await self._repo.add(conversation)
        await self._session.refresh(conversation)
        return conversation

    async def list_conversations(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, limit: int = 20
    ) -> list[Conversation]:
        await SpaceService(self._session).get(owner_id, space_id)
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.owner_id == owner_id, Conversation.space_id == space_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def get_conversation(
        self, owner_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> tuple[Conversation, list[MessageOut]]:
        conversation = await self._require(owner_id, conversation_id)
        messages = await self._repo.messages(conversation.id)
        live = await self._live_document_ids(owner_id, messages)
        return conversation, [message_out(m, live) for m in messages]

    async def _require(self, owner_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
        conversation = await self._repo.get_conversation(owner_id, conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation")
        return conversation

    async def _live_document_ids(self, owner_id: uuid.UUID, messages: list[Message]) -> set[str]:
        cited = {c["document_id"] for m in messages for c in m.citations if c.get("document_id")}
        if not cited:
            return set()
        result = await self._session.execute(
            select(Document.id).where(
                Document.owner_id == owner_id,
                Document.id.in_([uuid.UUID(d) for d in cited]),
                Document.status != DELETING,
            )
        )
        return {str(d) for d in result.scalars()}

    # ---------- asking ----------

    async def prepare(
        self,
        owner_id: uuid.UUID,
        conversation_id: uuid.UUID,
        question: str,
        document_ids: list[uuid.UUID] | None,
    ) -> PreparedTurn:
        conversation = await self._require(owner_id, conversation_id)

        quota = await self._quota.status(owner_id)
        if quota.remaining <= 0:
            raise UserQuotaExceededError(0, quota.resets_at.isoformat())

        ready = await ready_document_ids(self._session, owner_id, conversation.space_id)
        # IDs outside the owner's READY documents in this space are dropped silently (R4).
        selected = ready if document_ids is None else [d for d in document_ids if d in set(ready)]

        sources: list[RetrievedChunk] = []
        ai_down = False
        if selected:
            try:
                [vector] = await self._gateway.embed([question], "query", user_id=str(owner_id))
                candidates = await search_chunks(
                    self._session,
                    owner_id=owner_id,
                    space_id=conversation.space_id,
                    query_vector=vector,
                    document_ids=selected,
                    candidates=settings.CHAT_CANDIDATES,
                )
                max_distance = settings.CHAT_MAX_DISTANCE
            except AI_DOWN_ERRORS:
                ai_down = True
                candidates = await keyword_search(
                    self._session,
                    owner_id=owner_id,
                    space_id=conversation.space_id,
                    question=question,
                    document_ids=selected,
                    limit=settings.CHAT_CANDIDATES,
                )
                max_distance = 1.0
            sources = select_sources(
                candidates,
                max_distance=max_distance,
                top_k=settings.CHAT_TOP_K,
                per_document=settings.CHAT_MAX_PER_DOCUMENT,
            )

        if not sources:
            mode = "not_found"
        elif ai_down or self._gateway.breaker.state == CircuitState.OPEN:
            mode = "retrieval_only"
        else:
            mode = "answer"

        history = await self._history(conversation.id)
        user_message = Message(
            conversation_id=conversation.id,
            owner_id=owner_id,
            role="user",
            content=question,
            mode="question",
            status="complete",
            citations=[],
            document_ids=None if document_ids is None else [str(d) for d in selected],
        )
        await self._repo.add(user_message)
        snapshots = [citation_snapshot(i, s) for i, s in enumerate(sources, start=1)]
        assistant = Message(
            conversation_id=conversation.id,
            owner_id=owner_id,
            role="assistant",
            content="",
            mode=mode,
            status="pending" if mode == "answer" else "complete",
            citations=[] if mode == "not_found" else snapshots,
        )
        await self._repo.add(assistant)
        if conversation.title is None:
            conversation.title = question[:TITLE_CHARS]
        conversation.updated_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(user_message)
        return PreparedTurn(
            owner_id=owner_id,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message_id=assistant.id,
            mode=mode,
            question=question,
            sources=sources,
            history=history,
        )

    async def _history(self, conversation_id: uuid.UUID) -> list[dict[str, str]]:
        """Recent finished turns as plain text; old sources are not resent."""
        recent = await self._repo.messages(conversation_id, limit=settings.CHAT_HISTORY_MESSAGES)
        return [
            {"role": m.role, "content": m.content}
            for m in recent
            if m.content and m.status in ("complete", "partial")
        ]

    async def stream(self, turn: PreparedTurn) -> AsyncGenerator[str, None]:
        yield sse(
            "start",
            {
                "user_message": message_out(turn.user_message).model_dump(mode="json"),
                "assistant_message_id": str(turn.assistant_message_id),
                "mode": turn.mode,
            },
        )
        snapshots = [citation_snapshot(i, s) for i, s in enumerate(turn.sources, start=1)]
        if turn.mode != "not_found":
            yield sse("citations", {"citations": snapshots})
        if turn.mode != "answer":
            yield sse("done", {"message": await self._load(turn)})
            return

        if not await self._quota.reserve(turn.owner_id):
            quota = await self._quota.status(turn.owner_id)
            await self._finish(turn, "", "error", error_code="USER_QUOTA_EXCEEDED")
            yield sse(
                "error",
                {
                    "code": "USER_QUOTA_EXCEEDED",
                    "message": "You have used all your queries for today",
                    "quota_reset_at": quota.resets_at.isoformat(),
                },
            )
            return

        messages = [
            *turn.history,
            {"role": "user", "content": build_user_turn(turn.question, turn.sources)},
        ]
        buffer = ""  # held back while it could still be the NOT_FOUND sentinel
        sent = ""
        finished = False
        try:
            async for chunk in self._gateway.chat_stream(
                messages,
                system_prompt=SYSTEM_PROMPT,
                max_tokens=settings.CHAT_MAX_OUTPUT_TOKENS,
                temperature=0.2,
                user_id=str(turn.owner_id),
            ):
                buffer += chunk
                if not sent and _maybe_not_found(buffer):
                    continue
                sent += buffer
                yield sse("delta", {"text": buffer})
                buffer = ""
            answer = sent + buffer
            if is_not_found(answer):
                # "Not found" never uses a question, even when the model decided it.
                await self._quota.refund(turn.owner_id)
                await self._finish(turn, "", "complete", mode="not_found", citations=[])
            else:
                if buffer:
                    yield sse("delta", {"text": buffer})
                cited = cited_indexes(answer, len(snapshots))
                kept = [snapshots[i - 1] for i in cited] if cited else snapshots
                await self._finish(turn, answer.strip(), "complete", citations=kept)
            finished = True
            yield sse("done", {"message": await self._load(turn)})
        except AppError as exc:
            finished = True
            if not sent:
                await self._quota.refund(turn.owner_id)
                if isinstance(exc, AI_DOWN_ERRORS):
                    await self._finish(turn, "", "complete", mode="retrieval_only")
                    yield sse("done", {"message": await self._load(turn)})
                    return
                await self._finish(turn, "", "error", error_code=exc.code)
            else:
                await self._finish(turn, sent.strip(), "partial", error_code=exc.code)
            yield sse("error", {"code": exc.code, "message": exc.message})
        except Exception:
            finished = True
            logger.exception("Chat stream failed")
            if not sent:
                await self._quota.refund(turn.owner_id)
            await self._finish(
                turn, sent.strip(), "partial" if sent else "error", error_code="INTERNAL_ERROR"
            )
            yield sse("error", {"code": "INTERNAL_ERROR", "message": "Something went wrong"})
        finally:
            if not finished:
                # Client went away mid-answer: keep what was produced.
                await asyncio.shield(
                    self._finish(
                        turn,
                        sent.strip(),
                        "partial" if sent else "error",
                        error_code="CLIENT_CLOSED",
                    )
                )

    async def _finish(
        self,
        turn: PreparedTurn,
        content: str,
        status: str,
        *,
        mode: str | None = None,
        citations: list[dict[str, Any]] | None = None,
        error_code: str | None = None,
    ) -> None:
        values: dict[str, Any] = {"content": content, "status": status, "error_code": error_code}
        if mode is not None:
            values["mode"] = mode
        if citations is not None:
            values["citations"] = citations
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(Message)
                    .where(
                        Message.id == turn.assistant_message_id,
                        Message.owner_id == turn.owner_id,
                    )
                    .values(**values)
                )
                await session.commit()
        except Exception:
            logger.exception("Saving the assistant message failed")

    async def _load(self, turn: PreparedTurn) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            message = await session.get(Message, turn.assistant_message_id)
            assert message is not None
            return message_out(message).model_dump(mode="json")


def _maybe_not_found(text: str) -> bool:
    head = text.strip().upper()
    return len(head) < len(NOT_FOUND) + 1 and NOT_FOUND.startswith(head.rstrip("."))


def message_out(message: Message, live_document_ids: set[str] | None = None) -> MessageOut:
    citations = message.citations or []
    if live_document_ids is not None:
        citations = [
            {
                **c,
                "document_id": c["document_id"]
                if c.get("document_id") in live_document_ids
                else None,
            }
            for c in citations
        ]
    return MessageOut.model_validate(
        {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "mode": message.mode,
            "status": message.status,
            "error_code": message.error_code,
            "citations": citations,
            "document_ids": message.document_ids,
            "created_at": message.created_at,
        }
    )
