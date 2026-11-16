"""F16 acceptance criteria (docs/specs/f16-admin.md section 9)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response
from sqlalchemy import update

from app.db.session import AsyncSessionLocal
from app.integrations.object_storage import get_storage
from app.main import app
from app.modules.ai.usage import record_ai_usage
from app.modules.documents.models import Document
from app.modules.documents.queue import get_job_queue
from app.modules.users.models import User
from tests.api.test_documents import PDF, consent, upload
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import (
    Reader,
    TopicProvider,
    ai,
    ask,
    final,
    new_conversation,
    new_reader,
    seed_document,
)
from tests.fixtures.fakes import InMemoryStorage, RecordingQueue
from tests.fixtures.pdfs import make_pdf

__all__ = ["ai"]  # pytest fixture, imported for use by the tests below

pytestmark = pytest.mark.usefixtures("clean_db")

NATIVE = {"X-Client-Platform": "native"}


@pytest_asyncio.fixture
async def queue() -> AsyncGenerator[RecordingQueue, None]:
    recording = RecordingQueue()
    app.dependency_overrides[get_job_queue] = lambda: recording
    app.dependency_overrides[get_storage] = lambda: InMemoryStorage()
    yield recording


async def make_admin(client: AsyncClient, email: str = "admin@example.com") -> Reader:
    admin = await new_reader(client, email)
    async with AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.id == admin.user_id).values(role="admin"))
        await s.commit()
    return admin


async def call(client: AsyncClient, method: str, url: str, who: Reader, **kw: Any) -> Response:
    response = await client.request(method, url, headers={**NATIVE, **who.auth}, **kw)
    assert_response_matches_contract(response)
    return response


async def audit(
    client: AsyncClient, admin: Reader, action: str | None = None
) -> list[dict[str, Any]]:
    params = {"action": action} if action else {}
    return (await call(client, "GET", "/v1/admin/audit", admin, params=params)).json()["items"]  # type: ignore[no-any-return]


# 1. Only admins get in; the role is checked on the server.
async def test_admin_endpoints_require_the_admin_role(client: AsyncClient) -> None:
    learner = await new_reader(client)
    for method, url in [
        ("GET", "/v1/admin/overview"),
        ("GET", "/v1/admin/users"),
        ("GET", "/v1/admin/settings"),
        ("PATCH", "/v1/admin/settings"),
        ("GET", "/v1/admin/audit"),
    ]:
        response = await call(client, method, url, learner, json={"values": {"ai_enabled": False}})
        assert response.status_code == 403, url
        assert response.json()["code"] == "FORBIDDEN"
    assert (await client.get("/v1/admin/overview")).status_code == 401


# 2. Overview counts users, documents, questions and tokens of today.
async def test_overview(client: AsyncClient) -> None:
    admin = await make_admin(client)
    learner = await new_reader(client)
    await seed_document(learner, "A.pdf", [(1, "x")])
    await record_ai_usage(
        user_id=str(learner.user_id),
        provider="fake",
        model="m",
        operation="chat",
        input_tokens=30,
        output_tokens=12,
        latency_ms=5,
        success=True,
    )
    await record_ai_usage(
        user_id=None,
        provider="fake",
        model="m",
        operation="embed",
        input_tokens=8,
        output_tokens=0,
        latency_ms=5,
        success=False,
        error_code="X",
    )

    body = (await call(client, "GET", "/v1/admin/overview", admin)).json()

    assert body["users_total"] == 2 and body["users_active_today"] == 2
    assert body["documents_by_status"] == {"READY": 1}
    assert (body["questions_today"], body["ai_calls_today"], body["ai_failures_today"]) == (1, 2, 1)
    assert body["ai_tokens_today"] == 50
    assert body["ai_enabled"] is True and body["circuit_state"] == "closed"


# 3. User list: search and metadata only (R13).
async def test_list_and_search_users(client: AsyncClient) -> None:
    admin = await make_admin(client)
    learner = await new_reader(client, "learner@example.com")
    await seed_document(learner, "A.pdf", [(1, "x")])

    body = (await call(client, "GET", "/v1/admin/users", admin, params={"q": "LEARNER"})).json()

    assert body["total"] == 1
    [user] = body["items"]
    assert (user["email"], user["document_count"], user["sign_in_methods"]) == (
        "learner@example.com",
        1,
        ["email"],
    )
    assert not {"content", "filename", "messages"} & set(user)


# 4. Block revokes sessions and is audited with its reason; admins cannot block themselves.
async def test_block_and_unblock(client: AsyncClient) -> None:
    admin = await make_admin(client)
    session = (
        await client.post(
            "/v1/auth/register",
            json={"email": "victim@example.com", "password": "a long enough passphrase"},
            headers=NATIVE,
        )
    ).json()
    target = Reader(
        {"Authorization": f"Bearer {session['access_token']}"}, session["user"]["id"], ""
    )

    response = await call(
        client, "POST", f"/v1/admin/users/{target.user_id}/block", admin, json={"reason": "Spam"}
    )
    assert response.status_code == 200 and response.json()["status"] == "blocked"
    me = await client.get("/v1/me", headers=target.auth)
    assert me.status_code == 403 and me.json()["code"] == "ACCOUNT_BLOCKED"
    refresh = await client.post(
        "/v1/auth/refresh", json={"refresh_token": session["refresh_token"]}, headers=NATIVE
    )
    assert refresh.status_code == 401
    [entry] = await audit(client, admin, "user.block")
    assert (entry["reason"], entry["before"], entry["after"]) == (
        "Spam",
        {"status": "active"},
        {"status": "blocked"},
    )
    assert entry["actor_email"] == "admin@example.com"

    unblocked = await call(client, "POST", f"/v1/admin/users/{target.user_id}/unblock", admin)
    assert unblocked.json()["status"] == "active"
    myself = await call(
        client, "POST", f"/v1/admin/users/{admin.user_id}/block", admin, json={"reason": "x"}
    )
    assert myself.status_code == 409 and myself.json()["code"] == "CANNOT_TARGET_SELF"


# 5. Per-user quota override, with expiry.
async def test_quota_override(client: AsyncClient) -> None:
    admin = await make_admin(client)
    learner = await new_reader(client)
    url = f"/v1/admin/users/{learner.user_id}/quota"

    set_ = await call(client, "PUT", url, admin, json={"daily_limit": 2})
    assert set_.json()["quota_override"] == {"daily_limit": 2, "expires_at": None}
    assert (await client.get("/v1/usage/me", headers=learner.auth)).json()["daily_limit"] == 2

    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    await call(client, "PUT", url, admin, json={"daily_limit": 3, "expires_at": past})
    assert (await client.get("/v1/usage/me", headers=learner.auth)).json()["daily_limit"] == 30

    cleared = await call(client, "PUT", url, admin, json={"daily_limit": None})
    assert cleared.json()["quota_override"] is None
    assert [e["action"] for e in await audit(client, admin)] == ["user.quota"] * 3


# 6. Sign out everywhere, and delete on request (U9) with the audit row kept.
async def test_sign_out_and_delete_user(client: AsyncClient, queue: RecordingQueue) -> None:
    admin = await make_admin(client)
    learner = await new_reader(client)
    await seed_document(learner, "A.pdf", [(1, "x")], storage_key="files/k1")

    assert (
        await call(client, "POST", f"/v1/admin/users/{learner.user_id}/sign-out", admin)
    ).status_code == 204
    deleted = await call(
        client,
        "POST",
        f"/v1/admin/users/{learner.user_id}/deletion",
        admin,
        json={"reason": "Ticket #12"},
    )
    assert deleted.status_code == 204
    assert (
        await call(client, "GET", f"/v1/admin/users/{learner.user_id}", admin)
    ).status_code == 404
    assert [k for _, k in queue.purges] == ["files/k1"]
    [entry] = await audit(client, admin, "user.delete")
    assert entry["reason"] == "Ticket #12"


# 7. Documents by status, and retrying a failed one.
async def test_documents_and_retry(client: AsyncClient, queue: RecordingQueue) -> None:
    admin = await make_admin(client)
    learner = await new_reader(client)
    failed = await seed_document(learner, "Bad.pdf", [(1, "x")])
    ready = await seed_document(learner, "Good.pdf", [(1, "x")])
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(Document)
            .where(Document.id == failed)
            .values(status="FAILED", error_code="PROCESSING_FAILED")
        )
        await s.commit()

    listed = (
        await call(client, "GET", "/v1/admin/documents", admin, params={"status": "FAILED"})
    ).json()["items"]
    assert [(d["filename"], d["owner_email"], d["error_code"]) for d in listed] == [
        ("Bad.pdf", "reader@example.com", "PROCESSING_FAILED")
    ]
    retried = await call(client, "POST", f"/v1/admin/documents/{failed}/retry", admin)
    assert retried.status_code == 200 and retried.json()["status"] == "QUEUED"
    assert [d for d, _ in queue.jobs] == [failed]
    assert (
        await call(client, "POST", f"/v1/admin/documents/{ready}/retry", admin)
    ).status_code == 409
    assert [e["action"] for e in await audit(client, admin)] == ["document.retry"]


# 8. Runtime settings: validated, audited, and applied without a restart.
async def test_settings_apply_at_runtime(
    client: AsyncClient, ai: TopicProvider, queue: RecordingQueue
) -> None:
    admin = await make_admin(client)
    learner = await new_reader(client)
    await seed_document(learner, "A.pdf", [(1, "A derivative measures change.")])

    bad = await call(
        client, "PATCH", "/v1/admin/settings", admin, json={"values": {"max_pages": 0, "nope": 1}}
    )
    assert bad.status_code == 422
    assert {e["field"] for e in bad.json()["errors"]} == {"max_pages", "nope"}

    changed = await call(
        client,
        "PATCH",
        "/v1/admin/settings",
        admin,
        json={"values": {"ai_enabled": False, "user_daily_query_limit": 5, "max_pages": 1}},
    )
    assert changed.json()["values"]["ai_enabled"] is False
    assert changed.json()["defaults"]["max_pages"] == 200

    assert (await client.get("/v1/usage/me", headers=learner.auth)).json()["daily_limit"] == 5
    conversation = await new_conversation(client, learner)
    _, events = await ask(client, learner, conversation, "What is a derivative?")
    assert final(events)["mode"] == "retrieval_only"  # AI switched off: passages only
    assert ai.chat_calls == []
    await consent(client, learner.auth)
    too_long = await upload(
        client, learner.auth, make_pdf(["one", "two"]), space_id=learner.space_id
    )
    assert too_long.status_code == 422 and too_long.json()["max_pages"] == 1

    entries = await audit(client, admin, "settings.update")
    assert {(e["target_id"], e["before"]["value"], e["after"]["value"]) for e in entries} == {
        ("ai_enabled", True, False),
        ("user_daily_query_limit", 30, 5),
        ("max_pages", 200, 1),
    }
    ok = await upload(client, learner.auth, PDF, space_id=learner.space_id)
    assert ok.status_code == 422  # PDF fixture has 2 pages, still above the limit
