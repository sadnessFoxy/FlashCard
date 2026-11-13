"""
LLM gateway: the single entry point for AI calls (R5).

Retry policy (docs/QUOTA_AND_RESILIENCE.md):
- AiRateLimitedError (per-minute limit): wait retry_after (capped), retry; not a provider failure
- AiQuotaExhaustedError (daily quota, billing, bad key): trip the breaker, never retry (R8)
- AiTemporarilyUnavailableError (network, 5xx): up to MAX_TRANSIENT_ATTEMPTS with backoff
- Breaker open: fail fast with AiCircuitOpenError
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any, TypeVar

from app.core.config import settings
from app.core.exceptions import (
    AiCircuitOpenError,
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
)
from app.core.logging import get_logger
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker, CircuitState
from app.modules.ai.providers.base import EmbedTask, LLMProvider
from app.modules.ai.usage import UsageRecorder, estimate_tokens, record_ai_usage

logger = get_logger(__name__)

MAX_TRANSIENT_ATTEMPTS = 3
MAX_RATE_LIMIT_WAITS = 5
BACKOFF_SECONDS = [1.0, 2.0, 4.0]

T = TypeVar("T")
Sleep = Callable[[float], Awaitable[None]]


class LLMGateway:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        breaker: CircuitBreaker | None = None,
        sleep: Sleep = asyncio.sleep,
        recorder: UsageRecorder = record_ai_usage,
    ) -> None:
        self._provider = provider
        self._breaker = breaker or CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        self._sleep = sleep
        self._record = recorder

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    async def _call(
        self,
        operation: str,
        user_id: str | None,
        input_tokens: int,
        fn: Callable[[], Awaitable[T]],
        output_tokens: Callable[[T], int] = lambda _: 0,
    ) -> T:
        transient_failures = 0
        rate_limit_waits = 0
        while True:
            if self._breaker.state == CircuitState.OPEN:
                raise AiCircuitOpenError()
            started = time.perf_counter()
            try:
                result = await fn()
            except AiRateLimitedError as exc:
                await self._log(operation, user_id, started, False, exc.code)
                rate_limit_waits += 1
                if rate_limit_waits > MAX_RATE_LIMIT_WAITS:
                    raise
                wait = min(
                    exc.retry_after_seconds or BACKOFF_SECONDS[-1],
                    float(settings.AI_RATE_LIMIT_MAX_WAIT_SECONDS),
                )
                logger.info("AI rate limited (%s), waiting %.1fs", operation, wait)
                await self._sleep(wait)
                continue
            except AiQuotaExhaustedError as exc:
                await self._log(operation, user_id, started, False, "AI_QUOTA_EXHAUSTED")
                self._breaker.trip()
                raise exc
            except AiTemporarilyUnavailableError as exc:
                await self._log(operation, user_id, started, False, exc.code)
                self._breaker.record_failure()
                transient_failures += 1
                if transient_failures >= MAX_TRANSIENT_ATTEMPTS:
                    raise
                delay = BACKOFF_SECONDS[min(transient_failures - 1, len(BACKOFF_SECONDS) - 1)]
                logger.warning(
                    "AI call failed (%s, attempt %d/%d), retrying in %.1fs",
                    operation,
                    transient_failures,
                    MAX_TRANSIENT_ATTEMPTS,
                    delay,
                )
                await self._sleep(delay)
                continue
            self._breaker.record_success()
            await self._log(
                operation, user_id, started, True, None, input_tokens, output_tokens(result)
            )
            return result

    async def _log(
        self,
        operation: str,
        user_id: str | None,
        started: float,
        success: bool,
        error_code: str | None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        await self._record(
            user_id=user_id,
            provider=self._provider.provider_name,
            model=self._model_for(operation),
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=(time.perf_counter() - started) * 1000,
            success=success,
            error_code=error_code,
        )

    @staticmethod
    def _model_for(operation: str) -> str:
        return (
            settings.GEMINI_EMBEDDING_MODEL if operation == "embed" else settings.GEMINI_CHAT_MODEL
        )

    async def embed(
        self, texts: list[str], task: EmbedTask = "document", user_id: str | None = None
    ) -> list[list[float]]:
        return await self._call(
            "embed",
            user_id,
            sum(estimate_tokens(t) for t in texts),
            lambda: self._provider.embed(texts, task),
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> str:
        return await self._call(
            "generate",
            user_id,
            estimate_tokens(prompt) + estimate_tokens(system_prompt or ""),
            lambda: self._provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
            ),
            output_tokens=estimate_tokens,
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        user_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming is not retried mid-stream; errors surface to the caller (F7)."""
        if self._breaker.state == CircuitState.OPEN:
            raise AiCircuitOpenError()
        started = time.perf_counter()
        produced: list[str] = []
        try:
            async for chunk in self._provider.chat_stream(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            ):
                produced.append(chunk)
                yield chunk
        except AiQuotaExhaustedError:
            self._breaker.trip()
            await self._log("chat", user_id, started, False, "AI_QUOTA_EXHAUSTED")
            raise
        except (AiRateLimitedError, AiTemporarilyUnavailableError) as exc:
            self._breaker.record_failure()
            await self._log("chat", user_id, started, False, exc.code)
            raise
        self._breaker.record_success()
        await self._log(
            "chat",
            user_id,
            started,
            True,
            None,
            sum(estimate_tokens(m["content"]) for m in messages),
            estimate_tokens("".join(produced)),
        )
