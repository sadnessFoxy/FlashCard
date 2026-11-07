#!/usr/bin/env python3
"""
Script dọn dẹp jobs và dữ liệu cũ.
Chạy định kỳ qua cron hoặc ARQ scheduled task.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def cleanup_stale_processing_documents() -> int:
    """
    Đặt lại tài liệu stuck ở PROCESSING quá lâu.
    Tài liệu ở PROCESSING quá 30 phút -> chuyển về PENDING để retry.
    """
    # TODO (giai đoạn F5): implement với DB query
    logger.info("Checking for stale processing documents")
    return 0


async def cleanup_expired_one_time_tokens() -> int:
    """Xóa token xác minh email và reset mật khẩu đã hết hạn."""
    # TODO (giai đoạn F4): implement
    logger.info("Cleaning up expired one-time tokens")
    return 0


async def main() -> None:
    logger.info("Starting cleanup jobs at %s", datetime.now(UTC).isoformat())

    stale_docs = await cleanup_stale_processing_documents()
    expired_tokens = await cleanup_expired_one_time_tokens()

    logger.info(
        "Cleanup complete: stale_docs=%d expired_tokens=%d",
        stale_docs,
        expired_tokens,
    )


if __name__ == "__main__":
    asyncio.run(main())
