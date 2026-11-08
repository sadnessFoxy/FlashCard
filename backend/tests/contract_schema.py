"""
Đọc contract/openapi.yaml và kiểm tra dữ liệu theo schema trong contract.
Schema OpenAPI 3.1 là JSON Schema 2020-12 nên dùng thẳng jsonschema.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contract" / "openapi.yaml"
_CONTRACT_URI = "urn:flashcard:contract"

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@lru_cache(maxsize=1)
def load_contract() -> dict[str, Any]:
    with CONTRACT_PATH.open(encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data


@lru_cache(maxsize=1)
def _registry() -> Registry:
    resource = Resource(contents=load_contract(), specification=DRAFT202012)
    return Registry().with_resource(_CONTRACT_URI, resource)


def contract_operations() -> dict[tuple[str, str], dict[str, Any]]:
    """{(METHOD, path): operation} cho mọi operation trong contract."""
    ops: dict[tuple[str, str], dict[str, Any]] = {}
    for path, item in load_contract()["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                ops[(method.upper(), path)] = operation
    return ops


def response_validator(method: str, path: str, status: int) -> Draft202012Validator:
    """Validator cho body JSON của một response đã khai báo trong contract."""
    operation = contract_operations()[(method.upper(), path)]
    response = operation["responses"][str(status)]
    schema = response["content"]["application/json"]["schema"]
    # Bọc lại để $ref nội bộ ("#/components/...") được phân giải trong tài liệu contract.
    wrapped = {"$ref": f"{_CONTRACT_URI}{schema['$ref']}"} if "$ref" in schema else schema
    return Draft202012Validator(wrapped, registry=_registry())


def assert_matches_contract(method: str, path: str, status: int, body: Any) -> None:
    errors = sorted(response_validator(method, path, status).iter_errors(body), key=str)
    assert not errors, "Response không khớp contract:\n" + "\n".join(
        f"- {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors
    )
