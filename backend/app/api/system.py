"""
System endpoints: liveness (/health) and dependency status (/v1/system/status).

Only stable error codes are returned, never connection strings or raw errors (R10).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from app import __version__
from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.db.session import engine

logger = get_logger(__name__)

CHECK_TIMEOUT_SECONDS = 2.0

DependencyStatus = Literal["up", "down"]
CheckErrorCode = Literal["TIMEOUT", "UNREACHABLE", "EXTENSION_MISSING"]


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    environment: Literal["development", "staging", "production"]
    version: str


class DependencyCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DependencyStatus
    latency_ms: float
    error_code: CheckErrorCode | None = None


class DatabaseCheck(DependencyCheck):
    pgvector_version: str | None = None


class SystemChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database: DatabaseCheck
    redis: DependencyCheck


class SystemStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]
    version: str
    checks: SystemChecks


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _error_code(exc: BaseException) -> CheckErrorCode:
    return "TIMEOUT" if isinstance(exc, TimeoutError) else "UNREACHABLE"


async def check_database() -> DatabaseCheck:
    """Query the database and read the pgvector version."""
    started = time.perf_counter()

    async def _query() -> str | None:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
            return result.scalar_one_or_none()

    try:
        version = await asyncio.wait_for(_query(), CHECK_TIMEOUT_SECONDS)
    except Exception as exc:  # noqa: BLE001 - any failure means down
        logger.warning("Database check failed: %s", type(exc).__name__)
        return DatabaseCheck(
            status="down", latency_ms=_elapsed_ms(started), error_code=_error_code(exc)
        )

    if version is None:
        return DatabaseCheck(
            status="down", latency_ms=_elapsed_ms(started), error_code="EXTENSION_MISSING"
        )
    return DatabaseCheck(status="up", latency_ms=_elapsed_ms(started), pgvector_version=version)


async def check_redis() -> DependencyCheck:
    """PING Redis."""
    started = time.perf_counter()
    try:
        await asyncio.wait_for(get_redis().ping(), CHECK_TIMEOUT_SECONDS)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis check failed: %s", type(exc).__name__)
        return DependencyCheck(
            status="down", latency_ms=_elapsed_ms(started), error_code=_error_code(exc)
        )
    return DependencyCheck(status="up", latency_ms=_elapsed_ms(started))


DatabaseChecker = Callable[[], Awaitable[DatabaseCheck]]
RedisChecker = Callable[[], Awaitable[DependencyCheck]]


def get_database_checker() -> DatabaseChecker:
    return check_database


def get_redis_checker() -> RedisChecker:
    return check_redis


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
async def get_health() -> HealthResponse:
    """API process is up; touches no dependency."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,  # type: ignore[arg-type]  # validated in Settings
        version=__version__,
    )


@router.get(
    "/v1/system/status",
    response_model=SystemStatusResponse,
    response_model_exclude_none=False,
    operation_id="getSystemStatus",
)
async def get_system_status(
    db_checker: DatabaseChecker = Depends(get_database_checker),
    redis_checker: RedisChecker = Depends(get_redis_checker),
) -> SystemStatusResponse:
    """Check database and Redis concurrently; always 200 with per-dependency status."""
    database, redis = await asyncio.gather(db_checker(), redis_checker())
    overall: Literal["ok", "degraded"] = (
        "ok" if database.status == "up" and redis.status == "up" else "degraded"
    )
    return SystemStatusResponse(
        status=overall,
        version=__version__,
        checks=SystemChecks(database=database, redis=redis),
    )
