"""F4 acceptance criteria (docs/specs/f4-email-codes.md section 9)."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select

from app.core.config import settings
from app.core.redis import get_redis
from app.db.session import AsyncSessionLocal
from app.integrations.object_storage import get_storage
from app.main import app
from app.modules.auth.models import AuthCode
from app.modules.documents.queue import get_job_queue
from app.modules.users.service import UserService
from tests.api.test_documents import PDF, consent, new_space, sign_up, upload
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.fakes import InMemoryStorage, RecordingMailer, RecordingQueue

pytestmark = pytest.mark.usefixtures("clean_db")

EMAIL = "learner@example.com"
PASSWORD = "a long enough passphrase"
NATIVE = {"X-Client-Platform": "native"}


async def post(
    client: AsyncClient, url: str, auth: dict[str, str] | None = None, **kw: Any
) -> Response:
    response = await client.post(url, headers={**NATIVE, **(auth or {})}, **kw)
    assert_response_matches_contract(response)
    return response


async def register(client: AsyncClient) -> tuple[dict[str, str], str]:
    body = (
        await post(client, "/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["refresh_token"]


async def me(client: AsyncClient, auth: dict[str, str]) -> dict[str, Any]:
    return (await client.get("/v1/me", headers=auth)).json()  # type: ignore[no-any-return]


async def confirm(client: AsyncClient, auth: dict[str, str], code: str) -> Response:
    return await post(client, "/v1/auth/email-verification/confirm", auth, json={"code": code})


async def forgot(client: AsyncClient, email: str = EMAIL) -> Response:
    return await post(client, "/v1/auth/password-reset", json={"email": email})


async def reset(
    client: AsyncClient, code: str, new_password: str = "a brand new passphrase"
) -> Response:
    return await post(
        client,
        "/v1/auth/password-reset/confirm",
        json={"email": EMAIL, "code": code, "new_password": new_password},
    )


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"


# 1. Registration emails a code; entering it verifies the email.
async def test_registration_sends_a_code_that_verifies(
    client: AsyncClient, mailer: RecordingMailer
) -> None:
    auth, _ = await register(client)
    code = mailer.last_code(EMAIL)
    assert (await me(client, auth))["email_verified"] is False

    response = await confirm(client, auth, f" {code} ")

    assert response.status_code == 200 and response.json()["email_verified"] is True
    assert (await confirm(client, auth, code)).status_code == 200  # already verified: no-op


# 2. Wrong codes are rejected and kill the code after the allowed tries.
async def test_wrong_codes_and_attempt_limit(client: AsyncClient, mailer: RecordingMailer) -> None:
    auth, _ = await register(client)
    code = mailer.last_code(EMAIL)

    for _ in range(settings.AUTH_CODE_MAX_ATTEMPTS):
        response = await confirm(client, auth, wrong(code))
        assert response.status_code == 400 and response.json()["code"] == "INVALID_CODE"

    assert (await confirm(client, auth, code)).status_code == 400  # the right code is dead now
    assert (await confirm(client, auth, "12ab56")).status_code == 422


# 3. Resending retires the old code and is rate limited.
async def test_resend_replaces_code_and_is_limited(
    client: AsyncClient, mailer: RecordingMailer
) -> None:
    auth, _ = await register(client)
    first = mailer.last_code(EMAIL)

    response = await post(client, "/v1/auth/email-verification", auth)
    assert response.status_code == 429  # registration just sent one
    assert response.json()["code"] == "TOO_MANY_ATTEMPTS"

    await get_redis().flushdb()  # pretend the minute passed
    assert (await post(client, "/v1/auth/email-verification", auth)).status_code == 204
    second = mailer.last_code(EMAIL)
    if second != first:
        assert (await confirm(client, auth, first)).status_code == 400
    assert (await confirm(client, auth, second)).status_code == 200


# 4. Unverified accounts cannot upload; verified ones can.
async def test_upload_requires_verified_email(client: AsyncClient, mailer: RecordingMailer) -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_job_queue] = lambda: queue
    auth = await sign_up(client, EMAIL, verified=False)
    await consent(client, auth)
    space = await new_space(client, auth)

    response = await upload(client, auth, PDF, space_id=space)
    assert response.status_code == 403 and response.json()["code"] == "EMAIL_NOT_VERIFIED"

    await confirm(client, auth, mailer.last_code(EMAIL))
    assert (await upload(client, auth, PDF, space_id=space)).status_code == 202


# 5. Forgot password answers the same for known and unknown emails.
async def test_forgot_password_does_not_reveal_accounts(
    client: AsyncClient, mailer: RecordingMailer
) -> None:
    await register(client)
    sent_before = len(mailer.sent)

    unknown = await forgot(client, "nobody@example.com")
    known = await forgot(client)

    assert unknown.status_code == known.status_code == 202
    assert unknown.content == known.content == b""
    assert len(mailer.sent) == sent_before + 1  # only the real account got an email
    assert mailer.sent[-1].to == EMAIL


# 6. Resetting changes the password, signs out every session and verifies the email.
async def test_reset_password(client: AsyncClient, mailer: RecordingMailer) -> None:
    auth, refresh_token = await register(client)
    await forgot(client)
    code = mailer.last_code(EMAIL)

    weak = await reset(client, code, "short")
    assert weak.status_code == 422 and weak.json()["code"] == "WEAK_PASSWORD"
    assert (await reset(client, wrong(code))).status_code == 400
    assert (await reset(client, code)).status_code == 204
    assert (await reset(client, code)).status_code == 400  # single use

    refreshed = await post(client, "/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 401
    old = await post(client, "/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert old.status_code == 401
    new = await post(
        client, "/v1/auth/login", json={"email": EMAIL, "password": "a brand new passphrase"}
    )
    assert new.status_code == 200 and new.json()["user"]["email_verified"] is True
    assert "đổi" in mailer.sent[-1].subject or "changed" in mailer.sent[-1].subject


# 7. A code only works for its own purpose.
async def test_codes_are_bound_to_their_purpose(
    client: AsyncClient, mailer: RecordingMailer
) -> None:
    auth, _ = await register(client)
    verify_code = mailer.last_code(EMAIL)
    assert (await reset(client, verify_code)).status_code == 400
    await forgot(client)
    reset_code = mailer.last_code(EMAIL)
    if reset_code != verify_code:
        assert (await confirm(client, auth, reset_code)).status_code == 400


# 8. Expired codes are rejected.
async def test_expired_code(
    client: AsyncClient, mailer: RecordingMailer, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "AUTH_CODE_TTL_MINUTES", 0)
    auth, _ = await register(client)
    assert (await confirm(client, auth, mailer.last_code(EMAIL))).status_code == 400


# 9. Codes are stored as HMACs, never in plain text (R15).
async def test_codes_are_not_stored_in_plain_text(
    client: AsyncClient, mailer: RecordingMailer
) -> None:
    await register(client)
    code = mailer.last_code(EMAIL)
    async with AsyncSessionLocal() as s:
        stored = (await s.execute(select(AuthCode.code_hash))).scalars().all()
    assert stored and all(code not in h and len(h) == 64 for h in stored)


# 10. Google-only accounts are pointed to Google sign-in; repeated requests are limited silently.
async def test_google_only_and_request_limit(client: AsyncClient, mailer: RecordingMailer) -> None:
    async with AsyncSessionLocal() as s:
        await UserService(s).create(email="g@example.com", password_hash=None, locale="en")
        await s.commit()

    assert (await forgot(client, "g@example.com")).status_code == 202
    assert "Google" in mailer.sent[-1].subject

    await register(client)
    sent = len(mailer.sent)
    for _ in range(settings.PASSWORD_RESET_MAX_PER_EMAIL_PER_HOUR + 2):
        assert (await forgot(client)).status_code == 202
    assert len(mailer.sent) - sent == settings.PASSWORD_RESET_MAX_PER_EMAIL_PER_HOUR
