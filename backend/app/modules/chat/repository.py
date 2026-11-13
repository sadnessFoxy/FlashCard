"""Data access for conversations and messages, always scoped to the owner (R4)."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.models import Conversation, Message
from app.modules.documents.models import Document
from app.modules.documents.states import DELETING


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_conversation(
        self, owner_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self, owner_id: uuid.UUID, space_id: uuid.UUID, limit: int
    ) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.owner_id == owner_id, Conversation.space_id == space_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def delete_conversation(self, conversation: Conversation) -> None:
        # Messages go with it (ON DELETE CASCADE).
        await self._session.execute(
            delete(Conversation).where(
                Conversation.id == conversation.id,
                Conversation.owner_id == conversation.owner_id,
            )
        )

    async def messages(self, conversation_id: uuid.UUID, limit: int | None = None) -> list[Message]:
        """Oldest first; with `limit`, only the most recent ones."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.role.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        rows = list((await self._session.execute(stmt)).scalars())
        rows.reverse()
        return rows

    async def live_document_ids(self, owner_id: uuid.UUID, document_ids: set[str]) -> set[str]:
        """Which of these documents still exist for the owner."""
        if not document_ids:
            return set()
        result = await self._session.execute(
            select(Document.id).where(
                Document.owner_id == owner_id,
                Document.id.in_([uuid.UUID(d) for d in document_ids]),
                Document.status != DELETING,
            )
        )
        return {str(d) for d in result.scalars()}

    async def add(self, obj: Conversation | Message) -> None:
        self._session.add(obj)
        await self._session.flush()
