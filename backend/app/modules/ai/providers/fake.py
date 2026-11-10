"""
Fake AI provider for tests and offline development.
Returns canned data; never calls a real API.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import settings
from app.modules.ai.providers.base import LLMProvider


class FakeProvider(LLMProvider):
    """
    Test double for LLMProvider.
    Output has the right shape but no meaning.
    """

    @property
    def embedding_dimensions(self) -> int:
        return settings.EMBEDDING_DIMENSIONS

    @property
    def provider_name(self) -> str:
        return "fake"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Random embeddings of the configured size."""
        await asyncio.sleep(0.01)  # simulate latency
        embeddings = []
        for _ in texts:
            vec = [random.gauss(0, 1) for _ in range(self.embedding_dimensions)]
            # Normalize vector (cosine similarity)
            magnitude = sum(x**2 for x in vec) ** 0.5
            normalized = [x / magnitude for x in vec]
            embeddings.append(normalized)
        return embeddings

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a canned answer word by word."""
        last_message = messages[-1]["content"] if messages else ""
        response = (
            f"[FAKE] Canned answer for: '{last_message[:50]}'. "
            "Use a real provider for real answers."
        )

        words = response.split()
        for word in words:
            await asyncio.sleep(0.05)  # simulate streaming delay
            yield word + " "

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Canned non-streaming response."""
        await asyncio.sleep(0.1)

        if response_format and response_format.get("type") == "json_object":
            return '{"result": "[FAKE] JSON response", "confidence": 0.9}'

        return (
            f"[FAKE] Canned response for: '{prompt[:50]}...'. "
            "This is FakeProvider; no real API was called."
        )
