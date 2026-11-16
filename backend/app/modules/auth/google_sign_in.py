"""
Sign in with Google (U1, docs/specs/f3-google.md).

Account linking rule (DECISIONS): a Google sign-in joins an existing email account only
when Google says the email is verified; otherwise the user must sign in the old way
first, so nobody can take over an account with an unverified Google address.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccountBlockedError, GoogleLinkRequiredError
from app.core.logging import get_logger
from app.modules.auth.email import normalize_email
from app.modules.auth.google import GoogleIdentity, GoogleTokenVerifier
from app.modules.auth.models import AuthIdentity
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService, ClientInfo, IssuedSession
from app.modules.users.models import User
from app.modules.users.service import UserService

logger = get_logger(__name__)
PROVIDER = "google"


class GoogleSignIn:
    def __init__(self, session: AsyncSession, verifier: GoogleTokenVerifier) -> None:
        self._session = session
        self._verifier = verifier
        self._repo = AuthRepository(session)
        self._users = UserService(session)

    async def sign_in(self, id_token: str, locale: str, client: ClientInfo) -> IssuedSession:
        identity = await self._verifier.verify(id_token)
        user = await self._known_user(identity) or await self._link_or_create(identity, locale)
        if not user.is_active:
            raise AccountBlockedError()
        return await AuthService(self._session).start_session(user, client)

    async def _known_user(self, identity: GoogleIdentity) -> User | None:
        linked = await self._repo.identity(PROVIDER, identity.subject)
        return await self._users.get(linked.user_id) if linked else None

    async def _link_or_create(self, identity: GoogleIdentity, locale: str) -> User:
        email = normalize_email(identity.email)
        user = await self._users.get_by_email(email)
        if user is not None and not identity.email_verified:
            raise GoogleLinkRequiredError()
        if user is None:
            user = await self._users.create(email=email, password_hash=None, locale=locale)
            logger.info("User registered with Google (user_id=%s)", user.id)
        else:
            logger.info("Google linked to an existing account (user_id=%s)", user.id)
        if identity.email_verified and user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
        await self._repo.add_identity(
            AuthIdentity(
                user_id=user.id,
                provider=PROVIDER,
                provider_subject=identity.subject,
                email=email,
                email_verified=identity.email_verified,
            )
        )
        return user
