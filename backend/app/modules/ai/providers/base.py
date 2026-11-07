"""
Abstract base class cho AI providers.
Tuân thủ R5: mọi AI call qua providers interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class LLMProvider(ABC):
    """
    Interface chung cho các LLM provider.
    Cho phép chuyển provider chỉ bằng đổi config, không sửa code.
    """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Tạo embeddings cho danh sách văn bản.

        Args:
            texts: Danh sách văn bản cần embed

        Returns:
            Danh sách vector embedding (mỗi vector là list[float])

        Raises:
            AiTemporarilyUnavailableError: Provider không khả dụng
            AiRateLimitedError: Vượt giới hạn tốc độ
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
        Sinh văn bản theo kiểu streaming (Server-Sent Events).

        Args:
            messages: Lịch sử hội thoại theo format [{role, content}]
            system_prompt: System prompt (không đưa thông tin định danh người dùng)
            max_tokens: Giới hạn số token đầu ra
            temperature: Độ ngẫu nhiên (0.0 - 1.0)

        Yields:
            Từng chunk văn bản

        Raises:
            AiTemporarilyUnavailableError: Provider không khả dụng
            AiRateLimitedError: Vượt giới hạn tốc độ
            ContextTooLongError: Context vượt quá giới hạn
        """
        ...
        yield ""  # type: ignore[misc]  # Satisfy abstract generator typing

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """
        Sinh văn bản không streaming (cho các tác vụ cần kết quả đầy đủ).

        Args:
            prompt: Prompt đầu vào
            system_prompt: System prompt
            max_tokens: Giới hạn số token đầu ra
            temperature: Độ ngẫu nhiên
            response_format: Định dạng đầu ra (ví dụ {"type": "json_object"})

        Returns:
            Văn bản được sinh ra

        Raises:
            AiTemporarilyUnavailableError: Provider không khả dụng
            AiRateLimitedError: Vượt giới hạn tốc độ
        """
        ...

    @property
    @abstractmethod
    def embedding_dimensions(self) -> int:
        """Số chiều của vector embedding."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Tên nhà cung cấp (cho logging và metrics)."""
        ...
