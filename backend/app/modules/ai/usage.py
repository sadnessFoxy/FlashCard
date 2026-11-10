"""
Records every AI call (tokens, model, latency).
Called by llm_gateway after each successful call.
R10: never stores prompt or document content.
"""

from __future__ import annotations

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
    Record one AI call
    in ai_usage, for quota and cost tracking.

    Notes:
    - no prompt, document or personal data (R10)
    - metadata only: provider, model, token count, latency
    """
    # TODO(F5): persist to the ai_usage table
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
