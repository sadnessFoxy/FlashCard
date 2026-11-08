"""
JWT token và password hashing.
Tuân thủ R3: SECRET_KEY từ env, không hardcode.
Tuân thủ R12: access token ngắn (15 phút), refresh token có rotation.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Dùng argon2 (ưu tiên) với bcrypt fallback
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=1,
)

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash mật khẩu bằng argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So sánh mật khẩu với hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Tạo JWT access token (ngắn hạn)."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return str(jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM))


def create_refresh_token(subject: str) -> str:
    """Tạo JWT refresh token (dài hạn)."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
        # Jti (JWT ID) để hỗ trợ thu hồi token
        "jti": secrets.token_hex(16),
    }
    return str(jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM))


def decode_token(token: str) -> dict[str, Any]:
    """Decode và verify JWT token. Raise JWTError nếu không hợp lệ."""
    return dict(jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM]))


def create_one_time_token() -> tuple[str, str]:
    """
    Tạo token một lần (cho xác minh email, đặt lại mật khẩu).
    Trả về (token_plaintext, token_hash).
    Chỉ lưu hash vào DB; gửi plaintext qua email.
    Tuân thủ R15: token chỉ dùng một lần, có hạn, chỉ lưu dạng băm.
    """
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def hash_token(token: str) -> str:
    """Hash token để lưu vào DB."""
    return hashlib.sha256(token.encode()).hexdigest()
