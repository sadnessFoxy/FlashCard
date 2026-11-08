"""
LLM Gateway: điểm vào duy nhất cho mọi lời gọi AI.
Tuân thủ R5: mọi AI call qua gateway này.
Tuân thủ R8: lỗi hết hạn mức không retry, chuyển PAUSED_QUOTA.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Any

from app.core.exceptions import AiRateLimitedError, AiTemporarilyUnavailableError
from app.core.logging import get_logger
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker, CircuitState
from app.modules.ai.providers.base import LLMProvider
from app.modules.ai.usage import record_ai_usage

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]  # Exponential backoff (giây)


class LLMGateway:
    """
    Gateway cho tất cả AI calls.
    - Retry cho lỗi tạm thời (network, 5xx)
    - Không retry lỗi hết hạn mức (quota exhausted)
    - Circuit breaker để ngăn gọi liên tục khi provider lỗi
    - Ghi usage sau mỗi lần gọi
    """

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )

    async def embed(
        self,
        texts: list[str],
        user_id: str | None = None,
    ) -> list[list[float]]:
        """Tạo embeddings với retry và circuit breaker."""
        if self._circuit_breaker.state == CircuitState.OPEN:
            raise AiTemporarilyUnavailableError()

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            start_time = time.perf_counter()
            try:
                result = await self._provider.embed(texts)
                latency_ms = (time.perf_counter() - start_time) * 1000

                self._circuit_breaker.record_success()
                await record_ai_usage(
                    user_id=user_id,
                    provider=self._provider.provider_name,
                    model="embedding",
                    operation="embed",
                    input_tokens=sum(len(t.split()) for t in texts),
                    output_tokens=0,
                    latency_ms=latency_ms,
                    success=True,
                )
                return result

            except (AiRateLimitedError, AiTemporarilyUnavailableError) as e:
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._circuit_breaker.record_failure()

                await record_ai_usage(
                    user_id=user_id,
                    provider=self._provider.provider_name,
                    model="embedding",
                    operation="embed",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    success=False,
                    error_code=e.code if hasattr(e, "code") else "AI_ERROR",
                )

                # R8: lỗi hết hạn mức - không retry
                if isinstance(e, AiRateLimitedError):
                    raise

                last_error = e

                if attempt < MAX_RETRIES - 1:
                    import asyncio

                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        "Embed failed (attempt=%d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                        e,
                    )
                    await asyncio.sleep(delay)

        raise last_error or AiTemporarilyUnavailableError()

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        user_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat với circuit breaker."""
        if self._circuit_breaker.state == CircuitState.OPEN:
            raise AiTemporarilyUnavailableError()

        start_time = time.perf_counter()
        try:
            async for chunk in self._provider.chat_stream(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            ):
                yield chunk

            latency_ms = (time.perf_counter() - start_time) * 1000
            self._circuit_breaker.record_success()
            await record_ai_usage(
                user_id=user_id,
                provider=self._provider.provider_name,
                model="chat",
                operation="chat",
                input_tokens=sum(len(m["content"].split()) for m in messages),
                output_tokens=0,
                latency_ms=latency_ms,
                success=True,
            )

        except (AiRateLimitedError, AiTemporarilyUnavailableError) as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._circuit_breaker.record_failure()
            await record_ai_usage(
                user_id=user_id,
                provider=self._provider.provider_name,
                model="chat",
                operation="chat",
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_code=e.code if hasattr(e, "code") else "AI_ERROR",
            )
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> str:
        """Non-streaming generation với retry."""
        if self._circuit_breaker.state == CircuitState.OPEN:
            raise AiTemporarilyUnavailableError()

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            start_time = time.perf_counter()
            try:
                result = await self._provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format=response_format,
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._circuit_breaker.record_success()
                await record_ai_usage(
                    user_id=user_id,
                    provider=self._provider.provider_name,
                    model="generate",
                    operation="generate",
                    input_tokens=len(prompt.split()),
                    output_tokens=len(result.split()),
                    latency_ms=latency_ms,
                    success=True,
                )
                return result

            except (AiRateLimitedError, AiTemporarilyUnavailableError) as e:
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._circuit_breaker.record_failure()
                await record_ai_usage(
                    user_id=user_id,
                    provider=self._provider.provider_name,
                    model="generate",
                    operation="generate",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    success=False,
                    error_code=e.code if hasattr(e, "code") else "AI_ERROR",
                )

                # R8: lỗi hết hạn mức - không retry
                if isinstance(e, AiRateLimitedError):
                    raise

                last_error = e
                if attempt < MAX_RETRIES - 1:
                    import asyncio

                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    await asyncio.sleep(delay)

        raise last_error or AiTemporarilyUnavailableError()
