"""Data access for `auth_identities` and `refresh_tokens`."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AuthIdentity, RefreshToken


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_identity(self, identity: AuthIdentity) -> None:
        self._session.add(identity)
        await self._session.flush()

    async def add_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_refresh_token_for_update(self, token_hash: str) -> RefreshToken | None:
        """Row lock so two refreshes of one token cannot both rotate it."""
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        )
        return result.scalar_one_or_none()

    async def revoke_family(self, family_id: uuid.UUID, now: datetime) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
