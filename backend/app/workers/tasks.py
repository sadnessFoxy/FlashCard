"""
Định nghĩa các ARQ task functions.
"""
from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


async def cleanup_expired_tokens(ctx: dict) -> None:  # type: ignore[type-arg]
    """Xóa token hết hạn khỏi database."""
    logger.info("Running cleanup_expired_tokens task")
    # TODO (giai đoạn F2): implement
