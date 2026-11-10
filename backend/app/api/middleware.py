"""
Middleware cho FastAPI application.
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach an X-Request-ID to every request and response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Log request duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        logger.debug(
            "Request %s %s completed in %.2fms (status=%d)",
            request.method,
            request.url.path,
            process_time,
            response.status_code,
        )
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response


UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_SESSION_COOKIES = ("access_token", "refresh_token")


class CsrfOriginMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection for cookie-based web clients (spec f2 section 7).

    Unsafe requests that carry a session cookie, or claim to be the web client, must send
    an Origin listed in CORS_ORIGINS. Native clients use Bearer tokens and are unaffected.
    """

    def __init__(self, app: object, allowed_origins: list[str]) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._allowed = {origin.rstrip("/") for origin in allowed_origins}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in UNSAFE_METHODS and self._needs_check(request):
            origin = (request.headers.get("Origin") or "").rstrip("/")
            if origin not in self._allowed:
                logger.warning("CSRF check rejected %s %s", request.method, request.url.path)
                return JSONResponse(
                    status_code=403,
                    content={"code": "CSRF_REJECTED", "message": "Origin not allowed"},
                )
        return await call_next(request)

    @staticmethod
    def _needs_check(request: Request) -> bool:
        if request.headers.get("X-Client-Platform") == "web":
            return True
        has_cookie = any(name in request.cookies for name in _SESSION_COOKIES)
        has_bearer = request.headers.get("Authorization", "").lower().startswith("bearer ")
        return has_cookie and not has_bearer
