"""
ARQ queue configuration.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from arq.connections import RedisSettings

from app.core.config import settings


def get_redis_settings() -> RedisSettings:
    """ARQ Redis settings from REDIS_URL."""
    # Parse redis://host:port/db
    url = settings.REDIS_URL
    return RedisSettings.from_dsn(url)


class WorkerSettings:
    """ARQ worker settings."""

    redis_settings = get_redis_settings()
    # Task functions
    functions: list[Callable[..., Any]] = []  # register tasks here
    max_jobs = 10
    job_timeout = 300  # seconds per job
