"""
Application errors; codes match contract/openapi.yaml.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for expected business errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers or {}


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
            {"max_size_mb": max_mb},
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
    """Transient per-minute limit: wait `retry_after_seconds`, then retry."""

    def __init__(self, retry_after_seconds: float | None = None) -> None:
        self.retry_after_seconds = retry_after_seconds
        details = {"retry_after_seconds": int(retry_after_seconds)} if retry_after_seconds else None
        super().__init__(
            "AI_RATE_LIMITED",
            "AI service rate limit reached, please try again later",
            429,
            details,
        )


class AiCircuitOpenError(AiTemporarilyUnavailableError):
    """The gateway is refusing calls after repeated provider failures."""


class AiQuotaExhaustedError(AppError):
    """Daily quota or billing exhausted: never retry (R8). API code: AI_TEMPORARILY_UNAVAILABLE."""

    def __init__(self) -> None:
        super().__init__(
            "AI_TEMPORARILY_UNAVAILABLE",
            "AI features are temporarily unavailable",
            503,
        )


class ContextTooLongError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "CONTEXT_TOO_LONG",
            "Query context is too long, please reduce document selection",
            400,
        )


# ------- Auth (docs/specs/f2-email-auth.md) -------


class InvalidCredentialsError(AppError):
    """Same error for unknown email and wrong password (no enumeration)."""

    def __init__(self) -> None:
        super().__init__("INVALID_CREDENTIALS", "Invalid email or password", 401)


class AccountBlockedError(AppError):
    def __init__(self) -> None:
        super().__init__("ACCOUNT_BLOCKED", "This account has been blocked", 403)


class EmailUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "EMAIL_UNAVAILABLE",
            "Cannot register with this email. Sign in or reset the password instead.",
            409,
        )


class WeakPasswordError(AppError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            "WEAK_PASSWORD", "Password does not meet the rules", 422, {"reason": reason}
        )


class TooManyAttemptsError(AppError):
    def __init__(self, retry_after_seconds: int) -> None:
        retry_after = max(1, retry_after_seconds)
        super().__init__(
            "TOO_MANY_ATTEMPTS",
            "Too many attempts, try again later",
            429,
            {"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )


class InvalidRefreshTokenError(AppError):
    def __init__(self) -> None:
        super().__init__("INVALID_REFRESH_TOKEN", "Session expired, sign in again", 401)


# ------- Spaces (docs/specs/f4b-spaces.md) -------


class SpaceNameTakenError(AppError):
    def __init__(self) -> None:
        super().__init__("SPACE_NAME_TAKEN", "A space with this name already exists", 409)


# ------- Documents (docs/specs/f5-document-upload.md) -------


class ConsentRequiredError(AppError):
    def __init__(self, version: str) -> None:
        super().__init__(
            "CONSENT_REQUIRED", "Consent to AI processing is required", 403, {"version": version}
        )


class DocumentLimitReachedError(AppError):
    def __init__(self, limit: int) -> None:
        super().__init__(
            "DOCUMENT_LIMIT_REACHED", "Document limit reached", 409, {"max_documents": limit}
        )


class TooManyPagesError(AppError):
    def __init__(self, max_pages: int) -> None:
        super().__init__("TOO_MANY_PAGES", "Too many pages", 422, {"max_pages": max_pages})


class PdfEncryptedError(AppError):
    def __init__(self) -> None:
        super().__init__("PDF_ENCRYPTED", "Password-protected PDFs are not supported", 422)


class SpaceRequiredError(AppError):
    def __init__(self) -> None:
        super().__init__("SPACE_REQUIRED", "space_id is required", 422)


class IdempotencyKeyReusedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "IDEMPOTENCY_KEY_REUSED", "Idempotency-Key was already used for another file", 409
        )


class EmailNotVerifiedError(AppError):
    def __init__(self) -> None:
        super().__init__("EMAIL_NOT_VERIFIED", "Verify your email before uploading", 403)


class DocumentNotRetryableError(AppError):
    def __init__(self, status: str) -> None:
        super().__init__(
            "DOCUMENT_NOT_RETRYABLE",
            "Only failed or paused documents can be retried",
            409,
            {"status": status},
        )


# ------- Flashcards (docs/specs/f9-flashcards.md) -------


class DeckFullError(AppError):
    def __init__(self, limit: int) -> None:
        super().__init__(
            "DECK_FULL", "This deck has reached its card limit", 409, {"max_cards": limit}
        )


class SourceEmptyError(AppError):
    """The chosen source has no text to make cards from."""

    def __init__(self) -> None:
        super().__init__("SOURCE_EMPTY", "The selected source has no text", 422)
