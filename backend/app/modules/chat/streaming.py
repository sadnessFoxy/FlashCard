"""
Stream one answer as Server-Sent Events (docs/specs/f7-qa.md section 4).

Runs after the request handler has returned, so it saves through its own short DB
sessions (`AnswerStore`). Every way out of the stream leaves the assistant message in a
final state: complete, partial or error.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import update

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.chat.citations import Citation, keep_cited, snapshots
from app.modules.chat.models import Message
from app.modules.chat.presenters import message_out
from app.modules.chat.prompts import (
    SYSTEM_PROMPT,
    build_user_turn,
    could_be_not_found,
    is_not_found,
)
from app.modules.chat.sources import AI_DOWN_ERRORS
from app.modules.documents.retrieval import RetrievedChunk
from app.modules.usage.quota import QuestionQuota

logger = get_logger(__name__)

ANSWER_TEMPERATURE = 0.2


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@dataclass
class PreparedTurn:
    """Everything `prepare` decided; the stream only executes it."""

    owner_id: uuid.UUID
    conversation_id: uuid.UUID
    user_message: Message
    assistant_message_id: uuid.UUID
    mode: str
    question: str
    sources: list[RetrievedChunk]
    history: list[dict[str, str]] = field(default_factory=list)


class AnswerStore:
    """Writes the assistant message of one turn, each call in its own session."""

    def __init__(self, turn: PreparedTurn) -> None:
        self._turn = turn

    async def finish(
        self,
        content: str,
        status: str,
        *,
        mode: str | None = None,
        citations: list[Citation] | None = None,
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
                        Message.id == self._turn.assistant_message_id,
                        Message.owner_id == self._turn.owner_id,
                    )
                    .values(**values)
                )
                await session.commit()
        except Exception:
            logger.exception("Saving the assistant message failed")

    async def load(self) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            message = await session.get(Message, self._turn.assistant_message_id)
            assert message is not None
            return message_out(message).model_dump(mode="json")


class AnswerStream:
    def __init__(self, turn: PreparedTurn, gateway: LLMGateway, quota: QuestionQuota) -> None:
        self._turn = turn
        self._gateway = gateway
        self._quota = quota
        self._store = AnswerStore(turn)
        self._citations = snapshots(turn.sources)

    async def events(self) -> AsyncGenerator[str, None]:
        turn = self._turn
        yield sse(
            "start",
            {
                "user_message": message_out(turn.user_message).model_dump(mode="json"),
                "assistant_message_id": str(turn.assistant_message_id),
                "mode": turn.mode,
            },
        )
        if turn.mode != "not_found":
            yield sse("citations", {"citations": self._citations})
        if turn.mode != "answer":
            yield await self._done()
            return
        if not await self._quota.reserve(turn.owner_id):
            yield await self._quota_used_up()
            return
        async for event in self._generate():
            yield event

    async def _generate(self) -> AsyncGenerator[str, None]:
        held = ""  # text held back while it could still be the NOT_FOUND sentinel
        sent = ""
        finished = False
        try:
            async for chunk in self._gateway.chat_stream(
                self._prompt_messages(),
                system_prompt=SYSTEM_PROMPT,
                max_tokens=settings.CHAT_MAX_OUTPUT_TOKENS,
                temperature=ANSWER_TEMPERATURE,
                user_id=str(self._turn.owner_id),
            ):
                held += chunk
                if not sent and could_be_not_found(held):
                    continue
                sent += held
                yield sse("delta", {"text": held})
                held = ""
            answer = sent + held
            if is_not_found(answer):
                await self._quota.refund(self._turn.owner_id)  # "not found" is free
                await self._store.finish("", "complete", mode="not_found", citations=[])
            else:
                if held:
                    yield sse("delta", {"text": held})
                citations = keep_cited(answer, self._citations)
                await self._store.finish(answer.strip(), "complete", citations=citations)
            finished = True
            yield await self._done()
        except AppError as exc:
            finished = True
            yield await self._failed(
                sent, exc.code, exc.message, ai_down=isinstance(exc, AI_DOWN_ERRORS)
            )
        except Exception:
            finished = True
            logger.exception("Chat stream failed")
            yield await self._failed(sent, "INTERNAL_ERROR", "Something went wrong", ai_down=False)
        finally:
            if not finished:
                # The client went away mid-answer: keep what was produced.
                await asyncio.shield(self._save_interrupted(sent, "CLIENT_CLOSED"))

    def _prompt_messages(self) -> list[dict[str, str]]:
        turn = self._turn
        return [
            *turn.history,
            {"role": "user", "content": build_user_turn(turn.question, turn.sources)},
        ]

    async def _failed(self, sent: str, code: str, message: str, *, ai_down: bool) -> str:
        if not sent:
            await self._quota.refund(self._turn.owner_id)
            if ai_down:  # nothing shown yet: degrade to the passages instead (U8)
                await self._store.finish("", "complete", mode="retrieval_only")
                return await self._done()
        await self._save_interrupted(sent, code)
        return sse("error", {"code": code, "message": message})

    async def _save_interrupted(self, sent: str, code: str) -> None:
        await self._store.finish(sent.strip(), "partial" if sent else "error", error_code=code)

    async def _quota_used_up(self) -> str:
        quota = await self._quota.status(self._turn.owner_id)
        await self._store.finish("", "error", error_code="USER_QUOTA_EXCEEDED")
        return sse(
            "error",
            {
                "code": "USER_QUOTA_EXCEEDED",
                "message": "You have used all your queries for today",
                "quota_reset_at": quota.resets_at.isoformat(),
            },
        )

    async def _done(self) -> str:
        return sse("done", {"message": await self._store.load()})
