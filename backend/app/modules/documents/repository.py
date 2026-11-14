"""Data access for documents, chunks and jobs. Every user-facing query filters by owner (R4)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, DocumentChunk, DocumentJob
from app.modules.documents.states import COUNTED, sources_for


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------ documents

    async def lock_owner(self, owner_id: uuid.UUID) -> None:
        """Serialize uploads per user so the document limit cannot be raced past."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"documents:{owner_id}"}
        )

    async def count_for_owner(self, owner_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Document)
            .where(Document.owner_id == owner_id, Document.status.in_(COUNTED))
        )
        return int(result.scalar_one())

    async def get_for_owner(self, owner_id: uuid.UUID, document_id: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, owner_id: uuid.UUID, key: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.owner_id == owner_id, Document.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def list_in_space(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(
                Document.owner_id == owner_id,
                Document.space_id == space_id,
                Document.status != "DELETING",
            )
            .order_by(Document.created_at.desc(), Document.id)
        )
        return list(result.scalars())

    async def get(self, document_id: uuid.UUID) -> Document | None:
        """Worker-side lookup; the worker acts for the owner recorded on the row."""
        return await self._session.get(Document, document_id, populate_existing=True)

    async def add(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        return document

    async def transition(
        self,
        document_id: uuid.UUID,
        target: str,
        *,
        sources: Sequence[str] | None = None,
        error_code: str | None = None,
        **values: object,
    ) -> bool:
        """Conditional update (R6): only moves from an allowed source status. True if it moved."""
        allowed = set(sources) if sources is not None else set(sources_for(target))
        allowed &= set(sources_for(target))
        result = await self._session.execute(
            update(Document)
            .where(Document.id == document_id, Document.status.in_(allowed))
            .values(status=target, error_code=error_code, updated_at=func.now(), **values)
            .execution_options(synchronize_session=False)
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def stale(self, status: str, older_than: datetime) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(Document.id).where(Document.status == status, Document.updated_at < older_than)
        )
        return list(result.scalars())

    async def in_space_for_owner(
        self, owner_id: uuid.UUID, space_id: uuid.UUID
    ) -> list[tuple[uuid.UUID, str]]:
        """(id, storage_key) of every document in the space, DELETING ones included."""
        result = await self._session.execute(
            select(Document.id, Document.storage_key).where(
                Document.owner_id == owner_id, Document.space_id == space_id
            )
        )
        return [(row[0], row[1]) for row in result.all()]

    async def set_text_source(self, document_id: uuid.UUID, text_source: str) -> None:
        await self._session.execute(
            update(Document).where(Document.id == document_id).values(text_source=text_source)
        )

    async def all_for_owner(self, owner_id: uuid.UUID) -> list[tuple[uuid.UUID, str]]:
        """(id, storage_key) of every document of the owner, in any status."""
        result = await self._session.execute(
            select(Document.id, Document.storage_key).where(Document.owner_id == owner_id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def delete_if_deleting(self, document_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(Document)
            .where(Document.id == document_id, Document.status == "DELETING")
            .execution_options(synchronize_session=False)
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def stale_deleting(self, older_than: datetime) -> list[tuple[uuid.UUID, str]]:
        result = await self._session.execute(
            select(Document.id, Document.storage_key).where(
                Document.status == "DELETING", Document.updated_at < older_than
            )
        )
        return [(row[0], row[1]) for row in result.all()]

    # --------------------------------------------------------------- chunks

    async def chunk_count(self, document_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
        return int(result.scalar_one())

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self._session.add_all(chunks)

    async def unembedded(self, document_id: uuid.UUID, limit: int) -> list[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id, DocumentChunk.embedding.is_(None))
            .order_by(DocumentChunk.chunk_index)
            .limit(limit)
        )
        return list(result.scalars())

    # ----------------------------------------------------------------- jobs

    async def add_job(self, job: DocumentJob) -> DocumentJob:
        self._session.add(job)
        await self._session.flush()
        return job

    async def latest_job(self, document_id: uuid.UUID) -> DocumentJob | None:
        result = await self._session.execute(
            select(DocumentJob)
            .where(DocumentJob.document_id == document_id)
            .order_by(DocumentJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
