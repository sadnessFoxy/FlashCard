"""Email verification for email-and-password accounts (U2)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidCodeError, TooManyAttemptsError
from app.core.logging import get_logger
from app.core.rate_limit import RateLimiter, limit_key, rate_limiter
from app.integrations.email import Mailer, send_quietly
from app.modules.auth.codes import OneTimeCodes
from app.modules.auth.email_templates import account_email
from app.modules.auth.repository import AuthRepository
from app.modules.users.models import User

logger = get_logger(__name__)
PURPOSE = "verify_email"
HOUR = 60 * 60


class EmailVerification:
    def __init__(
        self, session: AsyncSession, mailer: Mailer, limiter: RateLimiter = rate_limiter
    ) -> None:
        self._session = session
        self._codes = OneTimeCodes(session)
        self._mailer = mailer
        self._limiter = limiter

    async def send(self, user: User) -> None:
        """Email a fresh code; nothing to do for an already verified address."""
        if user.email_verified_at is not None:
            return
        await self._check_rate(user)
        code = await self._codes.issue(user.id, PURPOSE)
        email = account_email("verify", user.email, user.locale, code)
        await send_quietly(self._mailer, email, PURPOSE)
        logger.info("Verification code sent (user_id=%s)", user.id)

    async def confirm(self, user: User, code: str) -> User:
        if user.email_verified_at is not None:
            return user
        if not await self._codes.consume(user.id, PURPOSE, code):
            await self._session.commit()  # keep the counted attempt even though we fail
            raise InvalidCodeError()
        mark_email_verified(user)
        identity = await AuthRepository(self._session).email_identity(user.id)
        if identity is not None:
            identity.email_verified = True
        logger.info("Email verified (user_id=%s)", user.id)
        return user

    async def _check_rate(self, user: User) -> None:
        burst = (
            limit_key("verify-send-burst", str(user.id)),
            1,
            settings.VERIFY_EMAIL_RESEND_SECONDS,
        )
        hourly = (
            limit_key("verify-send-hour", str(user.id)),
            settings.VERIFY_EMAIL_MAX_PER_HOUR,
            HOUR,
        )
        for key, limit, window in (burst, hourly):
            status = await self._limiter.hit_and_check(key, limit, window)
            if status.blocked:
                raise TooManyAttemptsError(status.retry_after_seconds)


def mark_email_verified(user: User) -> None:
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
