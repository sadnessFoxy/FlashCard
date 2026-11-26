"""List settings (CORS_ORIGINS, GOOGLE_CLIENT_IDS) in every accepted env format."""

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
    assert Settings.parse_string_list(raw) == expected


def test_rejects_unknown_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "prod")
    with pytest.raises(ValueError, match="ENVIRONMENT"):
        Settings()  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("https://app.example.com", ["https://app.example.com"]),
        (
            "a.apps.googleusercontent.com,b.apps.googleusercontent.com",
            ["a.apps.googleusercontent.com", "b.apps.googleusercontent.com"],
        ),
        ('["https://app.example.com"]', ["https://app.example.com"]),
    ],
)
def test_list_settings_from_env(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    # Through the real env source: values are not required to be JSON.
    monkeypatch.setenv("CORS_ORIGINS", raw)
    monkeypatch.setenv("GOOGLE_CLIENT_IDS", raw)
    loaded = Settings()  # type: ignore[call-arg]
    assert loaded.CORS_ORIGINS == expected and loaded.GOOGLE_CLIENT_IDS == expected
