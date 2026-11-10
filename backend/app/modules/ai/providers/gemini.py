"""
Google Gemini AI provider.
R5: API key, model names and dimensions come from settings.
R3: GEMINI_API_KEY is never hard-coded or committed.
R10: never log document content or personal data.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
    ContextTooLongError,
)
from app.core.logging import get_logger
from app.modules.ai.providers.base import LLMProvider

logger = get_logger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com"
GEMINI_API_VERSION = "v1beta"


class GeminiProvider(LLMProvider):
    """
    Gemini API provider (free tier).
    Moving to a paid tier only needs a new GEMINI_API_KEY and model config.
    """

    def __init__(self) -> None:
        # Key and model names come from config
        self._api_key = settings.GEMINI_API_KEY
        self._chat_model = settings.GEMINI_CHAT_MODEL
        self._embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self._embedding_dims = settings.EMBEDDING_DIMENSIONS

        self._client = httpx.AsyncClient(
            base_url=GEMINI_API_BASE,
            timeout=httpx.Timeout(60.0, connect=10.0),
            # Key travels in a header, not the URL, so it never lands in logs (R10)
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
        )

    @property
    def embedding_dimensions(self) -> int:
        return self._embedding_dims

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _handle_error_response(self, status_code: int, response_body: dict[str, Any]) -> None:
        """Map a Gemini error response to our exceptions."""
        error = response_body.get("error", {})
        error_code = error.get("code", status_code)
        error_status = error.get("status", "")

        # R8: quota exhausted, do not retry
        if error_code == 429 or error_status in ("RESOURCE_EXHAUSTED",):
            logger.warning(
                "Gemini API rate limit exceeded (model=%s)",
                self._chat_model,
            )
            raise AiRateLimitedError()

        # Context too long
        if error_status == "INVALID_ARGUMENT" and "too long" in str(error).lower():
            raise ContextTooLongError()

        # Transient (5xx): retryable
        if error_code >= 500:
            logger.warning(
                "Gemini API server error (status=%d, model=%s)",
                error_code,
                self._chat_model,
            )
            raise AiTemporarilyUnavailableError()

        # Unknown error
        logger.error(
            "Gemini API unexpected error (status=%d, body=%s)",
            status_code,
            # Never log prompt or document content (R10)
            {k: v for k, v in error.items() if k in ("code", "status", "message")},
        )
        raise AiTemporarilyUnavailableError()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with the configured Gemini embedding model."""
        model_path = f"models/{self._embedding_model}"
        url = f"/{GEMINI_API_VERSION}/{model_path}:batchEmbedContents"

        requests = [
            {
                "model": model_path,
                "content": {"parts": [{"text": text}]},
                "taskType": "RETRIEVAL_DOCUMENT",
                # Required: Gemini defaults to 3072 dims otherwise (R5: from config)
                "outputDimensionality": self._embedding_dims,
            }
            for text in texts
        ]

        try:
            response = await self._client.post(
                url,
                json={"requests": requests},
            )
        except httpx.TimeoutException as e:
            logger.warning("Gemini embed request timed out")
            raise AiTemporarilyUnavailableError() from e
        except httpx.NetworkError as e:
            logger.warning("Gemini embed network error: %s", type(e).__name__)
            raise AiTemporarilyUnavailableError() from e

        if response.status_code != 200:
            self._handle_error_response(response.status_code, response.json())

        data = response.json()
        embeddings = [embedding["values"] for embedding in data.get("embeddings", [])]

        logger.debug(
            "Embedded %d texts (model=%s, dims=%d)",
            len(texts),
            self._embedding_model,
            self._embedding_dims,
        )

        return embeddings

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat via streamGenerateContent."""
        url = f"/{GEMINI_API_VERSION}/models/{self._chat_model}:streamGenerateContent"

        # Convert messages to Gemini's format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                {
                    "role": role,
                    "parts": [{"text": msg["content"]}],
                }
            )

        request_body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }

        if system_prompt:
            request_body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        if max_tokens:
            request_body["generationConfig"]["maxOutputTokens"] = max_tokens

        try:
            async with self._client.stream(
                "POST",
                url,
                json=request_body,
                params={"alt": "sse"},
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    self._handle_error_response(response.status_code, json.loads(body))

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_data = line[6:]
                        if chunk_data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(chunk_data)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException as e:
            logger.warning("Gemini stream timed out (model=%s)", self._chat_model)
            raise AiTemporarilyUnavailableError() from e
        except httpx.NetworkError as e:
            logger.warning("Gemini stream network error: %s", type(e).__name__)
            raise AiTemporarilyUnavailableError() from e

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Non-streaming generation."""
        url = f"/{GEMINI_API_VERSION}/models/{self._chat_model}:generateContent"

        request_body: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }

        if system_prompt:
            request_body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        if max_tokens:
            request_body["generationConfig"]["maxOutputTokens"] = max_tokens

        if response_format and response_format.get("type") == "json_object":
            request_body["generationConfig"]["responseMimeType"] = "application/json"

        try:
            response = await self._client.post(
                url,
                json=request_body,
            )
        except httpx.TimeoutException as e:
            logger.warning("Gemini generate timed out (model=%s)", self._chat_model)
            raise AiTemporarilyUnavailableError() from e
        except httpx.NetworkError as e:
            logger.warning("Gemini generate network error: %s", type(e).__name__)
            raise AiTemporarilyUnavailableError() from e

        if response.status_code != 200:
            self._handle_error_response(response.status_code, response.json())

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise AiTemporarilyUnavailableError()

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts)

        # Log usage only, never content (R10)
        usage = data.get("usageMetadata", {})
        logger.debug(
            "Gemini generate usage (model=%s, input_tokens=%d, output_tokens=%d)",
            self._chat_model,
            usage.get("promptTokenCount", 0),
            usage.get("candidatesTokenCount", 0),
        )

        return text

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
