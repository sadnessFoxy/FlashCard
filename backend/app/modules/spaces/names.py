"""Space name normalization and default names (spec f4b section 6)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import PurePosixPath

from app.modules.spaces.models import NAME_MAX_LENGTH

_WHITESPACE = re.compile(r"\s+")
_DOCUMENT_SUFFIXES = {".pdf", ".docx"}


def normalize_name(raw: str) -> str:
    """NFC (Vietnamese diacritics compare consistently), trim, collapse whitespace."""
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", raw)).strip()


def validate_name(raw: str) -> str:
    """Normalized name, or ValueError when empty or too long."""
    name = normalize_name(raw)
    if not name:
        raise ValueError("name must not be empty")
    if len(name) > NAME_MAX_LENGTH:
        raise ValueError(f"name must be at most {NAME_MAX_LENGTH} characters")
    return name


def default_name_from_filename(filename: str) -> str:
    """'Giáo trình.pdf' -> 'Giáo trình'. Falls back to a generic name when nothing is left."""
    base = PurePosixPath(filename.replace("\\", "/")).name
    for suffix in _DOCUMENT_SUFFIXES:
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
            break
    return normalize_name(base)[:NAME_MAX_LENGTH].rstrip() or "Space"


def numbered(name: str, n: int) -> str:
    """'Name' -> 'Name (n)', trimming the base so the result stays within the limit."""
    suffix = f" ({n})"
    return name[: NAME_MAX_LENGTH - len(suffix)].rstrip() + suffix
