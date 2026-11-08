"""
Rate limiting dùng Redis.
Chi tiết hạn mức ba tầng: docs/QUOTA_AND_RESILIENCE.md.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter dựa trên Redis sliding window.
    Sẽ implement đầy đủ ở giai đoạn 3/5.
    """

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        Kiểm tra rate limit.
        Trả về (is_allowed, remaining_count).
        """
        # TODO (giai đoạn 3): implement Redis sliding window
        return True, limit

    async def get_remaining(self, key: str) -> int:
        """Lấy số lượt còn lại."""
        # TODO (giai đoạn 3): implement
        return 0


rate_limiter = RateLimiter()
