"""
Conversations and asking questions (docs/specs/f7-qa.md, f8-history.md).

Asking has two phases. `prepare` runs inside the request (ownership, quota, retrieval,
saving the question), so its failures are plain JSON errors. `stream` then plays the
answer as SSE events (see streaming.py).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.integrations.llm_gateway.circuit_breaker import CircuitState
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.chat.citations import cited_document_ids, snapshots
from app.modules.chat.models import Conversation, Message
from app.modules.chat.presenters import message_out
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import MessageOut
from app.modules.chat.sources import FoundSources, SourceFinder
from app.modules.chat.streaming import AnswerStream, PreparedTurn
from app.modules.spaces.service import SpaceService
from app.modules.usage.quota import QuestionQuota

TITLE_CHARS = 80


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
        self, owner_id: uuid.UUID, space_id: uuid.UUID, limit: int
    ) -> list[Conversation]:
        await SpaceService(self._session).get(owner_id, space_id)
        return await self._repo.list_conversations(owner_id, space_id, limit)

    async def get_conversation(
        self, owner_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> tuple[Conversation, list[MessageOut]]:
        conversation = await self._require(owner_id, conversation_id)
        messages = await self._repo.messages(conversation.id)
        cited = set().union(*(cited_document_ids(m.citations) for m in messages))
        live = await self._repo.live_document_ids(owner_id, cited)
        return conversation, [message_out(m, live) for m in messages]

    async def delete_conversation(self, owner_id: uuid.UUID, conversation_id: uuid.UUID) -> None:
        conversation = await self._require(owner_id, conversation_id)
        await self._repo.delete_conversation(conversation)

    async def _require(self, owner_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
        conversation = await self._repo.get_conversation(owner_id, conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation")
        return conversation

    # ---------- asking ----------

    async def prepare(
        self,
        owner_id: uuid.UUID,
        conversation_id: uuid.UUID,
        question: str,
        document_ids: list[uuid.UUID] | None,
    ) -> PreparedTurn:
        conversation = await self._require(owner_id, conversation_id)
        await self._quota.require(owner_id)
        found = await SourceFinder(self._session, self._gateway).find(
            owner_id=owner_id,
            space_id=conversation.space_id,
            question=question,
            document_ids=document_ids,
        )
        mode = self._mode(found)
        history = await self._history(conversation.id)

        user_message = Message(
            conversation_id=conversation.id,
            owner_id=owner_id,
            role="user",
            content=question,
            mode="question",
            status="complete",
            citations=[],
            document_ids=(
                None if document_ids is None else [str(d) for d in found.selected_document_ids]
            ),
        )
        assistant = Message(
            conversation_id=conversation.id,
            owner_id=owner_id,
            role="assistant",
            content="",
            mode=mode,
            status="pending" if mode == "answer" else "complete",
            citations=[] if mode == "not_found" else snapshots(found.sources),
        )
        await self._repo.add(user_message)
        await self._repo.add(assistant)
        self._touch(conversation, question)
        await self._session.commit()
        await self._session.refresh(user_message)
        return PreparedTurn(
            owner_id=owner_id,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message_id=assistant.id,
            mode=mode,
            question=question,
            sources=found.sources,
            history=history,
        )

    def stream(self, turn: PreparedTurn) -> AsyncGenerator[str, None]:
        return AnswerStream(turn, self._gateway, self._quota).events()

    def _mode(self, found: FoundSources) -> str:
        if not found.sources:
            return "not_found"
        if found.ai_down or self._gateway.breaker.state == CircuitState.OPEN:
            return "retrieval_only"
        return "answer"

    async def _history(self, conversation_id: uuid.UUID) -> list[dict[str, str]]:
        """Recent question/answer pairs as plain text; old sources are not resent.

        A question whose answer has no text (not found, retrieval only, error) is left out
        together with its answer: a dangling question confuses the model about the new one.
        """
        recent = await self._repo.messages(conversation_id, limit=settings.CHAT_HISTORY_MESSAGES)
        history: list[dict[str, str]] = []
        for question, answer in zip(recent, recent[1:], strict=False):
            if _is_answered_pair(question, answer):
                history.append({"role": "user", "content": question.content})
                history.append({"role": "assistant", "content": answer.content})
        return history

    @staticmethod
    def _touch(conversation: Conversation, question: str) -> None:
        if conversation.title is None:
            conversation.title = question[:TITLE_CHARS]
        conversation.updated_at = datetime.now(UTC)


def _is_answered_pair(question: Message, answer: Message) -> bool:
    return (
        question.role == "user"
        and answer.role == "assistant"
        and bool(answer.content)
        and answer.status in ("complete", "partial")
    )
