"""
Chapter summaries (U15): chapters are found once per document from the stored PDF;
each summary is made on request, saved, and never recomputed.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AiTemporarilyUnavailableError, NotFoundError
from app.core.logging import get_logger
from app.integrations.llm_gateway.gateway import LLMGateway
from app.integrations.object_storage import ObjectStorage
from app.modules.documents.access import ready_document
from app.modules.documents.formats import UnsupportedFileError, extract_pages
from app.modules.documents.models import Document
from app.modules.study.source_material import SourceMaterial, SourceMaterialLoader
from app.modules.study.summaries.models import DocumentSection, DocumentSummary
from app.modules.study.summaries.prompts import (
    SYSTEM_PROMPT,
    DraftPoint,
    build_request,
    parse_points,
)
from app.modules.study.summaries.repository import SummaryRepository
from app.modules.study.summaries.schemas import (
    SectionListOut,
    SectionOut,
    SummaryOut,
    SummaryPointOut,
)
from app.modules.study.summaries.sections import SectionDraft, find_sections, page_parts
from app.modules.usage.quota import SummaryQuota

logger = get_logger(__name__)

SUMMARY_TEMPERATURE = 0.3


class SummaryService:
    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage,
        gateway: LLMGateway,
        quota: SummaryQuota,
    ) -> None:
        self._session = session
        self._repo = SummaryRepository(session)
        self._storage = storage
        self._gateway = gateway
        self._quota = quota

    async def sections(self, owner_id: uuid.UUID, document_id: uuid.UUID) -> SectionListOut:
        document = await ready_document(self._session, owner_id, document_id)
        sections = await self._sections_of(document)
        summaries = await self._repo.summaries([s.id for s in sections])
        return SectionListOut(
            document_id=document.id,
            filename=document.filename,
            items=[_section_out(s, summaries.get(s.id)) for s in sections],
        )

    async def summarize(
        self, owner_id: uuid.UUID, document_id: uuid.UUID, section_id: uuid.UUID
    ) -> tuple[SummaryOut, bool]:
        """(summary, created). A saved summary is returned as is, without using the quota."""
        document = await ready_document(self._session, owner_id, document_id)
        section = next((s for s in await self._sections_of(document) if s.id == section_id), None)
        if section is None:
            raise NotFoundError("Section")
        existing = (await self._repo.summaries([section.id])).get(section.id)
        if existing is not None:
            return _summary_out(existing), False

        await self._quota.require(owner_id)
        material = await SourceMaterialLoader(
            self._session, settings.SUMMARY_SOURCE_CHARS
        ).from_document(
            owner_id, document.space_id, document.id, section.page_start, section.page_end
        )
        points = await self._quota.spend(owner_id, lambda: self._generate(owner_id, material))
        summary = DocumentSummary(
            section_id=section.id,
            owner_id=owner_id,
            points=[{"text": p.text, "page": p.page} for p in points],
            model=settings.GEMINI_CHAT_MODEL,
        )
        await self._repo.add(summary)
        await self._session.refresh(summary)
        return _summary_out(summary), True

    async def _sections_of(self, document: Document) -> list[DocumentSection]:
        """Found on first use from the stored PDF, then kept."""
        saved = await self._repo.sections(document.owner_id, document.id)
        if saved:
            return saved
        drafts = await self._find(document)
        sections = [
            DocumentSection(
                document_id=document.id,
                owner_id=document.owner_id,
                position=i,
                title=d.title[:200] if d.title else None,
                page_start=d.page_start,
                page_end=d.page_end,
            )
            for i, d in enumerate(drafts)
        ]
        await self._repo.add(*sections)
        return sections

    async def _find(self, document: Document) -> list[SectionDraft]:
        data = await self._storage.download_file(document.storage_key)
        try:
            pages = extract_pages(data, document.file_kind)
        except UnsupportedFileError:
            logger.warning("Section detection failed (document_id=%s)", document.id)
            return page_parts(document.page_count, settings.SUMMARY_PAGES_PER_PART)
        return find_sections(
            pages,
            pages_per_part=settings.SUMMARY_PAGES_PER_PART,
            max_sections=settings.SUMMARY_MAX_SECTIONS,
        )

    async def _generate(self, owner_id: uuid.UUID, material: SourceMaterial) -> list[DraftPoint]:
        raw = await self._gateway.generate(
            build_request(material.passages),
            system_prompt=SYSTEM_PROMPT,
            max_tokens=settings.SUMMARY_MAX_OUTPUT_TOKENS,
            temperature=SUMMARY_TEMPERATURE,
            response_format={"type": "json_object"},
            user_id=str(owner_id),
        )
        points = parse_points(raw, material.passages)
        if not points:
            logger.warning("Summary output was unusable (%d chars)", len(raw))
            raise AiTemporarilyUnavailableError()
        return points


def _summary_out(summary: DocumentSummary) -> SummaryOut:
    return SummaryOut(
        points=[SummaryPointOut(text=p["text"], page=p.get("page")) for p in summary.points],
        created_at=summary.created_at,
    )


def _section_out(section: DocumentSection, summary: DocumentSummary | None) -> SectionOut:
    return SectionOut(
        id=section.id,
        position=section.position,
        title=section.title,
        page_start=section.page_start,
        page_end=section.page_end,
        summary=_summary_out(summary) if summary else None,
    )
