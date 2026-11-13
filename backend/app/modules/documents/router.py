"""Router for documents (contract tag `documents`)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import FileTooLargeError
from app.db.session import get_db
from app.integrations.object_storage import ObjectStorage, get_storage
from app.modules.auth.dependencies import get_current_user
from app.modules.documents.queue import JobQueue, get_job_queue
from app.modules.documents.schemas import DocumentListOut, DocumentOut
from app.modules.documents.service import DocumentService
from app.modules.users.models import User

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db)]
Queue = Annotated[JobQueue, Depends(get_job_queue)]
Storage = Annotated[ObjectStorage, Depends(get_storage)]


@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="uploadDocument",
)
async def upload_document(
    response: Response,
    user: CurrentUser,
    db: Db,
    queue: Queue,
    storage: Storage,
    file: Annotated[UploadFile, File()],
    idempotency_key: Annotated[uuid.UUID, Header(alias="Idempotency-Key")],
    space_id: Annotated[uuid.UUID | None, Form()] = None,
) -> DocumentOut:
    limit = settings.max_file_size_bytes
    data = await file.read(limit + 1)  # never buffer more than the limit
    if len(data) > limit:
        raise FileTooLargeError(settings.MAX_FILE_SIZE_MB)
    document, created = await DocumentService(db, storage, queue).upload(
        user=user,
        data=data,
        filename=file.filename,
        space_id=space_id,
        idempotency_key=idempotency_key,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return DocumentOut.model_validate(document)


@router.get("", response_model=DocumentListOut, operation_id="listDocuments")
async def list_documents(
    user: CurrentUser,
    db: Db,
    queue: Queue,
    storage: Storage,
    space_id: Annotated[uuid.UUID, Query()],
) -> DocumentListOut:
    service = DocumentService(db, storage, queue)
    documents = await service.list_in_space(user.id, space_id)
    return DocumentListOut(
        items=[DocumentOut.model_validate(d) for d in documents],
        total_documents=await service.count_for_owner(user.id),
        max_documents=settings.MAX_DOCUMENTS_PER_USER,
    )


@router.get("/{document_id}", response_model=DocumentOut, operation_id="getDocument")
async def get_document(
    document_id: uuid.UUID, user: CurrentUser, db: Db, queue: Queue, storage: Storage
) -> DocumentOut:
    service = DocumentService(db, storage, queue)
    return DocumentOut.model_validate(await service.get(user.id, document_id))
