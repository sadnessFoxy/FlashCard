"""F3 acceptance criteria (docs/specs/f3-google.md section 9)."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select, update

from app.core.exceptions import InvalidGoogleTokenError
from app.db.session import AsyncSessionLocal
from app.main import app
from app.modules.auth.google import GoogleIdentity, get_google_verifier
from app.modules.auth.models import AuthIdentity
from app.modules.users.models import User
from tests.contract_schema import assert_response_matches_contract

pytestmark = pytest.mark.usefixtures("clean_db")

NATIVE = {"X-Client-Platform": "native"}


class FakeVerifier:
    """Token string -> identity, as if Google had signed it."""

    def __init__(self, identities: dict[str, GoogleIdentity]) -> None:
        self._identities = identities

    async def verify(self, id_token: str) -> GoogleIdentity:
        if id_token not in self._identities:
            raise InvalidGoogleTokenError()
        return self._identities[id_token]


def use(identities: dict[str, GoogleIdentity]) -> None:
    app.dependency_overrides[get_google_verifier] = lambda: FakeVerifier(identities)


GOOD = GoogleIdentity("google-1", "Learner@Gmail.com", email_verified=True)
UNVERIFIED = GoogleIdentity("google-2", "owner@example.com", email_verified=False)


async def google(client: AsyncClient, token: str, **extra: Any) -> Response:
    response = await client.post(
        "/v1/auth/google", json={"id_token": token, **extra}, headers=NATIVE
    )
    assert_response_matches_contract(response)
    return response


async def identities_of(email: str) -> list[str]:
    async with AsyncSessionLocal() as s:
        rows = await s.execute(
            select(AuthIdentity.provider)
            .join(User, User.id == AuthIdentity.user_id)
            .where(User.email == email)
        )
        return sorted(rows.scalars())


# 1. First sign-in creates a verified account without a password; the next one signs in.
async def test_first_sign_in_creates_an_account(client: AsyncClient) -> None:
    use({"good": GOOD})

    first = await google(client, "good", locale="en")

    assert first.status_code == 200
    body = first.json()
    assert body["user"]["email"] == "learner@gmail.com" and body["user"]["email_verified"] is True
    assert body["user"]["locale"] == "en" and body["access_token"] and body["refresh_token"]
    again = await google(client, "good")
    assert again.json()["user"]["id"] == body["user"]["id"]
    assert await identities_of("learner@gmail.com") == ["google"]
    me = await client.get(
        "/v1/me", headers={"Authorization": f"Bearer {again.json()['access_token']}"}
    )
    assert me.status_code == 200


# 2. A verified Google email joins the existing email account.
async def test_verified_google_links_existing_account(client: AsyncClient) -> None:
    await client.post(
        "/v1/auth/register",
        json={"email": "learner@gmail.com", "password": "a long enough passphrase"},
        headers=NATIVE,
    )
    use({"good": GOOD})

    response = await google(client, "good")

    assert response.status_code == 200
    assert await identities_of("learner@gmail.com") == ["email", "google"]
    assert response.json()["user"]["email_verified"] is True


# 3. An unverified Google email never takes over an existing account.
async def test_unverified_google_cannot_take_over(client: AsyncClient) -> None:
    await client.post(
        "/v1/auth/register",
        json={"email": "owner@example.com", "password": "a long enough passphrase"},
        headers=NATIVE,
    )
    use({"unverified": UNVERIFIED})

    response = await google(client, "unverified")

    assert response.status_code == 409 and response.json()["code"] == "GOOGLE_LINK_REQUIRED"
    assert await identities_of("owner@example.com") == ["email"]


# 4. Invalid tokens, blocked accounts, Google not set up.
async def test_errors(client: AsyncClient) -> None:
    not_configured = await google(client, "anything")
    assert (
        not_configured.status_code == 503
        and not_configured.json()["code"] == "GOOGLE_NOT_CONFIGURED"
    )

    use({"good": GOOD})
    invalid = await google(client, "forged")
    assert invalid.status_code == 401 and invalid.json()["code"] == "INVALID_GOOGLE_TOKEN"

    await google(client, "good")
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(User).where(User.email == "learner@gmail.com").values(status="blocked")
        )
        await s.commit()
    blocked = await google(client, "good")
    assert blocked.status_code == 403 and blocked.json()["code"] == "ACCOUNT_BLOCKED"


# 5. Web gets httpOnly cookies, never tokens in the body (R12).
async def test_web_gets_cookies(client: AsyncClient) -> None:
    use({"good": GOOD})
    response = await client.post(
        "/v1/auth/google",
        json={"id_token": "good"},
        headers={"X-Client-Platform": "web", "Origin": "http://localhost:8081"},
    )
    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert "httponly" in " ".join(response.headers.get_list("set-cookie")).lower()
