"""Upload and read documents (docs/specs/f5-document-upload.md). Logs carry ids only (R10)."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConsentRequiredError,
    DocumentLimitReachedError,
    DocumentNotRetryableError,
    EmailNotVerifiedError,
    FileTooLargeError,
    FileTypeNotSupportedError,
    IdempotencyKeyReusedError,
    NotFoundError,
    PdfEncryptedError,
    SpaceRequiredError,
    TooManyPagesError,
)
from app.core.logging import get_logger
from app.integrations.object_storage import ObjectStorage
from app.modules.documents.filenames import sanitize_filename
from app.modules.documents.formats import CONTENT_TYPES, UnsupportedFileError, inspect_file
from app.modules.documents.models import Document, DocumentJob
from app.modules.documents.queue import JobQueue
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.states import DELETING, FAILED, PAUSED_QUOTA, QUEUED, UPLOADED
from app.modules.spaces.models import Space
from app.modules.spaces.service import SpaceService
from app.modules.users.models import User
from app.modules.users.service import UserService

logger = get_logger(__name__)

AI_CONSENT_KIND = "ai_processing"


def storage_key_for(owner_id: uuid.UUID, document_id: uuid.UUID) -> str:
    return f"documents/{owner_id}/{document_id}.pdf"


class DocumentService:
    def __init__(self, session: AsyncSession, storage: ObjectStorage, queue: JobQueue) -> None:
        self._session = session
        self._repo = DocumentRepository(session)
        self._spaces = SpaceService(session)
        self._users = UserService(session)
        self._storage = storage
        self._queue = queue

    async def upload(
        self,
        *,
        user: User,
        data: bytes,
        filename: str | None,
        space_id: uuid.UUID | None,
        idempotency_key: uuid.UUID,
    ) -> tuple[Document, bool]:
        """(document, created). A replay of the same key and file returns the original."""
        digest = hashlib.sha256(data).hexdigest()
        existing = await self._repo.get_by_idempotency_key(user.id, idempotency_key)
        if existing is not None:
            return self._replay(existing, digest), False

        await self._check_allowed(user)
        if len(data) > settings.max_file_size_bytes:
            raise FileTooLargeError(settings.MAX_FILE_SIZE_MB)
        try:
            info = inspect_file(data)
        except UnsupportedFileError:
            raise FileTypeNotSupportedError("not a PDF or .docx") from None
        if info.encrypted:
            raise PdfEncryptedError()
        if info.page_count > settings.MAX_PAGES:
            raise TooManyPagesError(settings.MAX_PAGES)

        safe_name = sanitize_filename(filename)
        await self._repo.lock_owner(user.id)
        if await self._repo.count_for_owner(user.id) >= settings.MAX_DOCUMENTS_PER_USER:
            raise DocumentLimitReachedError(settings.MAX_DOCUMENTS_PER_USER)
        space = await self._resolve_space(user.id, space_id, safe_name)

        document_id = uuid.uuid4()
        document = Document(
            id=document_id,
            owner_id=user.id,
            space_id=space.id,
            filename=safe_name,
            file_kind=info.kind,
            storage_key=storage_key_for(user.id, document_id),
            size_bytes=len(data),
            page_count=info.page_count,
            sha256=digest,
            status=UPLOADED,
            idempotency_key=idempotency_key,
        )
        try:
            async with self._session.begin_nested():
                await self._repo.add(document)
        except IntegrityError:
            # A concurrent request with the same key won the race.
            raced = await self._repo.get_by_idempotency_key(user.id, idempotency_key)
            if raced is None:
                raise
            return self._replay(raced, digest), False

        await self._storage.upload_file(document.storage_key, data, CONTENT_TYPES[info.kind])
        await self._repo.transition(document.id, QUEUED, sources=[UPLOADED])
        await self._repo.add_job(DocumentJob(document_id=document.id))
        # Commit before enqueueing so the worker can see the row.
        await self._session.commit()
        await self._session.refresh(document)
        await self._queue.enqueue_ingest(document.id)
        logger.info(
            "Document uploaded (document_id=%s, user_id=%s, pages=%d)",
            document.id,
            user.id,
            info.page_count,
        )
        return document, True

    async def list_in_space(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> list[Document]:
        await self._spaces.get(owner_id, space_id)  # 404 for someone else's space
        return await self._repo.list_in_space(owner_id, space_id)

    async def count_for_owner(self, owner_id: uuid.UUID) -> int:
        return await self._repo.count_for_owner(owner_id)

    async def get(self, owner_id: uuid.UUID, document_id: uuid.UUID) -> Document:
        document = await self._repo.get_for_owner(owner_id, document_id)
        if document is None or document.status == "DELETING":
            raise NotFoundError("Document")
        return document

    async def retry(self, owner_id: uuid.UUID, document_id: uuid.UUID) -> Document:
        """FAILED or PAUSED_QUOTA -> QUEUED with a fresh job (chunks already embedded are kept)."""
        document = await self.get(owner_id, document_id)
        if not await self._repo.transition(document.id, QUEUED, sources=[FAILED, PAUSED_QUOTA]):
            raise DocumentNotRetryableError(document.status)
        await self._repo.add_job(DocumentJob(document_id=document.id))
        await self._session.commit()
        await self._session.refresh(document)
        await self._queue.enqueue_ingest(document.id)
        logger.info("Document retry requested (document_id=%s)", document.id)
        return document

    async def delete(self, owner_id: uuid.UUID, document_id: uuid.UUID) -> None:
        """Hide now (DELETING), purge file and rows in the background."""
        document = await self.get(owner_id, document_id)
        if not await self._repo.transition(document.id, DELETING):
            raise NotFoundError("Document")  # deleted concurrently
        await self._session.commit()
        await self._queue.enqueue_purge(document.id, document.storage_key)
        logger.info("Document deletion requested (document_id=%s)", document.id)

    async def move(
        self, owner_id: uuid.UUID, document_id: uuid.UUID, space_id: uuid.UUID
    ) -> Document:
        document = await self.get(owner_id, document_id)
        target = await self._spaces.get(owner_id, space_id)  # 404 for someone else's space
        document.space_id = target.id
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def delete_space(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> None:
        """Delete a space and everything in it: documents go through the purge flow so their
        files are removed; rows are removed with the space (FK cascade)."""
        await self._spaces.get(owner_id, space_id)
        documents = await self._repo.in_space_for_owner(owner_id, space_id)
        for document_id, _key in documents:
            await self._repo.transition(document_id, DELETING)
        await self._spaces.delete(owner_id, space_id)
        await self._session.commit()
        for document_id, key in documents:
            await self._queue.enqueue_purge(document_id, key)

    # -------------------------------------------------------------- helpers

    @staticmethod
    def _replay(existing: Document, digest: str) -> Document:
        if existing.sha256 != digest:
            raise IdempotencyKeyReusedError()
        return existing

    async def _check_allowed(self, user: User) -> None:
        if not await self._users.has_consent(user.id, AI_CONSENT_KIND, settings.AI_CONSENT_VERSION):
            raise ConsentRequiredError(settings.AI_CONSENT_VERSION)
        if settings.REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD and user.email_verified_at is None:
            raise EmailNotVerifiedError()

    async def _resolve_space(
        self, owner_id: uuid.UUID, space_id: uuid.UUID | None, filename: str
    ) -> Space:
        if space_id is not None:
            return await self._spaces.get(owner_id, space_id)
        if await self._spaces.list(owner_id):
            raise SpaceRequiredError()
        return await self._spaces.create_default_for_document(owner_id, filename)
