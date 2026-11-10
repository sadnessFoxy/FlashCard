"""
Request dependencies. Every authenticated endpoint uses `get_current_user` (basis for R4).
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccountBlockedError, UnauthorizedError
from app.core.security import InvalidAccessTokenError, decode_access_token
from app.db.session import get_db
from app.modules.auth.cookies import ACCESS_COOKIE
from app.modules.auth.service import ClientInfo
from app.modules.users.models import User
from app.modules.users.service import UserService


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token.strip()
    return None


def access_token_from_request(request: Request) -> str | None:
    """Native sends a Bearer header; web sends the httpOnly cookie."""
    return _bearer_token(request) or request.cookies.get(ACCESS_COOKIE)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = access_token_from_request(request)
    if not token:
        raise UnauthorizedError()
    try:
        claims = decode_access_token(token)
    except InvalidAccessTokenError:
        raise UnauthorizedError() from None

    user = await UserService(db).get(claims.user_id)
    if user is None or user.deleted_at is not None:
        raise UnauthorizedError()
    if user.status != "active":
        raise AccountBlockedError()
    return user


def get_client_info(request: Request) -> ClientInfo:
    # Behind a proxy (Railway), run uvicorn with --proxy-headers to get the real IP.
    ip = request.client.host if request.client else "unknown"
    return ClientInfo(ip=ip, user_agent=request.headers.get("User-Agent"))
