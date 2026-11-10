"""
F2 acceptance criteria (docs/specs/f2-email-auth.md section 9) against the real test DB
and Redis. Every response is checked against the contract.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from tests.conftest import ALLOWED_ORIGIN
from tests.contract_schema import assert_response_matches_contract

pytestmark = pytest.mark.usefixtures("clean_db")

EMAIL = "learner@example.com"
PASSWORD = "correct horse battery"
NATIVE = {"X-Client-Platform": "native"}
WEB = {"X-Client-Platform": "web", "Origin": ALLOWED_ORIGIN}


async def call(client: AsyncClient, method: str, path: str, **kwargs: object) -> Response:
    response = await client.request(method, path, **kwargs)  # type: ignore[arg-type]
    assert_response_matches_contract(response)
    return response


async def register(
    client: AsyncClient, email: str = EMAIL, password: str = PASSWORD, headers: dict | None = None
) -> Response:
    return await call(
        client,
        "POST",
        "/v1/auth/register",
        json={"email": email, "password": password},
        headers=headers or NATIVE,
    )


async def login(
    client: AsyncClient, email: str = EMAIL, password: str = PASSWORD, headers: dict | None = None
) -> Response:
    return await call(
        client,
        "POST",
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers=headers or NATIVE,
    )


async def refresh(client: AsyncClient, token: str) -> Response:
    return await call(
        client, "POST", "/v1/auth/refresh", json={"refresh_token": token}, headers=NATIVE
    )


async def scalar(sql: str, **params: object) -> object:
    async with engine.connect() as conn:
        return (await conn.execute(text(sql), params)).scalar_one()


# ---------------------------------------------------------------- register


async def test_register_creates_unverified_account_with_argon2_hash(client: AsyncClient) -> None:
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == EMAIL
    assert body["user"]["email_verified"] is False
    assert body["user"]["locale"] == "vi"
    assert body["access_token"] and body["refresh_token"]
    assert body["access_token_expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    stored = await scalar("SELECT password_hash FROM users WHERE email = :e", e=EMAIL)
    assert isinstance(stored, str) and stored.startswith("$argon2id$")
    assert PASSWORD not in stored
    assert await scalar("SELECT count(*) FROM auth_identities WHERE provider = 'email'") == 1


async def test_register_normalizes_email(client: AsyncClient) -> None:
    response = await register(client, email="  An@Example.COM ")

    assert response.json()["user"]["email"] == "an@example.com"
    assert (await login(client, email="an@example.com")).status_code == 200


@pytest.mark.parametrize(
    ("password", "reason"),
    [
        ("short7!", "too_short"),
        ("x" * 129, "too_long"),
        ("Password123", "too_common"),
        ("anhyeuem123", "too_common"),
        (EMAIL, "same_as_email"),
        ("LEARNER", "too_short"),
        ("learner1", None),  # 8 chars, not common, not the local part: accepted
    ],
)
async def test_register_password_rules(
    client: AsyncClient, password: str, reason: str | None
) -> None:
    response = await register(client, password=password)

    if reason is None:
        assert response.status_code == 201
    else:
        assert response.status_code == 422
        assert response.json() == {
            "code": "WEAK_PASSWORD",
            "message": "Password does not meet the rules",
            "reason": reason,
        }
        assert await scalar("SELECT count(*) FROM users") == 0


async def test_register_rejects_password_equal_to_email_local_part(client: AsyncClient) -> None:
    response = await register(client, email="longername@example.com", password="LongerName")

    assert response.json()["reason"] == "same_as_email"


async def test_register_existing_email_is_generic_and_creates_nothing(client: AsyncClient) -> None:
    await register(client)

    response = await register(client, email=EMAIL.upper(), password="another good secret")

    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_UNAVAILABLE"
    assert await scalar("SELECT count(*) FROM users") == 1


@pytest.mark.parametrize("email", ["not-an-email", "a@", "@example.com", ""])
async def test_register_invalid_email(client: AsyncClient, email: str) -> None:
    response = await register(client, email=email)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert [e["field"] for e in response.json()["errors"]] == ["email"]
    assert email == "" or "not-an-email" not in response.text  # input is never echoed


async def test_missing_platform_header_is_validation_error(client: AsyncClient) -> None:
    response = await call(
        client, "POST", "/v1/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )

    assert response.status_code == 422
    assert {"field": "X-Client-Platform", "type": "missing"} in response.json()["errors"]


async def test_register_rate_limited_per_ip(client: AsyncClient) -> None:
    for i in range(settings.REGISTER_MAX_PER_IP):
        assert (await register(client, email=f"user{i}@example.com")).status_code == 201

    response = await register(client, email="one-more@example.com")

    assert response.status_code == 429
    assert response.json()["code"] == "TOO_MANY_ATTEMPTS"
    assert int(response.headers["Retry-After"]) == response.json()["retry_after_seconds"] > 0


# ------------------------------------------------------------------- login


async def test_login_success(client: AsyncClient) -> None:
    await register(client)

    response = await login(client, email=" Learner@Example.com")

    assert response.status_code == 200
    assert response.json()["user"]["email"] == EMAIL


async def test_wrong_password_and_unknown_email_look_identical(client: AsyncClient) -> None:
    await register(client)

    wrong_password = await login(client, password="not the password")
    unknown_email = await login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["code"] == "INVALID_CREDENTIALS"


async def test_login_blocked_after_too_many_failures_even_with_right_password(
    client: AsyncClient,
) -> None:
    await register(client)
    for _ in range(settings.LOGIN_MAX_FAILURES_PER_EMAIL):
        assert (await login(client, password="wrong password!")).status_code == 401

    response = await login(client)

    assert response.status_code == 429
    assert response.json()["code"] == "TOO_MANY_ATTEMPTS"
    assert 0 < int(response.headers["Retry-After"]) <= settings.LOGIN_FAILURE_WINDOW_SECONDS


async def test_successful_login_resets_failure_counter(client: AsyncClient) -> None:
    await register(client)
    for _ in range(settings.LOGIN_MAX_FAILURES_PER_EMAIL - 1):
        await login(client, password="wrong password!")
    assert (await login(client)).status_code == 200

    for _ in range(settings.LOGIN_MAX_FAILURES_PER_EMAIL - 1):
        await login(client, password="wrong password!")

    assert (await login(client)).status_code == 200


async def test_blocked_account_only_revealed_with_correct_password(client: AsyncClient) -> None:
    await register(client)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE users SET status = 'blocked'"))

    right = await login(client)
    wrong = await login(client, password="not the password")

    assert (right.status_code, right.json()["code"]) == (403, "ACCOUNT_BLOCKED")
    assert (wrong.status_code, wrong.json()["code"]) == (401, "INVALID_CREDENTIALS")


# ---------------------------------------------------------------- sessions


async def test_me_returns_only_the_caller(client: AsyncClient) -> None:
    alice = (await register(client, email="alice@example.com")).json()
    await register(client, email="bob@example.com")

    response = await call(
        client, "GET", "/v1/me", headers={"Authorization": f"Bearer {alice['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json() == alice["user"]
    assert "password_hash" not in response.text


@pytest.mark.parametrize("token", [None, "garbage", "Bearer-less"])
async def test_me_requires_valid_token(client: AsyncClient, token: str | None) -> None:
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    response = await call(client, "GET", "/v1/me", headers=headers)

    assert (response.status_code, response.json()["code"]) == (401, "UNAUTHORIZED")


async def test_refresh_rotates_tokens(client: AsyncClient) -> None:
    first = (await register(client)).json()

    rotated = await refresh(client, first["refresh_token"])

    assert rotated.status_code == 200
    new = rotated.json()
    assert new["refresh_token"] != first["refresh_token"]
    me = await call(
        client, "GET", "/v1/me", headers={"Authorization": f"Bearer {new['access_token']}"}
    )
    assert me.status_code == 200


async def test_reusing_rotated_token_within_grace_does_not_kill_session(
    client: AsyncClient,
) -> None:
    first = (await register(client)).json()
    new = (await refresh(client, first["refresh_token"])).json()

    reused = await refresh(client, first["refresh_token"])

    assert (reused.status_code, reused.json()["code"]) == (401, "INVALID_REFRESH_TOKEN")
    assert (await refresh(client, new["refresh_token"])).status_code == 200


async def test_reusing_rotated_token_after_grace_revokes_whole_session(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "REFRESH_REUSE_GRACE_SECONDS", 0)
    first = (await register(client)).json()
    new = (await refresh(client, first["refresh_token"])).json()

    reused = await refresh(client, first["refresh_token"])

    assert reused.status_code == 401
    assert (await refresh(client, new["refresh_token"])).status_code == 401
    assert await scalar("SELECT count(*) FROM refresh_tokens WHERE revoked_at IS NULL") == 0


async def test_other_devices_survive_a_revoked_family(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "REFRESH_REUSE_GRACE_SECONDS", 0)
    phone = (await register(client)).json()
    laptop = (await login(client)).json()
    await refresh(client, phone["refresh_token"])
    await refresh(client, phone["refresh_token"])  # theft detected on the phone's family

    assert (await refresh(client, laptop["refresh_token"])).status_code == 200


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    session = (await register(client)).json()

    out = await call(
        client,
        "POST",
        "/v1/auth/logout",
        json={"refresh_token": session["refresh_token"]},
        headers=NATIVE,
    )

    assert out.status_code == 204
    assert (await refresh(client, session["refresh_token"])).status_code == 401


async def test_logout_with_unknown_token_is_still_204(client: AsyncClient) -> None:
    out = await call(
        client, "POST", "/v1/auth/logout", json={"refresh_token": "nope"}, headers=NATIVE
    )

    assert out.status_code == 204


async def test_session_expires_after_max_lifetime(client: AsyncClient) -> None:
    session = (await register(client)).json()
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE refresh_tokens SET session_started_at = now() - interval '91 days'")
        )

    assert (await refresh(client, session["refresh_token"])).status_code == 401


async def test_refresh_of_blocked_user_is_refused(client: AsyncClient) -> None:
    session = (await register(client)).json()
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE users SET status = 'blocked'"))

    response = await refresh(client, session["refresh_token"])

    assert (response.status_code, response.json()["code"]) == (403, "ACCOUNT_BLOCKED")
    assert await scalar("SELECT count(*) FROM refresh_tokens WHERE revoked_at IS NULL") == 0


# --------------------------------------------------------------------- web


async def test_web_login_uses_httponly_cookies_only(client: AsyncClient) -> None:
    await register(client)

    response = await login(client, headers=WEB)

    assert response.status_code == 200
    body = response.json()
    assert "access_token" not in body and "refresh_token" not in body
    cookies = response.headers.get_list("set-cookie")
    access = next(c for c in cookies if c.startswith("access_token="))
    refresh_cookie = next(c for c in cookies if c.startswith("refresh_token="))
    for cookie in (access, refresh_cookie):
        assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert "Path=/v1/auth" in refresh_cookie

    me = await call(client, "GET", "/v1/me")  # cookie jar sends access_token
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL


async def test_web_refresh_and_logout_use_cookies(client: AsyncClient) -> None:
    await register(client, headers=WEB)

    rotated = await call(client, "POST", "/v1/auth/refresh", headers=WEB)
    assert rotated.status_code == 200
    assert "refresh_token" not in rotated.json()

    out = await call(client, "POST", "/v1/auth/logout", headers=WEB)
    assert out.status_code == 204
    assert all('="";' in c or "Max-Age=0" in c for c in out.headers.get_list("set-cookie"))
    client.cookies.clear()
    assert (await call(client, "POST", "/v1/auth/refresh", headers=WEB)).status_code == 401


@pytest.mark.parametrize("origin", ["https://evil.example", None])
async def test_web_requests_from_foreign_origin_are_rejected(
    client: AsyncClient, origin: str | None
) -> None:
    await register(client, headers=WEB)
    headers = {"X-Client-Platform": "web"} | ({"Origin": origin} if origin else {})

    response = await call(client, "POST", "/v1/auth/refresh", headers=headers)

    assert (response.status_code, response.json()["code"]) == (403, "CSRF_REJECTED")


async def test_native_bearer_requests_skip_origin_check(client: AsyncClient) -> None:
    session = (await register(client)).json()

    response = await call(
        client,
        "POST",
        "/v1/auth/logout",
        json={"refresh_token": session["refresh_token"]},
        headers={
            "X-Client-Platform": "native",
            "Authorization": f"Bearer {session['access_token']}",
        },
    )

    assert response.status_code == 204
