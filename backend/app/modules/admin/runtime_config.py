"""
Settings an admin can change without redeploying (A5).

Values live in `app_settings`; a key that was never changed falls back to the
environment (app.core.config). Each process caches the values for CACHE_SECONDS, so a
change reaches every API and worker process within that time.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal

CACHE_SECONDS = 15.0


@dataclass(frozen=True)
class SettingSpec:
    kind: type
    default: Callable[[], Any]
    minimum: int | None = None
    maximum: int | None = None

    def validate(self, value: Any) -> Any:
        """The value in its proper type, or ValueError."""
        if self.kind is bool:
            if not isinstance(value, bool):
                raise ValueError("must be true or false")
            return value
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("must be a whole number")
        if self.minimum is not None and value < self.minimum:
            raise ValueError(f"must be at least {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise ValueError(f"must be at most {self.maximum}")
        return value


SPECS: dict[str, SettingSpec] = {
    "user_daily_query_limit": SettingSpec(int, lambda: settings.USER_DAILY_QUERY_LIMIT, 0, 10_000),
    "max_file_size_mb": SettingSpec(int, lambda: settings.MAX_FILE_SIZE_MB, 1, 100),
    "max_pages": SettingSpec(int, lambda: settings.MAX_PAGES, 1, 2_000),
    "max_documents_per_user": SettingSpec(int, lambda: settings.MAX_DOCUMENTS_PER_USER, 1, 1_000),
    # Emergency switch: off makes every AI call fail fast, so features degrade (U8).
    "ai_enabled": SettingSpec(bool, lambda: True),
    # 0 = no budget; otherwise the overview shows today's token use against it.
    "ai_daily_token_budget": SettingSpec(int, lambda: settings.AI_DAILY_TOKEN_BUDGET, 0, 10**10),
}


class RuntimeConfig:
    def __init__(self) -> None:
        self._values: dict[str, Any] | None = None
        self._loaded_at = 0.0

    async def values(self) -> dict[str, Any]:
        if self._values is None or time.monotonic() - self._loaded_at > CACHE_SECONDS:
            self._values = await self._load()
            self._loaded_at = time.monotonic()
        return dict(self._values)

    async def get(self, key: str) -> Any:
        return (await self.values())[key]

    async def ai_enabled(self) -> bool:
        return bool(await self.get("ai_enabled"))

    def invalidate(self) -> None:
        """Drop this process's cache (after an admin change, and between tests)."""
        self._values = None

    @staticmethod
    async def _load() -> dict[str, Any]:
        from app.modules.admin.models import AppSetting

        values = {key: spec.default() for key, spec in SPECS.items()}
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(select(AppSetting.key, AppSetting.value))).all()
        for key, value in rows:
            if key in SPECS:
                values[key] = value
        return values


runtime_config = RuntimeConfig()
