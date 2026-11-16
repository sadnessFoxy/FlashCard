"""Router for the admin console (/v1/admin), contract tag `admin`. Admin role required (R13)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.object_storage import ObjectStorage, get_storage
from app.modules.admin.dependencies import require_admin
from app.modules.admin.schemas import (
    AdminDocumentListOut,
    AdminDocumentOut,
    AdminUserListOut,
    AdminUserOut,
    AuditListOut,
    BlockUserRequest,
    OverviewOut,
    QuotaOverrideRequest,
    SettingsOut,
    SettingsPatch,
)
from app.modules.admin.service import AdminService
from app.modules.documents.queue import JobQueue, get_job_queue
from app.modules.users.models import User

Db = Annotated[AsyncSession, Depends(get_db, scope="function")]
Admin = Annotated[User, Depends(require_admin)]
Queue = Annotated[JobQueue, Depends(get_job_queue)]
Storage = Annotated[ObjectStorage, Depends(get_storage)]

router = APIRouter()


def get_admin_service(db: Db, admin: Admin) -> AdminService:
    return AdminService(db, admin)


Service = Annotated[AdminService, Depends(get_admin_service)]


@router.get("/overview", response_model=OverviewOut, operation_id="adminOverview")
async def overview(service: Service) -> OverviewOut:
    return await service.overview()


# ---------- users ----------


@router.get("/users", response_model=AdminUserListOut, operation_id="adminListUsers")
async def list_users(
    service: Service,
    q: Annotated[str | None, Query(max_length=254)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUserListOut:
    items, total = await service.list_users(q, limit, offset)
    return AdminUserListOut(items=items, total=total)


@router.get("/users/{user_id}", response_model=AdminUserOut, operation_id="adminGetUser")
async def get_user(user_id: uuid.UUID, service: Service) -> AdminUserOut:
    return await service.user(user_id)


@router.post("/users/{user_id}/block", response_model=AdminUserOut, operation_id="adminBlockUser")
async def block_user(user_id: uuid.UUID, body: BlockUserRequest, service: Service) -> AdminUserOut:
    return await service.block(user_id, body.reason)


@router.post(
    "/users/{user_id}/unblock", response_model=AdminUserOut, operation_id="adminUnblockUser"
)
async def unblock_user(user_id: uuid.UUID, service: Service) -> AdminUserOut:
    return await service.unblock(user_id)


@router.post(
    "/users/{user_id}/sign-out",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="adminSignOutUser",
)
async def sign_out_user(user_id: uuid.UUID, service: Service) -> Response:
    await service.sign_out(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/users/{user_id}/quota", response_model=AdminUserOut, operation_id="adminSetUserQuota")
async def set_quota(
    user_id: uuid.UUID, body: QuotaOverrideRequest, service: Service
) -> AdminUserOut:
    return await service.set_quota(user_id, body.daily_limit, body.expires_at)


@router.post(
    "/users/{user_id}/deletion",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="adminDeleteUser",
)
async def delete_user(
    user_id: uuid.UUID, body: BlockUserRequest, service: Service, queue: Queue
) -> Response:
    """For a deletion request received by support; `reason` records the request."""
    await service.delete_user(user_id, queue, body.reason)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- documents and jobs ----------


@router.get("/documents", response_model=AdminDocumentListOut, operation_id="adminListDocuments")
async def list_documents(
    service: Service,
    status_filter: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> AdminDocumentListOut:
    return AdminDocumentListOut(items=await service.documents(status_filter, limit))


@router.post(
    "/documents/{document_id}/retry",
    response_model=AdminDocumentOut,
    operation_id="adminRetryDocument",
)
async def retry_document(
    document_id: uuid.UUID, service: Service, storage: Storage, queue: Queue
) -> AdminDocumentOut:
    return await service.retry_document(document_id, storage, queue)


# ---------- settings and audit ----------


@router.get("/settings", response_model=SettingsOut, operation_id="adminGetSettings")
async def get_settings(service: Service) -> SettingsOut:
    return await service.settings()


@router.patch("/settings", response_model=SettingsOut, operation_id="adminUpdateSettings")
async def update_settings(body: SettingsPatch, service: Service) -> SettingsOut:
    return await service.update_settings(body.values)


@router.get("/audit", response_model=AuditListOut, operation_id="adminListAudit")
async def list_audit(
    service: Service,
    action: Annotated[str | None, Query(max_length=64)] = None,
    actor_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> AuditListOut:
    return AuditListOut(items=await service.audit(action, actor_id, limit))
