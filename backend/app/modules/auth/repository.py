"""Data access for `auth_identities`, `refresh_tokens` and `auth_codes`."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AuthCode, AuthIdentity, RefreshToken


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

    async def revoke_all_for_user(self, user_id: uuid.UUID, now: datetime) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def email_identity(self, user_id: uuid.UUID) -> AuthIdentity | None:
        result = await self._session.execute(
            select(AuthIdentity).where(
                AuthIdentity.user_id == user_id, AuthIdentity.provider == "email"
            )
        )
        return result.scalar_one_or_none()

    # ---------- one-time codes ----------

    async def add_code(self, code: AuthCode) -> None:
        self._session.add(code)
        await self._session.flush()

    async def live_code_for_update(
        self, user_id: uuid.UUID, purpose: str, now: datetime
    ) -> AuthCode | None:
        """The newest unused, unexpired code; locked so parallel guesses count one by one."""
        result = await self._session.execute(
            select(AuthCode)
            .where(
                AuthCode.user_id == user_id,
                AuthCode.purpose == purpose,
                AuthCode.used_at.is_(None),
                AuthCode.expires_at > now,
            )
            .order_by(AuthCode.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def retire_codes(self, user_id: uuid.UUID, purpose: str, now: datetime) -> None:
        """Older codes stop working once a new one is sent (or one is used)."""
        await self._session.execute(
            update(AuthCode)
            .where(
                AuthCode.user_id == user_id,
                AuthCode.purpose == purpose,
                AuthCode.used_at.is_(None),
            )
            .values(used_at=now)
        )
