"""Usage I/O schemas (contract tag `usage`)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.usage.quota import QuotaStatus


class UsageCounter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_limit: int
    used_today: int
    remaining: int
    resets_at: datetime

    @classmethod
    def from_status(cls, status: QuotaStatus) -> UsageCounter:
        return cls(
            daily_limit=status.daily_limit,
            used_today=status.used_today,
            remaining=status.remaining,
            resets_at=status.resets_at,
        )


class UsageOut(UsageCounter):
    """Top-level fields are the question quota; other AI features have their own counters."""

    card_suggestions: UsageCounter
