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
