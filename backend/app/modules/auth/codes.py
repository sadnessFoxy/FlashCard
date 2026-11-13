"""
Six-digit one-time codes sent by email (R15).

Stored as HMAC-SHA256(SECRET_KEY, purpose:user:code): a leaked database alone cannot be
brute-forced. A code is single use, expires after AUTH_CODE_TTL_MINUTES and dies after
AUTH_CODE_MAX_ATTEMPTS wrong entries. Sending a new code retires the previous ones.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.auth.models import AuthCode
from app.modules.auth.repository import AuthRepository

CODE_DIGITS = 6


def _digest(user_id: uuid.UUID, purpose: str, code: str) -> str:
    message = f"{purpose}:{user_id}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


class OneTimeCodes:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuthRepository(session)

    async def issue(self, user_id: uuid.UUID, purpose: str) -> str:
        now = datetime.now(UTC)
        await self._repo.retire_codes(user_id, purpose, now)
        code = str(secrets.randbelow(10**CODE_DIGITS)).zfill(CODE_DIGITS)
        await self._repo.add_code(
            AuthCode(
                user_id=user_id,
                purpose=purpose,
                code_hash=_digest(user_id, purpose, code),
                expires_at=now + timedelta(minutes=settings.AUTH_CODE_TTL_MINUTES),
            )
        )
        return code

    async def consume(self, user_id: uuid.UUID, purpose: str, code: str) -> bool:
        """True and spent when right; a wrong guess counts against the live code."""
        now = datetime.now(UTC)
        live = await self._repo.live_code_for_update(user_id, purpose, now)
        if live is None:
            return False
        if hmac.compare_digest(live.code_hash, _digest(user_id, purpose, code.strip())):
            live.used_at = now
            return True
        live.attempts += 1
        if live.attempts >= settings.AUTH_CODE_MAX_ATTEMPTS:
            live.used_at = now
        return False
