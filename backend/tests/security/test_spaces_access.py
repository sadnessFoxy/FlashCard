"""docs/TESTING.md: user A must not reach user B's data by changing an id (IDOR)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.usefixtures("clean_db")


async def _auth(client: AsyncClient, email: str) -> dict[str, str]:
    body = (
        await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "a long enough passphrase"},
            headers={"X-Client-Platform": "native"},
        )
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


async def test_other_users_space_is_invisible_and_untouchable(client: AsyncClient) -> None:
    alice = await _auth(client, "alice@example.com")
    bob = await _auth(client, "bob@example.com")
    space = (await client.post("/v1/spaces", json={"name": "Alice only"}, headers=alice)).json()
    url = f"/v1/spaces/{space['id']}"

    responses = [
        await client.get(url, headers=bob),
        await client.patch(url, json={"name": "hacked"}, headers=bob),
        await client.delete(url, headers=bob),
    ]

    for response in responses:
        assert (response.status_code, response.json()["code"]) == (404, "NOT_FOUND")
        assert "Alice only" not in response.text
    assert (await client.get("/v1/spaces", headers=bob)).json() == {"items": []}
    still_there = await client.get(url, headers=alice)
    assert still_there.json()["name"] == "Alice only"


async def test_owner_cannot_be_forged_in_body(client: AsyncClient) -> None:
    alice = await _auth(client, "alice@example.com")

    response = await client.post(
        "/v1/spaces",
        json={"name": "x", "owner_id": "00000000-0000-0000-0000-000000000000"},
        headers=alice,
    )

    assert (response.status_code, response.json()["code"]) == (422, "VALIDATION_ERROR")
