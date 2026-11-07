"""
Ghi nhận mỗi lần gọi AI (token usage, model, latency).
Dùng bởi llm_gateway sau mỗi lần gọi thành công.
Tuân thủ R10: không ghi nội dung prompt hay document.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


async def record_ai_usage(
    user_id: str | None,
    provider: str,
    model: str,
    operation: str,  # "embed" | "chat" | "generate"
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    success: bool,
    error_code: str | None = None,
) -> None:
    """
    Ghi nhận một lần gọi AI.
    Lưu vào bảng ai_usage để theo dõi hạn mức và chi phí.

    Lưu ý:
    - Không ghi nội dung prompt, document, hay thông tin cá nhân (R10)
    - Chỉ ghi metadata: provider, model, token count, latency
    """
    # TODO (giai đoạn 1/F): implement lưu vào DB table ai_usage
    logger.debug(
        "AI usage: provider=%s model=%s op=%s input_tokens=%d "
        "output_tokens=%d latency=%.0fms success=%s user=%s",
        provider,
        model,
        operation,
        input_tokens,
        output_tokens,
        latency_ms,
        success,
        user_id or "anonymous",
    )
