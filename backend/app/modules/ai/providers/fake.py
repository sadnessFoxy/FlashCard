"""
Fake AI provider cho unit test và development offline.
Trả về dữ liệu giả định không gọi API thật.
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
    Provider giả lập cho test.
    Trả về dữ liệu có cấu trúc đúng nhưng không có nghĩa.
    """

    @property
    def embedding_dimensions(self) -> int:
        return settings.EMBEDDING_DIMENSIONS

    @property
    def provider_name(self) -> str:
        return "fake"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Tạo random embeddings có đúng số chiều."""
        await asyncio.sleep(0.01)  # Giả lập latency nhỏ
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
        """Giả lập streaming response từng từ."""
        last_message = messages[-1]["content"] if messages else ""
        response = (
            f"[FAKE] Đây là câu trả lời giả lập cho câu hỏi: '{last_message[:50]}'. "
            "Dùng provider thật để có câu trả lời thực sự."
        )

        words = response.split()
        for word in words:
            await asyncio.sleep(0.05)  # Giả lập streaming delay
            yield word + " "

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Giả lập non-streaming response."""
        await asyncio.sleep(0.1)

        if response_format and response_format.get("type") == "json_object":
            return '{"result": "[FAKE] JSON response", "confidence": 0.9}'

        return (
            f"[FAKE] Phản hồi giả lập cho prompt: '{prompt[:50]}...'. "
            "Đây là FakeProvider dùng cho test, không gọi API thật."
        )
