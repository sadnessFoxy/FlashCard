"""Data access for `users`; only this module touches the table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserConsent


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

    async def consents(self, user_id: uuid.UUID) -> list[UserConsent]:
        result = await self._session.execute(
            select(UserConsent)
            .where(UserConsent.user_id == user_id)
            .order_by(UserConsent.created_at)
        )
        return list(result.scalars())

    async def get_consent(self, user_id: uuid.UUID, kind: str, version: str) -> UserConsent | None:
        result = await self._session.execute(
            select(UserConsent).where(
                UserConsent.user_id == user_id,
                UserConsent.kind == kind,
                UserConsent.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def add_consent(self, consent: UserConsent) -> UserConsent:
        self._session.add(consent)
        await self._session.flush()
        return consent
