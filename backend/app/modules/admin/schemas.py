"""Admin I/O schemas (contract tag `admin`). Metadata only: never document or chat content (R13)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------- overview (A2) ----------


class OverviewOut(_Strict):
    users_total: int
    users_active_today: int
    documents_by_status: dict[str, int]
    questions_today: int
    ai_calls_today: int
    ai_failures_today: int
    ai_tokens_today: int
    ai_daily_token_budget: int
    ai_budget_used_percent: float | None
    ai_enabled: bool
    circuit_state: Literal["closed", "open", "half_open"]
    queue_length: int


# ---------- users (A3) ----------


class QuotaOverrideOut(_Strict):
    daily_limit: int
    expires_at: datetime | None


class AdminUserOut(_Strict):
    id: uuid.UUID
    email: str
    role: Literal["user", "admin"]
    status: Literal["active", "blocked"]
    sign_in_methods: list[str]
    email_verified: bool
    created_at: datetime
    document_count: int
    questions_today: int
    quota_override: QuotaOverrideOut | None


class AdminUserListOut(_Strict):
    items: list[AdminUserOut]
    total: int


class BlockUserRequest(_Strict):
    reason: str = Field(min_length=1, max_length=500)


class QuotaOverrideRequest(_Strict):
    """`daily_limit` null removes the override."""

    daily_limit: int | None = Field(ge=0, le=10_000)
    expires_at: datetime | None = None


# ---------- documents and jobs (A4) ----------


class AdminJobOut(_Strict):
    status: str
    attempts: int
    last_error_code: str | None


class AdminDocumentOut(_Strict):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner_email: str
    filename: str
    file_kind: str
    text_source: str | None
    page_count: int
    status: str
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    last_job: AdminJobOut | None


class AdminDocumentListOut(_Strict):
    items: list[AdminDocumentOut]


# ---------- settings (A5) ----------


class SettingsOut(_Strict):
    values: dict[str, Any]
    defaults: dict[str, Any]


class SettingsPatch(_Strict):
    values: dict[str, Any] = Field(min_length=1)


# ---------- audit log (A7) ----------


class AuditEntryOut(_Strict):
    id: uuid.UUID
    actor_email: str
    action: str
    target_type: str
    target_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None
    created_at: datetime


class AuditListOut(_Strict):
    items: list[AuditEntryOut]
