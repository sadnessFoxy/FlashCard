"""
Backend khớp contract/openapi.yaml:
- mọi route của app đều có trong contract và ngược lại (không có endpoint "chui"),
- operationId giống nhau,
- validator của contract thật sự bắt được payload sai (tránh test luôn xanh).
Kiểm tra body response theo schema nằm trong từng test endpoint (test_system.py).
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
    """Các operation backend thật sự phục vụ, lấy từ schema FastAPI tự sinh."""
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
    assert app_ops - contract_ops == set(), "Route có trong backend nhưng thiếu trong contract"
    assert contract_ops - app_ops == set(), "Route có trong contract nhưng backend chưa làm"


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
