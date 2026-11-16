"""
Verify Google ID tokens on the server (R15): signature against Google's published keys,
audience (one of our OAuth client IDs), issuer and expiry. Nothing the app sends about
the user is trusted; only what the verified token says.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import settings
from app.core.exceptions import GoogleNotConfiguredError, InvalidGoogleTokenError

ISSUERS = ("accounts.google.com", "https://accounts.google.com")
# Resolve the signing key of a token (Google's JWKS in production, a fixed key in tests).
KeyResolver = Callable[[str], Any]


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str  # the stable Google account id ("sub")
    email: str
    email_verified: bool


class GoogleTokenVerifier:
    def __init__(self, client_ids: list[str], key_for: KeyResolver) -> None:
        self._client_ids = client_ids
        self._key_for = key_for

    async def verify(self, id_token: str) -> GoogleIdentity:
        # Key download and RSA checks are blocking: keep them off the event loop.
        return await asyncio.to_thread(self._verify_sync, id_token)

    def _verify_sync(self, id_token: str) -> GoogleIdentity:
        try:
            claims = jwt.decode(
                id_token,
                self._key_for(id_token),
                algorithms=["RS256"],
                audience=self._client_ids,
                issuer=list(ISSUERS),
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
            )
        except (jwt.PyJWTError, ValueError) as exc:
            raise InvalidGoogleTokenError() from exc
        email = claims.get("email")
        if not isinstance(email, str) or not email:
            raise InvalidGoogleTokenError()
        return GoogleIdentity(
            subject=str(claims["sub"]),
            email=email,
            email_verified=claims.get("email_verified") is True,
        )


_jwks: PyJWKClient | None = None


def _google_keys(id_token: str) -> Any:
    global _jwks
    if _jwks is None:
        _jwks = PyJWKClient(settings.GOOGLE_JWKS_URL, cache_keys=True)
    return _jwks.get_signing_key_from_jwt(id_token).key


def get_google_verifier() -> GoogleTokenVerifier:
    if not settings.GOOGLE_CLIENT_IDS:
        raise GoogleNotConfiguredError()
    return GoogleTokenVerifier(settings.GOOGLE_CLIENT_IDS, _google_keys)
