"""
ARQ queue configuration.
"""
from __future__ import annotations

from arq.connections import RedisSettings

from app.core.config import settings


def get_redis_settings() -> RedisSettings:
    """Lấy Redis settings cho ARQ từ REDIS_URL."""
    # Parse redis://host:port/db
    url = settings.REDIS_URL
    # ARQ RedisSettings từ URL
    return RedisSettings.from_dsn(url)


class WorkerSettings:
    """ARQ worker settings."""
    redis_settings = get_redis_settings()
    # Import các task functions
    functions: list = []  # Điền vào khi thêm tasks
    max_jobs = 10
    job_timeout = 300  # 5 phút timeout mỗi job
