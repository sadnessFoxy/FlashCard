"""
Shared fixtures.

R11: tests never touch the dev or prod database. DATABASE_URL is forced to the test
database (`flashcard_test`, or TEST_DATABASE_URL in CI) and Redis to db 15.
The Gemini key is forced to a fake value so tests can never call the real API.
Env vars must be set before `app` is imported: Settings reads them at import time.
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
os.environ["CORS_ORIGINS"] = '["http://localhost:8081"]'
os.environ["SQL_ECHO"] = "false"
os.environ["S3_BUCKET_NAME"] = "flashcard-test"  # never the dev bucket

from collections.abc import AsyncGenerator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.redis import close_redis, get_redis  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.integrations.llm_gateway.gateway import LLMGateway  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.ai.providers.fake import FakeProvider  # noqa: E402

ALLOWED_ORIGIN = "http://localhost:8081"
BACKEND_DIR = Path(__file__).resolve().parents[1]
_TABLES = (
    "ai_usage",
    "user_consents",
    "document_jobs",
    "document_chunks",
    "documents",
    "spaces",
    "refresh_tokens",
    "auth_identities",
    "users",
)


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "app" / "db" / "migrations"))
    return cfg


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Bring the test database to the latest migration once per run."""
    command.upgrade(alembic_config(), "head")


@pytest_asyncio.fixture
async def clean_db(migrated_db: None) -> AsyncGenerator[None, None]:
    """Empty tables and the test Redis db before each test that needs real state."""
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    await get_redis().flushdb()
    yield


@pytest_asyncio.fixture(autouse=True)
async def _reset_connections() -> AsyncGenerator[None, None]:
    """Each test has its own event loop, so drop pooled connections afterwards."""
    yield
    app.dependency_overrides.clear()
    await engine.dispose()
    await close_redis()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """In-process HTTP client (no network port)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fake_llm_gateway() -> LLMGateway:
    return LLMGateway(provider=FakeProvider())
