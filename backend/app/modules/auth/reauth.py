"""
Re-confirm the password of a signed-in user before sensitive actions (change password,
delete account). Wrong passwords are rate limited like sign-in, so a stolen session cannot
be used to guess the password.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import InvalidPasswordError, NoPasswordError, TooManyAttemptsError
from app.core.rate_limit import RateLimiter, limit_key, rate_limiter
from app.core.security import verify_password
from app.modules.users.models import User


class PasswordConfirmation:
    def __init__(self, limiter: RateLimiter = rate_limiter) -> None:
        self._limiter = limiter

    async def confirm(self, user: User, password: str) -> None:
        if user.password_hash is None:
            raise NoPasswordError()
        key = limit_key("reauth-fail", str(user.id))
        status = await self._limiter.check(key, settings.LOGIN_MAX_FAILURES_PER_EMAIL)
        if status.blocked:
            raise TooManyAttemptsError(status.retry_after_seconds)
        if not verify_password(password, user.password_hash):
            await self._limiter.hit(key, settings.LOGIN_FAILURE_WINDOW_SECONDS)
            raise InvalidPasswordError()
        await self._limiter.reset(key)
