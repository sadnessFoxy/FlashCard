"""
Pytest fixtures dùng chung cho toàn bộ test suite.

R11: test KHÔNG dùng database của môi trường phát triển hay production. DATABASE_URL bị ép
sang database test (mặc định `flashcard_test` trên Postgres local của Docker Compose),
đổi bằng biến TEST_DATABASE_URL (CI dùng biến này).
Khóa Gemini bị ép thành giá trị giả để test không bao giờ gọi API thật bằng khóa thật.

Các biến phải được đặt TRƯỚC khi import `app`, vì Settings đọc cấu hình lúc import.
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://flashcard:flashcard@localhost:5432/flashcard_test",
)
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
os.environ["GEMINI_API_KEY"] = "test-fake-key"
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ["ENVIRONMENT"] = "development"

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.redis import close_redis  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.integrations.llm_gateway.gateway import LLMGateway  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.ai.providers.fake import FakeProvider  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _reset_connections() -> AsyncGenerator[None, None]:
    """Mỗi test có event loop riêng: đóng pool database và Redis sau mỗi test
    để không dùng lại kết nối thuộc loop đã đóng."""
    yield
    app.dependency_overrides.clear()
    await engine.dispose()
    await close_redis()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client gọi thẳng vào app (không mở cổng mạng)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fake_llm_gateway() -> LLMGateway:
    """LLM Gateway dùng FakeProvider - không gọi API thật."""
    return LLMGateway(provider=FakeProvider())
