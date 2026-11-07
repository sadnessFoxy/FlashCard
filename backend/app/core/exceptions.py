"""
Exceptions tùy chỉnh cho toàn bộ ứng dụng.
Các mã lỗi khớp với contract/openapi.yaml.
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base exception cho tất cả lỗi nghiệp vụ."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__("UNAUTHORIZED", message, 401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__("FORBIDDEN", message, 403)


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__("NOT_FOUND", f"{resource} not found", 404)


class ValidationError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("VALIDATION_ERROR", message, 422, details)


class FileTooLargeError(AppError):
    def __init__(self, max_mb: int) -> None:
        super().__init__(
            "FILE_TOO_LARGE",
            f"File exceeds maximum size of {max_mb}MB",
            413,
        )


class FileTypeNotSupportedError(AppError):
    def __init__(self, file_type: str) -> None:
        super().__init__(
            "FILE_TYPE_NOT_SUPPORTED",
            f"File type {file_type!r} is not supported",
            415,
        )


class DocumentNotReadyError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "DOCUMENT_NOT_READY",
            "Document is still being processed",
            409,
        )


class DocumentProcessingFailedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "DOCUMENT_PROCESSING_FAILED",
            "Document processing failed",
            500,
        )


class UserQuotaExceededError(AppError):
    def __init__(
        self,
        quota_remaining: int = 0,
        quota_reset_at: str | None = None,
    ) -> None:
        details: dict[str, Any] = {"quota_remaining": quota_remaining}
        if quota_reset_at:
            details["quota_reset_at"] = quota_reset_at
        super().__init__(
            "USER_QUOTA_EXCEEDED",
            "You have used all your queries for today",
            429,
            details,
        )


class AiTemporarilyUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "AI_TEMPORARILY_UNAVAILABLE",
            "AI features are temporarily unavailable",
            503,
        )


class AiRateLimitedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "AI_RATE_LIMITED",
            "AI service rate limit reached, please try again later",
            429,
        )


class ContextTooLongError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "CONTEXT_TOO_LONG",
            "Query context is too long, please reduce document selection",
            400,
        )
