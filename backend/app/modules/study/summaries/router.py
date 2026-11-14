"""Router for chapter summaries (/v1/documents/{id}/sections), contract tag `summaries`."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.integrations.object_storage import ObjectStorage, get_storage
from app.modules.auth.dependencies import get_current_user
from app.modules.study.summaries.schemas import SectionListOut, SummaryOut
from app.modules.study.summaries.service import SummaryService
from app.modules.usage.quota import SummaryQuota, get_summary_quota
from app.modules.users.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]

router = APIRouter()


def get_summary_service(
    db: Db,
    storage: Annotated[ObjectStorage, Depends(get_storage)],
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
    quota: Annotated[SummaryQuota, Depends(get_summary_quota)],
) -> SummaryService:
    return SummaryService(db, storage, gateway, quota)


Service = Annotated[SummaryService, Depends(get_summary_service)]


@router.get(
    "/{document_id}/sections", response_model=SectionListOut, operation_id="listDocumentSections"
)
async def list_sections(
    document_id: uuid.UUID, user: CurrentUser, service: Service
) -> SectionListOut:
    """Chapters (or page-range parts) with their summaries when already made."""
    return await service.sections(user.id, document_id)


@router.post(
    "/{document_id}/sections/{section_id}/summary",
    response_model=SummaryOut,
    status_code=status.HTTP_201_CREATED,
    operation_id="summarizeSection",
)
async def summarize_section(
    document_id: uuid.UUID,
    section_id: uuid.UUID,
    response: Response,
    user: CurrentUser,
    service: Service,
) -> SummaryOut:
    """201 when made now (uses the summary quota); 200 when it already existed."""
    summary, created = await service.summarize(user.id, document_id, section_id)
    if not created:
        response.status_code = status.HTTP_200_OK
    return summary
