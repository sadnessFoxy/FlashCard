"""
Redis client dùng chung (cache, hạn mức, hàng đợi).
Tạo lười một lần, đóng khi app tắt.
"""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import settings

_client: Redis | None = None


def get_redis() -> Redis:
    """Trả về Redis client dùng chung, tạo ở lần gọi đầu."""
    global _client
    if _client is None:
        _client = Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


async def close_redis() -> None:
    """Đóng kết nối Redis khi app tắt."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
