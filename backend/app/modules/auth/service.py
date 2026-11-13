"""
Email + password authentication (docs/specs/f2-email-auth.md).

Logs carry user_id only, never email, password or token (R10).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountBlockedError,
    EmailUnavailableError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    TooManyAttemptsError,
    WeakPasswordError,
)
from app.core.logging import get_logger
from app.core.rate_limit import RateLimiter, limit_key, rate_limiter
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.modules.auth.email import normalize_email
from app.modules.auth.models import AuthIdentity, RefreshToken
from app.modules.auth.password_policy import check_password
from app.modules.auth.reauth import PasswordConfirmation
from app.modules.auth.repository import AuthRepository
from app.modules.users.models import User
from app.modules.users.service import EmailAlreadyUsedError, UserService

logger = get_logger(__name__)


@dataclass(frozen=True)
class IssuedSession:
    user: User
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime


@dataclass(frozen=True)
class ClientInfo:
    ip: str
    user_agent: str | None


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuthService:
    def __init__(self, session: AsyncSession, limiter: RateLimiter = rate_limiter) -> None:
        self._session = session
        self._repo = AuthRepository(session)
        self._users = UserService(session)
        self._limiter = limiter

    # ------------------------------------------------------------------ register

    async def register(
        self, *, email: str, password: str, locale: str, client: ClientInfo
    ) -> IssuedSession:
        """`email` is already normalized and validated by the schema."""
        status = await self._limiter.hit_and_check(
            limit_key("register-ip", client.ip),
            settings.REGISTER_MAX_PER_IP,
            settings.REGISTER_WINDOW_SECONDS,
        )
        if status.blocked:
            raise TooManyAttemptsError(status.retry_after_seconds)

        problem = check_password(password, email)
        if problem is not None:
            raise WeakPasswordError(problem)

        if await self._users.get_by_email(email) is not None:
            raise EmailUnavailableError()

        try:
            user = await self._users.create(
                email=email, password_hash=hash_password(password), locale=locale
            )
        except EmailAlreadyUsedError:
            raise EmailUnavailableError() from None

        await self._repo.add_identity(
            AuthIdentity(
                user_id=user.id,
                provider="email",
                provider_subject=email,
                email=email,
                email_verified=False,
            )
        )
        logger.info("User registered (user_id=%s)", user.id)
        return await self._start_session(user, client)

    # --------------------------------------------------------------------- login

    async def login(self, *, email: str, password: str, client: ClientInfo) -> IssuedSession:
        normalized = normalize_email(email)
        email_key = limit_key("login-fail-email", normalized)
        ip_key = limit_key("login-fail-ip", client.ip)

        # Check before verifying: once blocked, even the right password is refused.
        for key, limit in (
            (email_key, settings.LOGIN_MAX_FAILURES_PER_EMAIL),
            (ip_key, settings.LOGIN_MAX_FAILURES_PER_IP),
        ):
            status = await self._limiter.check(key, limit)
            if status.blocked:
                raise TooManyAttemptsError(status.retry_after_seconds)

        user = await self._users.get_by_email(normalized)
        # Always run argon2, even for unknown emails, so timing reveals nothing.
        password_ok = verify_password(password, user.password_hash if user else None)

        if user is None or not password_ok or user.deleted_at is not None:
            window = settings.LOGIN_FAILURE_WINDOW_SECONDS
            await self._limiter.hit(email_key, window)
            await self._limiter.hit(ip_key, window)
            raise InvalidCredentialsError()

        await self._limiter.reset(email_key)
        if user.status != "active":
            # Reveal the block only to someone who knows the password.
            raise AccountBlockedError()

        if user.password_hash and password_needs_rehash(user.password_hash):
            await self._users.update_password_hash(user, hash_password(password))

        logger.info("User signed in (user_id=%s)", user.id)
        return await self._start_session(user, client)

    # ----------------------------------------------------------- change password

    async def change_password(
        self, *, user: User, current_password: str, new_password: str, client: ClientInfo
    ) -> IssuedSession:
        """Signs out every session, then starts a fresh one for this device."""
        await PasswordConfirmation(self._limiter).confirm(user, current_password)
        problem = check_password(new_password, user.email)
        if problem is not None:
            raise WeakPasswordError(problem)
        await self._users.update_password_hash(user, hash_password(new_password))
        await self._repo.revoke_all_for_user(user.id, _utcnow())
        logger.info("Password changed (user_id=%s)", user.id)
        return await self._start_session(user, client)

    # ------------------------------------------------------------------- refresh

    async def refresh(self, *, refresh_token: str, client: ClientInfo) -> IssuedSession:
        now = _utcnow()
        current = await self._repo.get_refresh_token_for_update(hash_token(refresh_token))
        if current is None:
            raise InvalidRefreshTokenError()

        if current.revoked_at is not None:
            await self._handle_reuse(current, now)
            raise InvalidRefreshTokenError()

        session_deadline = current.session_started_at + timedelta(
            days=settings.SESSION_MAX_LIFETIME_DAYS
        )
        if current.expires_at <= now or session_deadline <= now:
            raise InvalidRefreshTokenError()

        user = await self._users.get(current.user_id)
        if user is None or user.deleted_at is not None:
            raise InvalidRefreshTokenError()
        if user.status != "active":
            await self._revoke_family_and_commit(current.family_id, now)
            raise AccountBlockedError()

        issued, new_row = await self._issue(
            user,
            client,
            family_id=current.family_id,
            session_started_at=current.session_started_at,
            now=now,
        )
        current.revoked_at = now
        current.replaced_by_id = new_row.id
        await self._session.flush()
        return issued

    # -------------------------------------------------------------------- logout

    async def logout(self, *, refresh_token: str | None) -> None:
        """Revoke this device's session family; unknown or missing tokens are ignored."""
        if not refresh_token:
            return
        current = await self._repo.get_refresh_token_for_update(hash_token(refresh_token))
        if current is not None:
            await self._repo.revoke_family(current.family_id, _utcnow())
            logger.info("User signed out (user_id=%s)", current.user_id)

    # ------------------------------------------------------------------- helpers

    async def _handle_reuse(self, token: RefreshToken, now: datetime) -> None:
        """A rotated token came back. Within the grace window (e.g. two tabs refreshing at once)
        just reject it; after that assume theft and revoke the family."""
        if token.replaced_by_id is None:
            return  # revoked by logout or block, not rotation
        grace = timedelta(seconds=settings.REFRESH_REUSE_GRACE_SECONDS)
        if token.revoked_at is not None and now - token.revoked_at <= grace:
            return
        logger.warning("Refresh token reuse detected, revoking session (user_id=%s)", token.user_id)
        await self._revoke_family_and_commit(token.family_id, now)

    async def _revoke_family_and_commit(self, family_id: uuid.UUID, now: datetime) -> None:
        # Commit now: the request ends with an error, which rolls the session back.
        await self._repo.revoke_family(family_id, now)
        await self._session.commit()

    async def _start_session(self, user: User, client: ClientInfo) -> IssuedSession:
        now = _utcnow()
        issued, _ = await self._issue(
            user, client, family_id=uuid.uuid4(), session_started_at=now, now=now
        )
        return issued

    async def _issue(
        self,
        user: User,
        client: ClientInfo,
        *,
        family_id: uuid.UUID,
        session_started_at: datetime,
        now: datetime,
    ) -> tuple[IssuedSession, RefreshToken]:
        raw = generate_opaque_token()
        expires_at = min(
            now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            session_started_at + timedelta(days=settings.SESSION_MAX_LIFETIME_DAYS),
        )
        row = await self._repo.add_refresh_token(
            RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                family_id=family_id,
                token_hash=hash_token(raw),
                session_started_at=session_started_at,
                expires_at=expires_at,
                user_agent=(client.user_agent or None) and client.user_agent[:200],
            )
        )
        issued = IssuedSession(
            user=user,
            access_token=create_access_token(user.id, now),
            refresh_token=raw,
            refresh_expires_at=expires_at,
        )
        return issued, row
