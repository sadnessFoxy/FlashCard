"""
Error handlers producing the contract's `ErrorResponse`.
R8: quota errors use contract codes, never 500.
R10: validation errors list field names only, never input values (may be passwords).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Framework-level HTTP errors (bad JSON, unknown route, wrong method) mapped to contract codes.
_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
}

# Leading "loc" item is the request part, not the field name.
_LOCATION_PREFIXES = {"body", "query", "path", "header", "cookie"}


def make_error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body.update(details)
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def _safe_errors(errors: Sequence[Any]) -> list[dict[str, str]]:
    """Keep field and type only; drop `input`/`ctx`, which may hold user data."""
    safe: list[dict[str, str]] = []
    for err in errors:
        loc = [str(part) for part in err.get("loc", ())]
        if loc and loc[0] in _LOCATION_PREFIXES:
            loc = loc[1:]
        kind = str(err.get("type", "invalid"))
        # json_invalid points at a character offset, not a field.
        field = "body" if kind == "json_invalid" else ".".join(loc) or "body"
        safe.append({"field": field, "type": kind})
    return safe


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Expected business error."""
    return make_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details or None,
        headers=exc.headers or None,
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Malformed request (body, header, query)."""
    return make_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        details={"errors": _safe_errors(exc.errors())},
    )


async def validation_error_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Pydantic validation error raised inside our code."""
    return make_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        details={"errors": _safe_errors(exc.errors())},
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Starlette/FastAPI HTTP errors, reshaped into ErrorResponse."""
    return make_error_response(
        code=_HTTP_CODES.get(exc.status_code, "HTTP_ERROR"),
        message=str(exc.detail) if exc.status_code < 500 else "Server error",
        status_code=exc.status_code,
        headers=dict(exc.headers) if exc.headers else None,
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Unexpected error: hide internals."""
    logger.exception("Unhandled exception: %s", type(exc).__name__)
    return make_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred",
        status_code=500,
    )
