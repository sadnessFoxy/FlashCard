"""
Classify Gemini API errors (docs/QUOTA_AND_RESILIENCE.md):
- per-minute limits -> AiRateLimitedError(retry_after): wait and retry
- daily quota, billing, bad or disabled key -> AiQuotaExhaustedError: never retry, pause jobs
- context too long -> ContextTooLongError
- 5xx and anything unknown -> AiTemporarilyUnavailableError: limited retries
"""

from __future__ import annotations

import re
from typing import Any

from app.core.exceptions import (
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
    AppError,
    ContextTooLongError,
)

_RETRY_DELAY = re.compile(r"^(\d+(?:\.\d+)?)s$")
_DAILY_HINTS = ("perday", "per_day", "daily")
_BILLING_HINTS = ("billing", "credit", "prepayment", "spend")


def _retry_delay_seconds(details: list[dict[str, Any]]) -> float | None:
    for item in details:
        if str(item.get("@type", "")).endswith("RetryInfo"):
            match = _RETRY_DELAY.match(str(item.get("retryDelay", "")))
            if match:
                return float(match.group(1))
    return None


def _quota_ids(details: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for item in details:
        if str(item.get("@type", "")).endswith("QuotaFailure"):
            for violation in item.get("violations", []) or []:
                ids.append(str(violation.get("quotaId", "")))
    return ids


def classify_gemini_error(status_code: int, body: Any) -> AppError:
    error = body.get("error", {}) if isinstance(body, dict) else {}
    status = str(error.get("status", ""))
    message = str(error.get("message", "")).lower()
    details = error.get("details", []) if isinstance(error.get("details"), list) else []

    if status_code == 429 or status == "RESOURCE_EXHAUSTED":
        quota_ids = " ".join(_quota_ids(details)).lower()
        if any(h in quota_ids for h in _DAILY_HINTS) or any(h in message for h in _BILLING_HINTS):
            return AiQuotaExhaustedError()
        return AiRateLimitedError(retry_after_seconds=_retry_delay_seconds(details))

    if status_code in (401, 403) or status in ("PERMISSION_DENIED", "UNAUTHENTICATED"):
        return AiQuotaExhaustedError()
    if status_code == 400 and "api key" in message:
        return AiQuotaExhaustedError()
    if status == "INVALID_ARGUMENT" and (
        "too long" in message or "maximum number of tokens" in message
    ):
        return ContextTooLongError()
    return AiTemporarilyUnavailableError()
