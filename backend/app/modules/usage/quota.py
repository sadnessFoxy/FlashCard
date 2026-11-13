"""
Per-user daily question quota in Redis (docs/QUOTA_AND_RESILIENCE.md, tier 2).
Days follow local time (QUOTA_UTC_OFFSET_HOURS). Redis failures fail open and are logged.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


@dataclass(frozen=True)
class QuotaStatus:
    daily_limit: int
    used_today: int
    resets_at: datetime

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.used_today)


def _local_tz() -> timezone:
    return timezone(timedelta(hours=settings.QUOTA_UTC_OFFSET_HOURS))


def _today_and_reset(now: datetime | None = None) -> tuple[str, datetime]:
    local = (now or datetime.now(UTC)).astimezone(_local_tz())
    midnight = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return local.strftime("%Y%m%d"), midnight.astimezone(UTC)


class QuestionQuota:
    def __init__(self, redis: Redis | None = None, now: datetime | None = None) -> None:
        self._redis = redis
        self._now = now

    @property
    def redis(self) -> Redis:
        return self._redis or get_redis()

    def _key(self, user_id: uuid.UUID) -> tuple[str, datetime]:
        day, reset = _today_and_reset(self._now)
        return f"quota:questions:{user_id}:{day}", reset

    async def status(self, user_id: uuid.UUID) -> QuotaStatus:
        key, reset = self._key(user_id)
        try:
            used = int(await self.redis.get(key) or 0)
        except RedisError as exc:
            logger.warning("Quota read failed, allowing (%s)", type(exc).__name__)
            used = 0
        return QuotaStatus(settings.USER_DAILY_QUERY_LIMIT, used, reset)

    async def reserve(self, user_id: uuid.UUID) -> bool:
        """Take one question atomically; False when the limit is already reached."""
        key, reset = self._key(user_id)
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expireat(key, reset + timedelta(hours=1))
                used, _ = await pipe.execute()
            if int(used) > settings.USER_DAILY_QUERY_LIMIT:
                await self.redis.decr(key)
                return False
            return True
        except RedisError as exc:
            logger.warning("Quota reserve failed, allowing (%s)", type(exc).__name__)
            return True

    async def refund(self, user_id: uuid.UUID) -> None:
        key, _ = self._key(user_id)
        try:
            if int(await self.redis.get(key) or 0) > 0:
                await self.redis.decr(key)
        except RedisError as exc:
            logger.warning("Quota refund failed (%s)", type(exc).__name__)


def get_question_quota() -> QuestionQuota:
    return QuestionQuota()
