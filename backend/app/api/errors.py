"""
Xử lý lỗi thống nhất cho toàn bộ API.
Trả về đúng format theo contract/openapi.yaml.
Tuân thủ R8: lỗi hết hạn mức trả mã lỗi trong contract, không trả 500.
"""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


def make_error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body.update(details)
    return JSONResponse(status_code=status_code, content=body)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Xử lý AppError - lỗi nghiệp vụ đã biết."""
    return make_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details if exc.details else None,
    )


async def validation_error_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Xử lý lỗi validation Pydantic."""
    return make_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        details={"errors": exc.errors()},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Xử lý lỗi không mong đợi - không tiết lộ chi tiết nội bộ."""
    logger.exception("Unhandled exception: %s", exc)
    return make_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred",
        status_code=500,
    )
