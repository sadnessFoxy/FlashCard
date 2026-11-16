"""Read-side queries for the admin console: counts and metadata, never content (R13)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import AdminAuditLog, UserQuotaOverride
from app.modules.auth.models import AuthIdentity, RefreshToken
from app.modules.documents.models import Document, DocumentJob
from app.modules.usage.models import AiUsage
from app.modules.users.models import User


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- overview ----------

    async def count_users(self) -> int:
        return int(await self._session.scalar(select(func.count()).select_from(User)) or 0)

    async def active_users_since(self, since: datetime) -> int:
        """Users who signed in or refreshed a session since then (sessions rotate often)."""
        stmt = select(func.count(func.distinct(RefreshToken.user_id))).where(
            RefreshToken.created_at >= since
        )
        return int(await self._session.scalar(stmt) or 0)

    async def documents_by_status(self) -> dict[str, int]:
        rows = await self._session.execute(
            select(Document.status, func.count()).group_by(Document.status)
        )
        return {status: int(n) for status, n in rows.all()}

    async def ai_usage_since(self, since: datetime) -> tuple[int, int, int, int]:
        """(chat answers, all calls, failed calls, tokens) since then."""
        row = (
            await self._session.execute(
                select(
                    func.count().filter(AiUsage.operation == "chat", AiUsage.success.is_(True)),
                    func.count(),
                    func.count().filter(AiUsage.success.is_(False)),
                    func.coalesce(func.sum(AiUsage.input_tokens + AiUsage.output_tokens), 0),
                ).where(AiUsage.created_at >= since)
            )
        ).one()
        return int(row[0]), int(row[1]), int(row[2]), int(row[3])

    # ---------- users ----------

    def _user_filter(self, stmt: Select, query: str | None) -> Select:  # type: ignore[type-arg]
        if query:
            stmt = stmt.where(User.email.ilike(f"%{query.strip().lower()}%"))
        return stmt

    async def list_users(
        self, query: str | None, limit: int, offset: int
    ) -> tuple[list[User], int]:
        total = await self._session.scalar(
            self._user_filter(select(func.count()).select_from(User), query)
        )
        rows = await self._session.execute(
            self._user_filter(select(User), query)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars()), int(total or 0)

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def sign_in_methods(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[str]]:
        rows = await self._session.execute(
            select(AuthIdentity.user_id, AuthIdentity.provider).where(
                AuthIdentity.user_id.in_(user_ids)
            )
        )
        methods: dict[uuid.UUID, list[str]] = {}
        for user_id, provider in rows.all():
            methods.setdefault(user_id, []).append(provider)
        return methods

    async def document_counts(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        rows = await self._session.execute(
            select(Document.owner_id, func.count())
            .where(Document.owner_id.in_(user_ids))
            .group_by(Document.owner_id)
        )
        return {owner: int(n) for owner, n in rows.all()}

    async def quota_overrides(
        self, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, UserQuotaOverride]:
        rows = await self._session.execute(
            select(UserQuotaOverride).where(UserQuotaOverride.user_id.in_(user_ids))
        )
        return {o.user_id: o for o in rows.scalars()}

    async def quota_override(self, user_id: uuid.UUID) -> UserQuotaOverride | None:
        return (await self.quota_overrides([user_id])).get(user_id)

    # ---------- documents ----------

    async def list_documents(self, status: str | None, limit: int) -> list[tuple[Document, str]]:
        stmt = select(Document, User.email).join(User, User.id == Document.owner_id)
        if status:
            stmt = stmt.where(Document.status == status)
        rows = await self._session.execute(stmt.order_by(Document.updated_at.desc()).limit(limit))
        return [(doc, email) for doc, email in rows.all()]

    async def latest_jobs(self, document_ids: list[uuid.UUID]) -> dict[uuid.UUID, DocumentJob]:
        if not document_ids:
            return {}
        rows = await self._session.execute(
            select(DocumentJob)
            .where(DocumentJob.document_id.in_(document_ids))
            .distinct(DocumentJob.document_id)
            .order_by(DocumentJob.document_id, DocumentJob.created_at.desc())
        )
        return {job.document_id: job for job in rows.scalars()}

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        return await self._session.get(Document, document_id)

    # ---------- audit ----------

    async def audit_entries(
        self, action: str | None, actor_id: uuid.UUID | None, limit: int
    ) -> list[AdminAuditLog]:
        stmt = select(AdminAuditLog)
        if action:
            stmt = stmt.where(AdminAuditLog.action == action)
        if actor_id:
            stmt = stmt.where(AdminAuditLog.actor_id == actor_id)
        rows = await self._session.execute(
            stmt.order_by(AdminAuditLog.created_at.desc()).limit(limit)
        )
        return list(rows.scalars())

    async def add(self, obj: object) -> None:
        self._session.add(obj)
        await self._session.flush()
