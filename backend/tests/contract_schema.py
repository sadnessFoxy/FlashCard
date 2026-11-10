"""
Validate payloads against contract/openapi.yaml.
OpenAPI 3.1 schemas are JSON Schema 2020-12, so jsonschema validates them directly.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
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


def _resolve(node: dict[str, Any]) -> dict[str, Any]:
    """Follow a local `$ref` such as `#/components/responses/X`."""
    while "$ref" in node:
        target: Any = load_contract()
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        node = target
    return node


def contract_operations() -> dict[tuple[str, str], dict[str, Any]]:
    """{(METHOD, path): operation} for every operation in the contract."""
    ops: dict[tuple[str, str], dict[str, Any]] = {}
    for path, item in load_contract()["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                ops[(method.upper(), path)] = operation
    return ops


def contract_path_for(path: str) -> str:
    """Map a concrete URL path to its contract template, e.g. /v1/spaces/{space_id}."""
    for template in load_contract()["paths"]:
        pattern = "^" + re.sub(r"\\\{[^/]+\\\}", "[^/]+", re.escape(template)) + "$"
        if re.match(pattern, path):
            return template
    raise AssertionError(f"{path} is not in the contract")


def _declared_response(method: str, path: str, status: int) -> dict[str, Any]:
    operation = contract_operations()[(method.upper(), contract_path_for(path))]
    responses = operation["responses"]
    assert str(status) in responses, f"{method} {path}: status {status} not declared in contract"
    return _resolve(responses[str(status)])


def response_validator(method: str, path: str, status: int) -> Draft202012Validator:
    schema = _declared_response(method, path, status)["content"]["application/json"]["schema"]
    # Wrap so internal refs ("#/components/...") resolve inside the contract document.
    wrapped = {"$ref": f"{_CONTRACT_URI}{schema['$ref']}"} if "$ref" in schema else schema
    return Draft202012Validator(wrapped, registry=_registry())


def assert_matches_contract(method: str, path: str, status: int, body: Any) -> None:
    errors = sorted(response_validator(method, path, status).iter_errors(body), key=str)
    assert not errors, "Response does not match the contract:\n" + "\n".join(
        f"- {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors
    )


def assert_response_matches_contract(response: httpx.Response) -> None:
    """Check status is declared and, when the contract declares a JSON body, its shape."""
    request = response.request
    path = request.url.path
    declared = _declared_response(request.method, path, response.status_code)
    if "content" in declared:
        assert_matches_contract(request.method, path, response.status_code, response.json())
    else:
        assert not response.content, f"{request.method} {path}: contract declares no body"
