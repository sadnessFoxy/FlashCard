"""Security scenarios for F2 (docs/TESTING.md, spec f2 criteria 5 and 15)."""

from __future__ import annotations

import logging

import pytest
from httpx import AsyncClient

from app.core import security
from tests.conftest import ALLOWED_ORIGIN

pytestmark = pytest.mark.usefixtures("clean_db")

EMAIL = "secret-person@example.com"
PASSWORD = "very private passphrase"
NATIVE = {"X-Client-Platform": "native"}


async def test_logs_never_contain_email_password_or_tokens(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    creds = {"email": EMAIL, "password": PASSWORD}

    session = (await client.post("/v1/auth/register", json=creds, headers=NATIVE)).json()
    await client.post("/v1/auth/login", json=creds | {"password": "wrong!wrong!"}, headers=NATIVE)
    await client.post("/v1/auth/register", json=creds, headers=NATIVE)  # duplicate
    await client.post("/v1/auth/register", json={"email": EMAIL, "password": "x"}, headers=NATIVE)
    rotated = (
        await client.post(
            "/v1/auth/refresh", json={"refresh_token": session["refresh_token"]}, headers=NATIVE
        )
    ).json()
    await client.get("/v1/me", headers={"Authorization": f"Bearer {rotated['access_token']}"})
    await client.post(
        "/v1/auth/logout", json={"refresh_token": rotated["refresh_token"]}, headers=NATIVE
    )
    await client.post(
        "/v1/auth/login",
        json=creds,
        headers={"X-Client-Platform": "web", "Origin": ALLOWED_ORIGIN},
    )

    logged = caplog.text
    assert "signed in" in logged  # the logs we inspect are really captured
    for secret in (
        EMAIL,
        PASSWORD,
        session["access_token"],
        session["refresh_token"],
        rotated["access_token"],
        rotated["refresh_token"],
    ):
        assert secret not in logged


async def test_validation_errors_never_echo_input(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/register",
        json={"email": "bad", "password": PASSWORD, "unexpected": PASSWORD},
        headers=NATIVE,
    )

    assert response.status_code == 422
    assert PASSWORD not in response.text


def test_unknown_user_still_runs_argon2(monkeypatch: pytest.MonkeyPatch) -> None:
    """Login for an unknown email must cost the same as a wrong password."""
    calls: list[str] = []
    real = security._hasher

    class Spy:
        def verify(self, hash_: str, password: str) -> bool:
            calls.append(hash_)
            return real.verify(hash_, password)

    monkeypatch.setattr(security, "_hasher", Spy())

    assert security.verify_password(PASSWORD, None) is False
    assert calls == [security._DUMMY_HASH]
