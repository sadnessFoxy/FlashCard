"""
Password rules (spec f2 section 6, NIST SP 800-63B): 8-128 chars, no composition rules,
reject common passwords and the email itself.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

MIN_LENGTH = 8
MAX_LENGTH = 128

PasswordProblem = Literal["too_short", "too_long", "too_common", "same_as_email"]

_COMMON_PASSWORDS_FILE = Path(__file__).parent / "data" / "common_passwords.txt"


@lru_cache(maxsize=1)
def _common_passwords() -> frozenset[str]:
    lines = _COMMON_PASSWORDS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip().lower() for line in lines if line.strip() and not line.startswith("#")
    )


def check_password(password: str, email: str) -> PasswordProblem | None:
    """Return why the password is rejected, or None. `email` must be normalized."""
    if len(password) < MIN_LENGTH:
        return "too_short"
    if len(password) > MAX_LENGTH:
        return "too_long"
    lowered = password.lower()
    if lowered in _common_passwords():
        return "too_common"
    if lowered in {email, email.split("@", 1)[0]}:
        return "same_as_email"
    return None
