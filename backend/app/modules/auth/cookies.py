"""
Web session cookies (R12): httpOnly, so JavaScript never sees tokens.
`refresh_token` is scoped to /v1/auth/ to limit exposure.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Response

from app.core.config import settings
from app.core.security import access_token_ttl_seconds

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/v1/auth"
AUTH_COOKIES = (ACCESS_COOKIE, REFRESH_COOKIE)


def set_session_cookies(
    response: Response, *, access_token: str, refresh_token: str, refresh_expires_at: datetime
) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=access_token_ttl_seconds(),
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    refresh_max_age = max(int((refresh_expires_at - datetime.now(UTC)).total_seconds()), 0)
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=refresh_max_age,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def clear_session_cookies(response: Response) -> None:
    for name, path in ((ACCESS_COOKIE, "/"), (REFRESH_COOKIE, REFRESH_COOKIE_PATH)):
        response.delete_cookie(
            name, path=path, httponly=True, secure=settings.cookie_secure, samesite="lax"
        )
