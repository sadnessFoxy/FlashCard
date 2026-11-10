#!/usr/bin/env python3
"""
Cleanup script for stale jobs and data,
run periodically via cron or an ARQ scheduled task.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def cleanup_stale_processing_documents() -> int:
    """
    Requeue documents stuck in PROCESSING:
    after 30 minutes they go back to QUEUED for retry.
    """
    # TODO(F5): implement
    logger.info("Checking for stale processing documents")
    return 0


async def cleanup_expired_one_time_tokens() -> int:
    """Delete expired email-verification and password-reset tokens."""
    # TODO(F4): implement
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
