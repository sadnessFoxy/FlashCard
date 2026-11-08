"""
Endpoint hệ thống với các phụ thuộc giả lập (không cần Docker).
Mọi response đều được kiểm tra theo schema trong contract.
"""

from __future__ import annotations

from httpx import AsyncClient

from app import __version__
from app.api.system import (
    DatabaseCheck,
    DependencyCheck,
    get_database_checker,
    get_redis_checker,
)
from app.main import app
from tests.contract_schema import assert_matches_contract

STATUS_PATH = "/v1/system/status"


def _override(database: DatabaseCheck, redis: DependencyCheck) -> None:
    async def fake_db() -> DatabaseCheck:
        return database

    async def fake_redis() -> DependencyCheck:
        return redis

    app.dependency_overrides[get_database_checker] = lambda: fake_db
    app.dependency_overrides[get_redis_checker] = lambda: fake_redis


DB_UP = DatabaseCheck(status="up", latency_ms=1.5, pgvector_version="0.8.7")
REDIS_UP = DependencyCheck(status="up", latency_ms=0.4)


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "environment": "development", "version": __version__}
    assert_matches_contract("GET", "/health", 200, body)


async def test_status_ok_when_all_dependencies_up(client: AsyncClient) -> None:
    _override(DB_UP, REDIS_UP)

    response = await client.get(STATUS_PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["pgvector_version"] == "0.8.7"
    assert_matches_contract("GET", STATUS_PATH, 200, body)


async def test_status_degraded_when_database_down(client: AsyncClient) -> None:
    _override(DatabaseCheck(status="down", latency_ms=2000, error_code="TIMEOUT"), REDIS_UP)

    response = await client.get(STATUS_PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == {
        "status": "down",
        "latency_ms": 2000,
        "error_code": "TIMEOUT",
        "pgvector_version": None,
    }
    assert_matches_contract("GET", STATUS_PATH, 200, body)


async def test_status_degraded_when_redis_down(client: AsyncClient) -> None:
    _override(DB_UP, DependencyCheck(status="down", latency_ms=3, error_code="UNREACHABLE"))

    response = await client.get(STATUS_PATH)

    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["redis"]["error_code"] == "UNREACHABLE"
    assert_matches_contract("GET", STATUS_PATH, 200, body)


async def test_status_degraded_when_pgvector_missing(client: AsyncClient) -> None:
    _override(DatabaseCheck(status="down", latency_ms=1, error_code="EXTENSION_MISSING"), REDIS_UP)

    body = (await client.get(STATUS_PATH)).json()

    assert body["status"] == "degraded"
    assert_matches_contract("GET", STATUS_PATH, 200, body)


async def test_status_does_not_leak_connection_details(client: AsyncClient) -> None:
    _override(DatabaseCheck(status="down", latency_ms=1, error_code="UNREACHABLE"), REDIS_UP)

    text = (await client.get(STATUS_PATH)).text

    for secret_fragment in ("postgresql", "asyncpg", "redis://", "password", "flashcard:"):
        assert secret_fragment not in text
