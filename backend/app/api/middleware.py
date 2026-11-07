"""
Middleware cho FastAPI application.
"""
from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Thêm X-Request-ID vào mỗi request/response."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Ghi log thời gian xử lý request."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # type: ignore[override]
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
