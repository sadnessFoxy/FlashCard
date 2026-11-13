"""
Forgotten password (U3). The request step always looks the same from outside, whether or
not the email exists, so it cannot be used to find accounts.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidCodeError, WeakPasswordError
from app.core.logging import get_logger
from app.core.rate_limit import RateLimiter, limit_key, rate_limiter
from app.core.security import hash_password
from app.integrations.email import Mailer, send_quietly
from app.modules.auth.codes import OneTimeCodes
from app.modules.auth.email_templates import account_email
from app.modules.auth.password_policy import check_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.verification import mark_email_verified
from app.modules.users.service import UserService

logger = get_logger(__name__)
PURPOSE = "reset_password"
HOUR = 60 * 60


class PasswordReset:
    def __init__(
        self, session: AsyncSession, mailer: Mailer, limiter: RateLimiter = rate_limiter
    ) -> None:
        self._session = session
        self._codes = OneTimeCodes(session)
        self._users = UserService(session)
        self._mailer = mailer
        self._limiter = limiter

    async def request(self, email: str, client_ip: str) -> None:
        """Send a code if the account exists; silently do nothing when limited or unknown."""
        if await self._limited(email, client_ip):
            return
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return
        if user.password_hash is None:  # Google-only account: point to Google sign-in
            message = account_email("google_only", email, user.locale)
            await send_quietly(self._mailer, message, PURPOSE)
            return
        code = await self._codes.issue(user.id, PURPOSE)
        await send_quietly(self._mailer, account_email("reset", email, user.locale, code), PURPOSE)
        logger.info("Password reset code sent (user_id=%s)", user.id)

    async def reset(self, email: str, code: str, new_password: str) -> None:
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active or user.password_hash is None:
            raise InvalidCodeError()
        problem = check_password(new_password, email)
        if problem is not None:
            raise WeakPasswordError(problem)
        if not await self._codes.consume(user.id, PURPOSE, code):
            await self._session.commit()  # keep the counted attempt even though we fail
            raise InvalidCodeError()

        await self._users.update_password_hash(user, hash_password(new_password))
        await AuthRepository(self._session).revoke_all_for_user(user.id, datetime.now(UTC))
        mark_email_verified(user)  # the code proved the user reads this mailbox
        message = account_email("password_changed", email, user.locale)
        await send_quietly(self._mailer, message, PURPOSE)
        logger.info("Password reset (user_id=%s)", user.id)

    async def _limited(self, email: str, client_ip: str) -> bool:
        checks = (
            (limit_key("reset-email", email), settings.PASSWORD_RESET_MAX_PER_EMAIL_PER_HOUR),
            (limit_key("reset-ip", client_ip), settings.PASSWORD_RESET_MAX_PER_IP_PER_HOUR),
        )
        for key, limit in checks:
            if (await self._limiter.hit_and_check(key, limit, HOUR)).blocked:
                return True
        return False
