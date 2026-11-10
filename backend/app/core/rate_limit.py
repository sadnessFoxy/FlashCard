"""
Fixed-window attempt counters in Redis (login failures, sign-ups; later AI quotas).

Keys hash the identifier so no raw email lands in Redis (R10).
If Redis is down we fail open and log: locking everyone out is worse.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)

_PREFIX = "rl"


def limit_key(scope: str, identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode()).hexdigest()[:32]
    return f"{_PREFIX}:{scope}:{digest}"


@dataclass(frozen=True)
class LimitStatus:
    blocked: bool
    retry_after_seconds: int = 0


class RateLimiter:
    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis

    @property
    def redis(self) -> Redis:
        return self._redis or get_redis()

    async def check(self, key: str, limit: int) -> LimitStatus:
        """Whether the limit is reached, without counting."""
        try:
            raw = await self.redis.get(key)
            if raw is not None and int(raw) >= limit:
                ttl = await self.redis.ttl(key)
                return LimitStatus(blocked=True, retry_after_seconds=max(ttl, 1))
        except RedisError as exc:
            logger.warning("Rate limit check skipped (Redis error: %s)", type(exc).__name__)
        return LimitStatus(blocked=False)

    async def hit(self, key: str, window_seconds: int) -> int:
        """Count one attempt; the window starts at the first hit. Returns the count."""
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, window_seconds, nx=True)
                count, _ = await pipe.execute()
            return int(count)
        except RedisError as exc:
            logger.warning("Rate limit hit not recorded (Redis error: %s)", type(exc).__name__)
            return 0

    async def hit_and_check(self, key: str, limit: int, window_seconds: int) -> LimitStatus:
        """Count one attempt and block once the count exceeds `limit`."""
        count = await self.hit(key, window_seconds)
        if count > limit:
            return await self.check(key, limit)
        return LimitStatus(blocked=False)

    async def reset(self, key: str) -> None:
        try:
            await self.redis.delete(key)
        except RedisError as exc:
            logger.warning("Rate limit reset skipped (Redis error: %s)", type(exc).__name__)


rate_limiter = RateLimiter()
