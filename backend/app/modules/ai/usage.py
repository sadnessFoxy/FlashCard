"""
Records every AI call in `ai_usage` (tokens, model, latency, outcome).
R10: metadata only, never prompt or document content.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


class UsageRecorder(Protocol):
    async def __call__(
        self,
        *,
        user_id: str | None,
        provider: str,
        model: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        error_code: str | None = None,
    ) -> None: ...


def estimate_tokens(text: str) -> int:
    """Rough count (~4 chars per token); real counts come from the provider later."""
    return max(1, len(text) // 4) if text else 0


async def record_ai_usage(
    *,
    user_id: str | None,
    provider: str,
    model: str,
    operation: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    success: bool,
    error_code: str | None = None,
) -> None:
    """Best effort: a failure to record must never break the AI call itself."""
    # Imported lazily so providers and gateway stay importable without the DB layer.
    from app.db.session import AsyncSessionLocal
    from app.modules.usage.models import AiUsage

    try:
        async with AsyncSessionLocal() as session:
            session.add(
                AiUsage(
                    user_id=uuid.UUID(user_id) if user_id else None,
                    provider=provider,
                    model=model,
                    operation=operation,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=int(latency_ms),
                    success=success,
                    error_code=error_code,
                )
            )
            await session.commit()
    except (SQLAlchemyError, OSError) as exc:
        logger.warning("Could not record AI usage: %s", type(exc).__name__)
