"""
Shared Redis client, created lazily and closed on shutdown.
"""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import settings

_client: Redis | None = None


def get_redis() -> Redis:
    """Return the shared client, creating it on first use."""
    global _client
    if _client is None:
        _client = Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


async def close_redis() -> None:
    """Close the shared client."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
