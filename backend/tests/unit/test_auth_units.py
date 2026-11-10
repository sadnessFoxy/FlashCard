"""Unit tests for F2 building blocks (no database)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core import security
from app.core.config import settings
from app.core.rate_limit import RateLimiter, limit_key
from app.modules.auth.email import normalize_email, validate_and_normalize_email
from app.modules.auth.password_policy import check_password

# ------------------------------------------------------------------ email


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  An@Example.COM ", "an@example.com"),
        ("first.last+tag@Gmail.com", "first.last+tag@gmail.com"),
        ("ＡＢＣ@example.com", "abc@example.com"),  # full-width letters (NFKC)
    ],
)
def test_normalize_email(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected


@pytest.mark.parametrize("raw", ["plainaddress", "a@b", "a b@example.com", "@example.com"])
def test_invalid_email_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        validate_and_normalize_email(raw)


# --------------------------------------------------------------- password


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("1234567", "too_short"),
        ("a" * 129, "too_long"),
        ("a" * 128, None),
        ("12345678", "too_common"),
        ("MatKhau123", "too_common"),
        ("an@example.com", "same_as_email"),
        ("An", "too_short"),
        ("    spaces count    ", None),
        ("mật khẩu tiếng việt", None),
    ],
)
def test_password_policy(password: str, expected: str | None) -> None:
    assert check_password(password, "an@example.com") == expected


# ------------------------------------------------------------ access token


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    claims = security.decode_access_token(security.create_access_token(user_id))
    assert claims.user_id == user_id


def test_expired_access_token_rejected() -> None:
    old = datetime.now(UTC) - timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)
    token = security.create_access_token(uuid.uuid4(), now=old)
    with pytest.raises(security.InvalidAccessTokenError):
        security.decode_access_token(token)


def test_access_token_with_wrong_signature_rejected() -> None:
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "another-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
    )
    with pytest.raises(security.InvalidAccessTokenError):
        security.decode_access_token(token)


def test_unsigned_token_rejected() -> None:
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        None,
        algorithm="none",
    )
    with pytest.raises(security.InvalidAccessTokenError):
        security.decode_access_token(token)


def test_token_of_other_type_rejected() -> None:
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(security.InvalidAccessTokenError):
        security.decode_access_token(token)


def test_password_hash_roundtrip() -> None:
    hashed = security.hash_password("a fine passphrase")
    assert security.verify_password("a fine passphrase", hashed)
    assert not security.verify_password("another one", hashed)
    assert not security.verify_password("anything", "not-a-valid-hash")


def test_opaque_tokens_are_unique_and_stored_hashed() -> None:
    a, b = security.generate_opaque_token(), security.generate_opaque_token()
    assert a != b and len(a) >= 64
    assert security.hash_token(a) != a and len(security.hash_token(a)) == 64


# -------------------------------------------------------------- rate limit


class _BrokenRedis:
    async def get(self, key: str) -> None:
        raise RedisConnectionError("down")

    async def delete(self, key: str) -> None:
        raise RedisConnectionError("down")

    def pipeline(self, transaction: bool = True) -> _BrokenRedis:
        raise RedisConnectionError("down")


async def test_rate_limiter_fails_open_when_redis_is_down() -> None:
    limiter = RateLimiter(redis=_BrokenRedis())  # type: ignore[arg-type]
    key = limit_key("login-fail-email", "an@example.com")

    assert (await limiter.check(key, limit=1)).blocked is False
    assert await limiter.hit(key, window_seconds=60) == 0
    await limiter.reset(key)


def test_limit_key_does_not_contain_raw_identifier() -> None:
    key = limit_key("login-fail-email", "an@example.com")
    assert "an@example.com" not in key and key.startswith("rl:login-fail-email:")
