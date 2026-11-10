"""
Password hashing, access tokens (JWT) and opaque tokens (refresh, one-time).

R3: SECRET_KEY comes from config. R10: never log passwords or tokens.
R15: refresh and one-time tokens are stored hashed only.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"  # noqa: S105 - token type, not a secret

# argon2id; above the OWASP minimum (19 MiB, t=2).
_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)

# Verified against when the user does not exist, so unknown emails take as long
# as wrong passwords (prevents email enumeration by timing).
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    """Hash a password with argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Check a password. A missing hash costs the same time and always fails."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and bool(password_hash)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True when the hash uses outdated parameters."""
    return _hasher.check_needs_rehash(password_hash)


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    expires_at: datetime


class InvalidAccessTokenError(Exception):
    """Bad signature, expired, wrong type or malformed."""


def create_access_token(user_id: uuid.UUID, now: datetime | None = None) -> str:
    """Short-lived JWT carrying only the user id (no email, R10)."""
    issued_at = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> AccessTokenClaims:
    """Verify signature, expiry and token type."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise InvalidAccessTokenError
        return AccessTokenClaims(
            user_id=uuid.UUID(str(payload["sub"])),
            expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=UTC),
        )
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise InvalidAccessTokenError from exc


def access_token_ttl_seconds() -> int:
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def generate_opaque_token() -> str:
    """Random URL-safe token (refresh, one-time). Not a JWT."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 for storage. Tokens carry 384 random bits, so a slow hash is unnecessary."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_one_time_token() -> tuple[str, str]:
    """(token for the user, hash to store), for email verification and password reset."""
    token = generate_opaque_token()
    return token, hash_token(token)
