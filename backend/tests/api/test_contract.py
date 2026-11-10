"""
Backend matches contract/openapi.yaml:
- every app route is in the contract and vice versa (no undocumented endpoints),
- operationIds match,
- the contract validator really rejects bad payloads (no always-green tests).
Response bodies are checked against schemas in each endpoint test.
"""

from __future__ import annotations

import pytest

from app.main import app
from tests.contract_schema import (
    HTTP_METHODS,
    assert_matches_contract,
    contract_operations,
    load_contract,
)


def _app_operations() -> dict[tuple[str, str], str]:
    """Operations the backend actually serves, from FastAPI's generated schema."""
    ops: dict[tuple[str, str], str] = {}
    for path, item in app.openapi()["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                ops[(method.upper(), path)] = operation["operationId"]
    return ops


def test_contract_is_openapi_3_1() -> None:
    assert load_contract()["openapi"].startswith("3.1")


def test_every_app_route_is_in_contract_and_vice_versa() -> None:
    app_ops = set(_app_operations())
    contract_ops = set(contract_operations())
    assert app_ops - contract_ops == set(), (
        "Route served by the backend but missing in the contract"
    )
    assert contract_ops - app_ops == set(), "Route in the contract but not implemented"


def test_operation_ids_match_contract() -> None:
    contract_ids = {key: op["operationId"] for key, op in contract_operations().items()}
    assert _app_operations() == contract_ids


def test_contract_validator_rejects_wrong_payload() -> None:
    with pytest.raises(AssertionError):
        assert_matches_contract("GET", "/health", 200, {"status": "ok", "unexpected": 1})
    with pytest.raises(AssertionError):
        assert_matches_contract(
            "GET",
            "/v1/system/status",
            200,
            {"status": "ok", "version": "1", "checks": {"database": {"status": "up"}}},
        )


async def test_framework_errors_use_error_response_shape(client) -> None:  # type: ignore[no-untyped-def]
    bad_json = await client.post(
        "/v1/auth/login",
        content=b"{not json",
        headers={"Content-Type": "application/json", "X-Client-Platform": "native"},
    )
    unknown = await client.get("/v1/does-not-exist")
    wrong_method = await client.put("/health")

    for response in (bad_json, unknown, wrong_method):
        body = response.json()
        assert set(body) >= {"code", "message"} and "detail" not in body
    assert bad_json.json()["errors"] == [{"field": "body", "type": "json_invalid"}]
    assert unknown.json()["code"] == "NOT_FOUND"
    assert wrong_method.json()["code"] == "METHOD_NOT_ALLOWED"
