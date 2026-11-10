"""
Real round trip through the backend to PostgreSQL (test DB with pgvector) and Redis.
Needs the Docker services running: `make infra-up`.
"""

from __future__ import annotations

from httpx import AsyncClient

from tests.contract_schema import assert_matches_contract


async def test_status_reaches_real_database_and_redis(client: AsyncClient) -> None:
    response = await client.get("/v1/system/status")

    assert response.status_code == 200
    body = response.json()
    assert body["checks"]["database"]["status"] == "up", body
    assert body["checks"]["database"]["pgvector_version"], body
    assert body["checks"]["redis"]["status"] == "up", body
    assert body["status"] == "ok"
    assert_matches_contract("GET", "/v1/system/status", 200, body)
