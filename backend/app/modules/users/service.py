"""User operations; other modules call this instead of reading `users` directly."""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserConsent
from app.modules.users.repository import UserRepository


class EmailAlreadyUsedError(Exception):
    """The normalized email already belongs to an account."""


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self._repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._repo.get_by_email(email)

    async def create(self, *, email: str, password_hash: str | None, locale: str) -> User:
        """Create a user (normalized email); the unique index stops concurrent duplicates."""
        user = User(email=email, password_hash=password_hash, locale=locale)
        try:
            async with self._session.begin_nested():
                return await self._repo.add(user)
        except IntegrityError as exc:
            raise EmailAlreadyUsedError from exc

    async def update_password_hash(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self._session.flush()

    async def consents(self, user_id: uuid.UUID) -> list[UserConsent]:
        return await self._repo.consents(user_id)

    async def has_consent(self, user_id: uuid.UUID, kind: str, version: str) -> bool:
        return await self._repo.get_consent(user_id, kind, version) is not None

    async def give_consent(
        self, user_id: uuid.UUID, kind: str, version: str
    ) -> tuple[UserConsent, bool]:
        """(consent, created). Idempotent: an existing consent is returned as is."""
        existing = await self._repo.get_consent(user_id, kind, version)
        if existing is not None:
            return existing, False
        try:
            async with self._session.begin_nested():
                consent = await self._repo.add_consent(
                    UserConsent(user_id=user_id, kind=kind, version=version)
                )
            return consent, True
        except IntegrityError:
            found = await self._repo.get_consent(user_id, kind, version)
            assert found is not None
            return found, False
