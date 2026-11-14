"""Data access for document sections and summaries, always scoped to the owner (R4)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study.summaries.models import DocumentSection, DocumentSummary


class SummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sections(self, owner_id: uuid.UUID, document_id: uuid.UUID) -> list[DocumentSection]:
        result = await self._session.execute(
            select(DocumentSection)
            .where(DocumentSection.owner_id == owner_id, DocumentSection.document_id == document_id)
            .order_by(DocumentSection.position)
        )
        return list(result.scalars())

    async def summaries(self, section_ids: list[uuid.UUID]) -> dict[uuid.UUID, DocumentSummary]:
        if not section_ids:
            return {}
        result = await self._session.execute(
            select(DocumentSummary).where(DocumentSummary.section_id.in_(section_ids))
        )
        return {s.section_id: s for s in result.scalars()}

    async def add(self, *objects: DocumentSection | DocumentSummary) -> None:
        self._session.add_all(objects)
        await self._session.flush()
