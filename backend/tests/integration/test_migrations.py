"""Migrations apply and roll back cleanly on the test database (docs/TESTING.md)."""

from __future__ import annotations

import asyncio

from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from tests.conftest import alembic_config

AUTH_TABLES = {"users", "auth_identities", "refresh_tokens"}


def _public_tables() -> set[str]:
    async def query() -> set[str]:
        eng = create_async_engine(settings.DATABASE_URL)
        try:
            async with eng.connect() as conn:
                rows = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
                return {r[0] for r in rows}
        finally:
            await eng.dispose()

    return asyncio.run(query())


def test_upgrade_downgrade_upgrade(migrated_db: None) -> None:
    cfg = alembic_config()

    command.downgrade(cfg, "base")
    assert not (AUTH_TABLES & _public_tables())

    command.upgrade(cfg, "head")
    assert AUTH_TABLES <= _public_tables()
