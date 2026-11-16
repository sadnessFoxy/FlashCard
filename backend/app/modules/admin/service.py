"""
Admin console (A2-A7). Every change is written to the audit log in the same transaction,
so there is no change without a record. Admins see metadata only, never content (R13).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CannotTargetSelfError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.object_storage import ObjectStorage
from app.modules.admin.models import AdminAuditLog, AppSetting, UserQuotaOverride
from app.modules.admin.repository import AdminRepository
from app.modules.admin.runtime_config import SPECS, runtime_config
from app.modules.admin.schemas import (
    AdminDocumentOut,
    AdminJobOut,
    AdminUserOut,
    AuditEntryOut,
    OverviewOut,
    QuotaOverrideOut,
    SettingsOut,
)
from app.modules.auth.repository import AuthRepository
from app.modules.documents.models import Document, DocumentJob
from app.modules.documents.queue import JobQueue
from app.modules.documents.service import DocumentService
from app.modules.usage.quota import QuestionQuota, today_started_at
from app.modules.users.account_deletion import AccountDeletion
from app.modules.users.models import User

logger = get_logger(__name__)

ARQ_QUEUE_KEY = "arq:queue"


class AdminService:
    def __init__(self, session: AsyncSession, actor: User) -> None:
        self._session = session
        self._repo = AdminRepository(session)
        self._actor = actor

    # ---------- A2 overview ----------

    async def overview(self) -> OverviewOut:
        since = today_started_at()
        questions, calls, failures, tokens = await self._repo.ai_usage_since(since)
        config = await runtime_config.values()
        budget = int(config["ai_daily_token_budget"])
        return OverviewOut(
            users_total=await self._repo.count_users(),
            users_active_today=await self._repo.active_users_since(since),
            documents_by_status=await self._repo.documents_by_status(),
            questions_today=questions,
            ai_calls_today=calls,
            ai_failures_today=failures,
            ai_tokens_today=tokens,
            ai_daily_token_budget=budget,
            ai_budget_used_percent=round(100 * tokens / budget, 1) if budget else None,
            ai_enabled=bool(config["ai_enabled"]),
            circuit_state=get_gateway().breaker.state.value,  # this API process
            queue_length=int(await get_redis().zcard(ARQ_QUEUE_KEY)),
        )

    # ---------- A3 users ----------

    async def list_users(
        self, query: str | None, limit: int, offset: int
    ) -> tuple[list[AdminUserOut], int]:
        users, total = await self._repo.list_users(query, limit, offset)
        return await self._users_out(users), total

    async def user(self, user_id: uuid.UUID) -> AdminUserOut:
        return (await self._users_out([await self._require_user(user_id)]))[0]

    async def block(self, user_id: uuid.UUID, reason: str) -> AdminUserOut:
        user = await self._require_other_user(user_id)
        before = user.status
        user.status = "blocked"
        await AuthRepository(self._session).revoke_all_for_user(user.id, datetime.now(UTC))
        await self._audit(
            "user.block", "user", user.id, {"status": before}, {"status": "blocked"}, reason
        )
        return await self.user(user.id)

    async def unblock(self, user_id: uuid.UUID) -> AdminUserOut:
        user = await self._require_user(user_id)
        before = user.status
        user.status = "active"
        await self._audit("user.unblock", "user", user.id, {"status": before}, {"status": "active"})
        return await self.user(user.id)

    async def sign_out(self, user_id: uuid.UUID) -> None:
        user = await self._require_other_user(user_id)
        await AuthRepository(self._session).revoke_all_for_user(user.id, datetime.now(UTC))
        await self._audit("user.sign_out", "user", user.id, None, None)

    async def set_quota(
        self, user_id: uuid.UUID, daily_limit: int | None, expires_at: datetime | None
    ) -> AdminUserOut:
        user = await self._require_user(user_id)
        current = await self._repo.quota_override(user.id)
        before = _override_dict(current)
        if daily_limit is None:
            await self._session.execute(
                delete(UserQuotaOverride).where(UserQuotaOverride.user_id == user.id)
            )
        elif current is None:
            await self._repo.add(
                UserQuotaOverride(user_id=user.id, daily_limit=daily_limit, expires_at=expires_at)
            )
        else:
            current.daily_limit, current.expires_at = daily_limit, expires_at
        after = (
            None
            if daily_limit is None
            else {"daily_limit": daily_limit, "expires_at": _iso(expires_at)}
        )
        await self._audit("user.quota", "user", user.id, before, after)
        return await self.user(user.id)

    async def delete_user(self, user_id: uuid.UUID, queue: JobQueue, reason: str) -> None:
        """Runs U9 for a user who asked support to delete their account."""
        user = await self._require_other_user(user_id)
        await self._audit("user.delete", "user", user.id, {"email": user.email}, None, reason)
        await AccountDeletion(self._session, queue).erase(user)  # commits with the audit row

    # ---------- A4 documents and jobs ----------

    async def documents(self, status: str | None, limit: int) -> list[AdminDocumentOut]:
        rows = await self._repo.list_documents(status, limit)
        jobs = await self._repo.latest_jobs([doc.id for doc, _ in rows])
        return [_document_out(doc, email, jobs.get(doc.id)) for doc, email in rows]

    async def retry_document(
        self, document_id: uuid.UUID, storage: ObjectStorage, queue: JobQueue
    ) -> AdminDocumentOut:
        document = await self._repo.get_document(document_id)
        if document is None:
            raise NotFoundError("Document")
        before = document.status
        retried = await DocumentService(self._session, storage, queue).retry(
            document.owner_id, document.id
        )
        await self._audit(
            "document.retry",
            "document",
            document.id,
            {"status": before},
            {"status": retried.status},
        )
        await self._session.commit()
        owner = await self._repo.get_user(retried.owner_id)
        jobs = await self._repo.latest_jobs([retried.id])
        return _document_out(retried, owner.email if owner else "", jobs.get(retried.id))

    # ---------- A5 settings ----------

    async def settings(self) -> SettingsOut:
        return SettingsOut(
            values=await runtime_config.values(),
            defaults={key: spec.default() for key, spec in SPECS.items()},
        )

    async def update_settings(self, changes: dict[str, Any]) -> SettingsOut:
        clean = self._validated(changes)
        current = await runtime_config.values()
        for key, value in clean.items():
            row = await self._session.scalar(select(AppSetting).where(AppSetting.key == key))
            if row is None:
                await self._repo.add(AppSetting(key=key, value=value))
            else:
                row.value = value
            await self._audit(
                "settings.update", "setting", key, {"value": current[key]}, {"value": value}
            )
        await self._session.commit()
        runtime_config.invalidate()  # other processes follow within the cache time
        return await self.settings()

    @staticmethod
    def _validated(changes: dict[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        errors: list[dict[str, str]] = []
        for key, value in changes.items():
            spec = SPECS.get(key)
            if spec is None:
                errors.append({"field": key, "type": "unknown_setting"})
                continue
            try:
                clean[key] = spec.validate(value)
            except ValueError:
                errors.append({"field": key, "type": "invalid_value"})
        if errors:
            raise ValidationError("Invalid settings", {"errors": errors})
        return clean

    # ---------- A7 audit log ----------

    async def audit(
        self, action: str | None, actor_id: uuid.UUID | None, limit: int
    ) -> list[AuditEntryOut]:
        entries = await self._repo.audit_entries(action, actor_id, limit)
        return [
            AuditEntryOut(
                id=e.id,
                actor_email=e.actor_email,
                action=e.action,
                target_type=e.target_type,
                target_id=e.target_id,
                before=e.before,
                after=e.after,
                reason=e.reason,
                created_at=e.created_at,
            )
            for e in entries
        ]

    # ---------- helpers ----------

    async def _audit(
        self,
        action: str,
        target_type: str,
        target_id: uuid.UUID | str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        reason: str | None = None,
    ) -> None:
        await self._repo.add(
            AdminAuditLog(
                actor_id=self._actor.id,
                actor_email=self._actor.email,
                action=action,
                target_type=target_type,
                target_id=str(target_id),
                before=before,
                after=after,
                reason=reason,
            )
        )
        logger.info("Admin action %s on %s (actor_id=%s)", action, target_type, self._actor.id)

    async def _require_user(self, user_id: uuid.UUID) -> User:
        user = await self._repo.get_user(user_id)
        if user is None:
            raise NotFoundError("User")
        return user

    async def _require_other_user(self, user_id: uuid.UUID) -> User:
        if user_id == self._actor.id:
            raise CannotTargetSelfError()
        return await self._require_user(user_id)

    async def _users_out(self, users: list[User]) -> list[AdminUserOut]:
        ids = [u.id for u in users]
        methods = await self._repo.sign_in_methods(ids)
        documents = await self._repo.document_counts(ids)
        overrides = await self._repo.quota_overrides(ids)
        quota = QuestionQuota()
        out = []
        for u in users:
            override = overrides.get(u.id)
            out.append(
                AdminUserOut(
                    id=u.id,
                    email=u.email,
                    role=u.role,  # type: ignore[arg-type]
                    status=u.status,  # type: ignore[arg-type]
                    sign_in_methods=sorted(methods.get(u.id, [])),
                    email_verified=u.email_verified_at is not None,
                    created_at=u.created_at,
                    document_count=documents.get(u.id, 0),
                    questions_today=(await quota.status(u.id)).used_today,
                    quota_override=QuotaOverrideOut(
                        daily_limit=override.daily_limit, expires_at=override.expires_at
                    )
                    if override
                    else None,
                )
            )
        return out


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _override_dict(override: UserQuotaOverride | None) -> dict[str, Any] | None:
    if override is None:
        return None
    return {"daily_limit": override.daily_limit, "expires_at": _iso(override.expires_at)}


def _document_out(
    document: Document, owner_email: str, job: DocumentJob | None
) -> AdminDocumentOut:
    return AdminDocumentOut(
        id=document.id,
        owner_id=document.owner_id,
        owner_email=owner_email,
        filename=document.filename,
        file_kind=document.file_kind,
        text_source=document.text_source,
        page_count=document.page_count,
        status=document.status,
        error_code=document.error_code,
        created_at=document.created_at,
        updated_at=document.updated_at,
        last_job=AdminJobOut(
            status=job.status, attempts=job.attempts, last_error_code=job.last_error_code
        )
        if job
        else None,
    )
