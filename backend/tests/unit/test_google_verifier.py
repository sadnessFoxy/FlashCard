"""F3: Google ID tokens are checked for signature, audience, issuer and expiry (R15)."""

from __future__ import annotations

import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.exceptions import InvalidGoogleTokenError
from app.modules.auth.google import GoogleTokenVerifier

CLIENT = "web-client.apps.googleusercontent.com"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(key: Any = KEY, **overrides: Any) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT,
        "sub": "google-123",
        "email": "Learner@Gmail.com",
        "email_verified": True,
        "iat": now,
        "exp": now + 600,
        **overrides,
    }
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm="RS256")


verifier = GoogleTokenVerifier([CLIENT], lambda _token: KEY.public_key())


async def test_valid_token() -> None:
    identity = await verifier.verify(token())
    assert (identity.subject, identity.email, identity.email_verified) == (
        "google-123",
        "Learner@Gmail.com",
        True,
    )


@pytest.mark.parametrize(
    "bad",
    [
        token(key=OTHER_KEY),  # forged signature
        token(aud="someone-else.apps.googleusercontent.com"),
        token(iss="https://evil.example.com"),
        token(exp=int(time.time()) - 10),
        token(email=None),
        "not-a-jwt",
    ],
)
async def test_rejected_tokens(bad: str) -> None:
    with pytest.raises(InvalidGoogleTokenError):
        await verifier.verify(bad)


async def test_unverified_email_is_reported() -> None:
    assert (await verifier.verify(token(email_verified=False))).email_verified is False
