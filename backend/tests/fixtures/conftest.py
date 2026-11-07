"""
Pytest fixtures dùng chung cho toàn bộ test suite.
Tuân thủ R11: không dùng database production để test.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.main import app
from app.modules.ai.providers.fake import FakeProvider
from app.integrations.llm_gateway.gateway import LLMGateway

# Database test: dùng SQLite in-memory hoặc PostgreSQL test riêng
# Không dùng DATABASE_URL production (R11)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Single event loop cho toàn bộ test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[Any, None]:
    """Engine kết nối database test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Database session mới cho mỗi test, rollback sau khi xong."""
    async_session = async_sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fake_llm_gateway() -> LLMGateway:
    """LLM Gateway dùng FakeProvider - không gọi API thật."""
    provider = FakeProvider()
    return LLMGateway(provider=provider)
