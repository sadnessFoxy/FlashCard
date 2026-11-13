"""Display-safe file names (never used as storage paths)."""

from __future__ import annotations

import unicodedata
from pathlib import PurePosixPath

MAX_FILENAME = 255


def sanitize_filename(raw: str | None, fallback: str = "document.pdf") -> str:
    name = PurePosixPath((raw or "").replace("\\", "/")).name
    name = unicodedata.normalize("NFC", name)
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C").strip()
    name = name.strip(". ")
    return name[:MAX_FILENAME] or fallback
