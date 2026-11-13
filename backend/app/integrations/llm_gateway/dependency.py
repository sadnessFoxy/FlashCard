"""Process-wide gateway for the API (the worker builds its own)."""

from __future__ import annotations

from app.integrations.llm_gateway.gateway import LLMGateway

_gateway: LLMGateway | None = None


def get_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        from app.modules.ai.providers.gemini import GeminiProvider

        _gateway = LLMGateway(GeminiProvider())
    return _gateway
