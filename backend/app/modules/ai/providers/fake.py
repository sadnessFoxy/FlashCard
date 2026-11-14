"""
Fake AI provider for tests and offline development; never calls a real API.
Embeddings are deterministic per text, and failures can be scripted per call.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppError
from app.modules.ai.providers.base import Attachment, EmbedTask, LLMProvider


class FakeProvider(LLMProvider):
    def __init__(self) -> None:
        # Errors raised by the next embed calls, in order; None means succeed.
        self.embed_script: list[AppError | None] = []
        self.embed_calls: list[list[str]] = []
        # Next chat answers, in order: a string (streamed word by word), an error raised
        # before the first token, or (partial_text, error) to fail mid-stream.
        self.chat_script: list[str | AppError | tuple[str, AppError]] = []
        self.chat_calls: list[dict[str, Any]] = []
        # Next generate results, in order: returned text, or an error to raise.
        self.generate_script: list[str | AppError] = []
        self.generate_calls: list[dict[str, Any]] = []

    @property
    def embedding_dimensions(self) -> int:
        return settings.EMBEDDING_DIMENSIONS

    @property
    def provider_name(self) -> str:
        return "fake"

    def _vector(self, text: str) -> list[float]:
        rng = random.Random(hashlib.sha256(text.encode()).digest())  # noqa: S311 - test data
        vec = [rng.gauss(0, 1) for _ in range(self.embedding_dimensions)]
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec]

    async def embed(self, texts: list[str], task: EmbedTask = "document") -> list[list[float]]:
        if self.embed_script:
            failure = self.embed_script.pop(0)
            if failure is not None:
                raise failure
        self.embed_calls.append(list(texts))
        return [self._vector(t) for t in texts]

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        self.chat_calls.append({"messages": messages, "system_prompt": system_prompt})
        step = self.chat_script.pop(0) if self.chat_script else "[FAKE] Canned answer [1]."
        if isinstance(step, AppError):
            raise step
        text, failure = (step, None) if isinstance(step, str) else step
        words = text.split(" ")
        for i, word in enumerate(words):
            yield word if i == len(words) - 1 else word + " "
        if failure is not None:
            raise failure

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
        attachment: Attachment | None = None,
    ) -> str:
        self.generate_calls.append(
            {"prompt": prompt, "system_prompt": system_prompt, "attachment": attachment}
        )
        if self.generate_script:
            step = self.generate_script.pop(0)
            if isinstance(step, AppError):
                raise step
            return step
        if response_format and response_format.get("type") == "json_object":
            return '{"result": "[FAKE] JSON response"}'
        return "[FAKE] Canned response; no real API was called."
