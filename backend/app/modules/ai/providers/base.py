"""
Abstract base class for AI providers.
R5: all AI calls go through this provider interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Literal

EmbedTask = Literal["document", "query"]


@dataclass(frozen=True)
class Attachment:
    """A file the model reads along with the prompt (e.g. one scanned PDF page)."""

    data: bytes
    mime_type: str


class LLMProvider(ABC):
    """
    Common interface for LLM providers;
    switching providers is a config change.
    """

    @abstractmethod
    async def embed(self, texts: list[str], task: EmbedTask = "document") -> list[list[float]]:
        """
        Embed a list of texts.

        Args:
            texts: texts to embed
            task: "document" for stored chunks, "query" for search queries

        Returns:
            One vector (list[float]) per text

        Raises:
            AiTemporarilyUnavailableError: provider unavailable
            AiRateLimitedError: per-minute limit hit (retry later)
            AiQuotaExhaustedError: daily quota or billing exhausted (do not retry)
        """
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream generated text.

        Args:
            messages: conversation as [{role, content}]
            system_prompt: system prompt (no user-identifying data)
            max_tokens: output token cap
            temperature: randomness (0.0 - 1.0)

        Yields:
            Text chunks

        Raises:
            AiTemporarilyUnavailableError: provider unavailable
            AiRateLimitedError: rate limit hit
            ContextTooLongError: context too long
        """
        ...
        yield ""  # makes this an async generator

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
        attachment: Attachment | None = None,
    ) -> str:
        """
        Generate text without streaming (when the full result is needed).

        Args:
            prompt: input prompt
            system_prompt: System prompt
            max_tokens: output token cap
            temperature: randomness
            response_format: output format, e.g. {"type": "json_object"}
            attachment: a file the model reads with the prompt (scanned pages)

        Returns:
            Generated text

        Raises:
            AiTemporarilyUnavailableError: provider unavailable
            AiRateLimitedError: rate limit hit
        """
        ...

    @property
    @abstractmethod
    def embedding_dimensions(self) -> int:
        """Embedding vector size."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name for logs and metrics."""
        ...
