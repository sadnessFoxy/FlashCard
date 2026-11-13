"""Shared ARQ names and connection settings (imported by API and worker)."""

from __future__ import annotations

from arq.connections import RedisSettings

from app.core.config import settings

INGEST_FUNCTION = "process_document"


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.REDIS_URL)
