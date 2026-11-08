"""Cách các hàm kiểm tra phụ thuộc phân loại lỗi (không cần Docker)."""

from __future__ import annotations

from types import TracebackType
from typing import Any

import pytest

from app.api import system


class _FailingEngine:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def connect(self) -> _FailingEngine:
        return self

    async def __aenter__(self) -> Any:
        raise self._exc

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


class _FailingRedis:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def ping(self) -> bool:
        raise self._exc


@pytest.mark.parametrize(
    ("exc", "expected"),
    [(OSError("connection refused"), "UNREACHABLE"), (TimeoutError(), "TIMEOUT")],
)
async def test_database_check_maps_errors(
    monkeypatch: pytest.MonkeyPatch, exc: BaseException, expected: str
) -> None:
    monkeypatch.setattr(system, "engine", _FailingEngine(exc))

    result = await system.check_database()

    assert result.status == "down"
    assert result.error_code == expected
    assert result.pgvector_version is None


@pytest.mark.parametrize(
    ("exc", "expected"),
    [(ConnectionError("refused"), "UNREACHABLE"), (TimeoutError(), "TIMEOUT")],
)
async def test_redis_check_maps_errors(
    monkeypatch: pytest.MonkeyPatch, exc: BaseException, expected: str
) -> None:
    monkeypatch.setattr(system, "get_redis", lambda: _FailingRedis(exc))

    result = await system.check_redis()

    assert result.status == "down"
    assert result.error_code == expected
