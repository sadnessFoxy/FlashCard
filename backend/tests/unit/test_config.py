"""CORS_ORIGINS parsing for every accepted env format."""

from __future__ import annotations

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('["http://a.test","http://b.test"]', ["http://a.test", "http://b.test"]),
        ("http://a.test, http://b.test", ["http://a.test", "http://b.test"]),
        ("http://a.test", ["http://a.test"]),
        (["http://a.test"], ["http://a.test"]),
    ],
)
def test_parse_cors_origins(raw: str | list[str], expected: list[str]) -> None:
    assert Settings.parse_cors_origins(raw) == expected


def test_rejects_unknown_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "prod")
    with pytest.raises(ValueError, match="ENVIRONMENT"):
        Settings()  # type: ignore[call-arg]
