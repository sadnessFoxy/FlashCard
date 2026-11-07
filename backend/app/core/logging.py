"""
Cấu hình logging.
Tuân thủ R10: không ghi mật khẩu, token, khóa API, nội dung tài liệu nhạy cảm.
"""
from __future__ import annotations

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Thiết lập logging cho ứng dụng."""
    log_level = logging.DEBUG if settings.is_development else logging.INFO

    # Format đơn giản cho development; JSON cho production
    if settings.is_development:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%H:%M:%S"
    else:
        # JSON format để dễ parse trong production log aggregator
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        datefmt = "%Y-%m-%dT%H:%M:%SZ"

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Lấy logger theo tên module."""
    return logging.getLogger(name)
