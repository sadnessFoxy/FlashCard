"""F4b acceptance criteria (docs/specs/f4b-spaces.md section 9), against the test DB."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient, Response

from app.db.session import AsyncSessionLocal
from app.modules.spaces.service import SpaceService
from tests.contract_schema import assert_response_matches_contract

pytestmark = pytest.mark.usefixtures("clean_db")


async def call(client: AsyncClient, method: str, path: str, **kwargs: object) -> Response:
    response = await client.request(method, path, **kwargs)  # type: ignore[arg-type]
    assert_response_matches_contract(response)
    return response


async def sign_up(client: AsyncClient, email: str) -> tuple[dict[str, str], str]:
    body = (
        await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "a long enough passphrase"},
            headers={"X-Client-Platform": "native"},
        )
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["id"]


@pytest.fixture
async def alice(client: AsyncClient) -> dict[str, str]:
    return (await sign_up(client, "alice@example.com"))[0]


async def create(client: AsyncClient, auth: dict[str, str], name: str) -> Response:
    return await call(client, "POST", "/v1/spaces", json={"name": name}, headers=auth)


async def test_create_normalizes_name(client: AsyncClient, alice: dict[str, str]) -> None:
    response = await create(client, alice, "  Giải   tích\t1 ")

    assert response.status_code == 201
    assert response.json()["name"] == "Giải tích 1"


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
async def test_invalid_names_rejected(
    client: AsyncClient, alice: dict[str, str], name: str
) -> None:
    response = await create(client, alice, name)

    assert (response.status_code, response.json()["code"]) == (422, "VALIDATION_ERROR")
    listed = await call(client, "GET", "/v1/spaces", headers=alice)
    assert listed.json() == {"items": []}


async def test_name_of_exactly_100_chars_is_accepted(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    assert (await create(client, alice, "x" * 100)).status_code == 201


async def test_duplicate_name_is_case_insensitive(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    await create(client, alice, "Giải tích 1")

    response = await create(client, alice, "giải TÍCH 1")

    assert (response.status_code, response.json()["code"]) == (409, "SPACE_NAME_TAKEN")


async def test_decomposed_vietnamese_counts_as_duplicate(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    await create(client, alice, "Hóa học")  # precomposed (NFC)

    response = await create(client, alice, "Hóa học")  # decomposed (NFD)

    assert response.status_code == 409


async def test_same_name_allowed_for_different_users(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    bob, _ = await sign_up(client, "bob@example.com")
    await create(client, alice, "Giải tích 1")

    assert (await create(client, bob, "Giải tích 1")).status_code == 201


async def test_list_is_own_spaces_newest_first(client: AsyncClient, alice: dict[str, str]) -> None:
    bob, _ = await sign_up(client, "bob@example.com")
    for name in ("A", "B", "C"):
        await create(client, alice, name)
    await create(client, bob, "Bob's")

    response = await call(client, "GET", "/v1/spaces", headers=alice)

    assert [s["name"] for s in response.json()["items"]] == ["C", "B", "A"]


async def test_rename_moves_space_to_top(client: AsyncClient, alice: dict[str, str]) -> None:
    first = (await create(client, alice, "First")).json()
    await create(client, alice, "Second")

    renamed = await call(
        client, "PATCH", f"/v1/spaces/{first['id']}", json={"name": "First v2"}, headers=alice
    )

    assert renamed.status_code == 200
    assert renamed.json()["name"] == "First v2"
    assert renamed.json()["updated_at"] > first["updated_at"]
    listed = await call(client, "GET", "/v1/spaces", headers=alice)
    assert [s["name"] for s in listed.json()["items"]] == ["First v2", "Second"]


async def test_rename_to_other_spaces_name_conflicts(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    first = (await create(client, alice, "First")).json()
    await create(client, alice, "Second")

    response = await call(
        client, "PATCH", f"/v1/spaces/{first['id']}", json={"name": "SECOND"}, headers=alice
    )

    assert response.status_code == 409


async def test_rename_changing_only_case_is_allowed(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    space = (await create(client, alice, "giải tích")).json()

    response = await call(
        client, "PATCH", f"/v1/spaces/{space['id']}", json={"name": "Giải Tích"}, headers=alice
    )

    assert (response.status_code, response.json()["name"]) == (200, "Giải Tích")


async def test_delete(client: AsyncClient, alice: dict[str, str]) -> None:
    space = (await create(client, alice, "Temp")).json()

    deleted = await call(client, "DELETE", f"/v1/spaces/{space['id']}", headers=alice)

    assert deleted.status_code == 204
    assert (
        await call(client, "GET", f"/v1/spaces/{space['id']}", headers=alice)
    ).status_code == 404
    assert (await call(client, "GET", "/v1/spaces", headers=alice)).json() == {"items": []}


async def test_unknown_and_malformed_ids(client: AsyncClient, alice: dict[str, str]) -> None:
    missing = await call(client, "GET", f"/v1/spaces/{uuid.uuid4()}", headers=alice)
    malformed = await call(client, "GET", "/v1/spaces/not-a-uuid", headers=alice)

    assert (missing.status_code, missing.json()["code"]) == (404, "NOT_FOUND")
    assert (malformed.status_code, malformed.json()["code"]) == (422, "VALIDATION_ERROR")


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/v1/spaces", None),
        ("POST", "/v1/spaces", {"name": "x"}),
        ("GET", f"/v1/spaces/{uuid.uuid4()}", None),
        ("PATCH", f"/v1/spaces/{uuid.uuid4()}", {"name": "x"}),
        ("DELETE", f"/v1/spaces/{uuid.uuid4()}", None),
    ],
)
async def test_requires_sign_in(
    client: AsyncClient, method: str, path: str, body: dict[str, str] | None
) -> None:
    response = await client.request(method, path, json=body)

    assert (response.status_code, response.json()["code"]) == (401, "UNAUTHORIZED")


async def test_default_space_named_after_document(
    client: AsyncClient, alice: dict[str, str]
) -> None:
    owner_id = (await call(client, "GET", "/v1/me", headers=alice)).json()["id"]

    async with AsyncSessionLocal() as session:
        service = SpaceService(session)
        first = await service.create_default_for_document(
            uuid.UUID(owner_id), "Giáo trình Giải tích.pdf"
        )
        second = await service.create_default_for_document(
            uuid.UUID(owner_id), "giáo trình giải tích.PDF"
        )
        await session.commit()

    assert first.name == "Giáo trình Giải tích"
    assert second.name == "giáo trình giải tích (2)"
