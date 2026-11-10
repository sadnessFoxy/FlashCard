"""Email normalization (spec f2 section 6)."""

from __future__ import annotations

import unicodedata

from email_validator import EmailNotValidError, validate_email


def normalize_email(raw: str) -> str:
    """Trim, NFKC, lowercase. Dots and `+tags` are kept: not every provider ignores them."""
    return unicodedata.normalize("NFKC", raw).strip().lower()


def validate_and_normalize_email(raw: str) -> str:
    """Normalize and validate syntax (no DNS lookup). Raises ValueError."""
    email = normalize_email(raw)
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError("invalid email address") from exc
    return email
