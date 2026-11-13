"""Regression: the request session must commit before the response is sent."""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"


def test_get_db_is_always_function_scoped() -> None:
    offenders = [
        f"{path.relative_to(APP)}: {match.group(0)}"
        for path in APP.rglob("*.py")
        for match in re.finditer(r"Depends\(get_db[^)]*\)", path.read_text(encoding="utf-8"))
        if 'scope="function"' not in match.group(0)
    ]
    assert not offenders, offenders
