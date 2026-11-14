"""The Gemini request carries an attached file inline, before the prompt (F14)."""

from __future__ import annotations

import base64
import json

import httpx

from app.modules.ai.providers.base import Attachment
from app.modules.ai.providers.gemini import GeminiProvider


async def test_generate_sends_the_attachment_inline() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["key_in_url"] = "key=" in str(request.url)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    provider = GeminiProvider()
    provider._client = httpx.AsyncClient(  # noqa: SLF001 - swap the network for a stub
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )

    text = await provider.generate(
        "Transcribe this page.", attachment=Attachment(b"%PDF-1", "application/pdf")
    )

    assert text == "ok"
    parts = seen["body"]["contents"][0]["parts"]  # type: ignore[index]
    assert parts[0] == {
        "inline_data": {
            "mime_type": "application/pdf",
            "data": base64.b64encode(b"%PDF-1").decode(),
        }
    }
    assert parts[1] == {"text": "Transcribe this page."}
    assert seen["key_in_url"] is False
    await provider.close()
