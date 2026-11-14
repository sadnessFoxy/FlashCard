"""F15 acceptance criteria (docs/specs/f15-profile.md section 9)."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.main import app
from app.modules.ai.usage import record_ai_usage
from app.modules.documents.queue import get_job_queue
from app.modules.study.flashcards.models import FlashcardDeck
from app.modules.usage.models import AiUsage
from app.modules.users.models import User
from app.modules.users.service import UserService
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import new_reader, seed_document
from tests.fixtures.fakes import RecordingMailer, RecordingQueue

pytestmark = pytest.mark.usefixtures("clean_db")

PASSWORD = "a long enough passphrase"  # what tests.api.test_documents.sign_up uses
NATIVE = {"X-Client-Platform": "native"}


async def call(
    client: AsyncClient, method: str, url: str, auth: dict[str, str], **kw: Any
) -> Response:
    response = await client.request(method, url, headers={**NATIVE, **auth}, **kw)
    assert_response_matches_contract(response)
    return response


async def change(
    client: AsyncClient, auth: dict[str, str], current: str, new: str = "a brand new passphrase"
) -> Response:
    return await call(
        client,
        "POST",
        "/v1/auth/password/change",
        auth,
        json={"current_password": current, "new_password": new},
    )


async def count(model: type, **where: Any) -> int:
    async with AsyncSessionLocal() as s:
        stmt = select(func.count()).select_from(model)
        for column, value in where.items():
            stmt = stmt.where(getattr(model, column) == value)
        return int((await s.execute(stmt)).scalar_one())


# 1. The interface language is saved on the account.
async def test_update_language(client: AsyncClient) -> None:
    reader = await new_reader(client)
    response = await call(client, "PATCH", "/v1/me", reader.auth, json={"locale": "en"})
    assert response.status_code == 200 and response.json()["locale"] == "en"
    assert (await client.get("/v1/me", headers=reader.auth)).json()["locale"] == "en"
    bad = await call(client, "PATCH", "/v1/me", reader.auth, json={"locale": "fr"})
    assert bad.status_code == 422


# 2. Changing the password signs out other sessions and keeps this device signed in.
async def test_change_password(client: AsyncClient, mailer: RecordingMailer) -> None:
    reader = await new_reader(client)
    other = (
        await client.post(
            "/v1/auth/login",
            json={"email": "reader@example.com", "password": PASSWORD},
            headers=NATIVE,
        )
    ).json()

    response = await change(client, reader.auth, PASSWORD)

    assert response.status_code == 200
    new_session = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert (await client.get("/v1/me", headers=new_session)).status_code == 200
    refreshed = await client.post(
        "/v1/auth/refresh", json={"refresh_token": other["refresh_token"]}, headers=NATIVE
    )
    assert refreshed.status_code == 401
    login = await client.post(
        "/v1/auth/login",
        json={"email": "reader@example.com", "password": "a brand new passphrase"},
        headers=NATIVE,
    )
    assert login.status_code == 200
    assert mailer.sent[-1].to == "reader@example.com"


# 3. Wrong current password, weak new password, attempt limit.
async def test_change_password_checks(client: AsyncClient) -> None:
    reader = await new_reader(client)

    weak = await change(client, reader.auth, PASSWORD, "short")
    assert weak.status_code == 422 and weak.json()["code"] == "WEAK_PASSWORD"
    for _ in range(settings.LOGIN_MAX_FAILURES_PER_EMAIL):
        wrong = await change(client, reader.auth, "not my password")
        assert wrong.status_code == 403 and wrong.json()["code"] == "INVALID_PASSWORD"
    blocked = await change(client, reader.auth, PASSWORD)  # even the right one, once blocked
    assert blocked.status_code == 429


# 4. Google-only accounts have no password to change.
async def test_google_only_account_cannot_change_password(client: AsyncClient) -> None:
    reader = await new_reader(client)
    async with AsyncSessionLocal() as s:
        user = await UserService(s).get(reader.user_id)
        assert user is not None
        user.password_hash = None
        await s.commit()
    response = await change(client, reader.auth, PASSWORD)
    assert response.status_code == 409 and response.json()["code"] == "NO_PASSWORD"


# 5. Deleting the account removes its data, queues file purges, keeps anonymous usage.
async def test_delete_account(client: AsyncClient) -> None:
    queue = RecordingQueue()
    app.dependency_overrides[get_job_queue] = lambda: queue
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    doc = await seed_document(reader, "Giải tích.pdf", [(1, "x")], storage_key="files/k1")
    await seed_document(other, "Theirs.pdf", [(1, "y")])
    await call(
        client, "POST", "/v1/decks", reader.auth, json={"space_id": reader.space_id, "name": "B"}
    )
    await record_ai_usage(
        user_id=str(reader.user_id),
        provider="fake",
        model="m",
        operation="chat",
        input_tokens=1,
        output_tokens=1,
        latency_ms=1,
        success=True,
    )

    wrong = await call(client, "POST", "/v1/me/deletion", reader.auth, json={"password": "nope"})
    assert wrong.status_code == 403
    response = await call(
        client, "POST", "/v1/me/deletion", reader.auth, json={"password": PASSWORD}
    )

    assert response.status_code == 204
    assert await count(User, id=reader.user_id) == 0
    assert await count(FlashcardDeck, owner_id=reader.user_id) == 0
    assert queue.purges == [(doc, "files/k1")]
    assert await count(AiUsage) == 1 and await count(AiUsage, user_id=reader.user_id) == 0
    assert (await client.get("/v1/me", headers=reader.auth)).status_code == 401
    assert (await client.get("/v1/me", headers=other.auth)).status_code == 200


# 6. Google-only accounts confirm by retyping their email.
async def test_delete_google_only_account(client: AsyncClient) -> None:
    app.dependency_overrides[get_job_queue] = lambda: RecordingQueue()
    reader = await new_reader(client)
    async with AsyncSessionLocal() as s:
        user = await UserService(s).get(reader.user_id)
        assert user is not None
        user.password_hash = None
        await s.commit()

    mismatch = await call(
        client, "POST", "/v1/me/deletion", reader.auth, json={"confirm_email": "x@example.com"}
    )
    assert mismatch.status_code == 422 and mismatch.json()["code"] == "CONFIRMATION_MISMATCH"
    response = await call(
        client,
        "POST",
        "/v1/me/deletion",
        reader.auth,
        json={"confirm_email": " Reader@Example.com "},
    )
    assert response.status_code == 204


# 7. Web: deleting the account clears the session cookies.
async def test_delete_account_clears_web_cookies(client: AsyncClient) -> None:
    app.dependency_overrides[get_job_queue] = lambda: RecordingQueue()
    reader = await new_reader(client)
    response = await client.post(
        "/v1/me/deletion",
        json={"password": PASSWORD},
        headers={**reader.auth, "X-Client-Platform": "web", "Origin": "http://localhost:8081"},
    )
    assert response.status_code == 204
    cookies = " ".join(response.headers.get_list("set-cookie"))
    assert "access_token=" in cookies and "refresh_token=" in cookies
