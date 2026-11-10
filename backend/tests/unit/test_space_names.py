"""Space name rules (spec f4b section 6)."""

from __future__ import annotations

import pytest

from app.modules.spaces.names import (
    default_name_from_filename,
    numbered,
    validate_name,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Giải   tích 1 ", "Giải tích 1"),
        ("Hóa học", "Hóa học"),  # NFD -> NFC
        ("📚 Ôn thi", "📚 Ôn thi"),
        ("a\n\tb", "a b"),
    ],
)
def test_validate_name_normalizes(raw: str, expected: str) -> None:
    assert validate_name(raw) == expected


@pytest.mark.parametrize("raw", ["", " \t\n", "x" * 101])
def test_validate_name_rejects(raw: str) -> None:
    with pytest.raises(ValueError):
        validate_name(raw)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("Giáo trình.pdf", "Giáo trình"),
        ("Bai giang.DOCX", "Bai giang"),
        ("C:\\Users\\me\\notes.pdf", "notes"),
        ("archive.tar.gz", "archive.tar.gz"),
        (".pdf", "Space"),
        ("x" * 150 + ".pdf", "x" * 100),
    ],
)
def test_default_name_from_filename(filename: str, expected: str) -> None:
    assert default_name_from_filename(filename) == expected


def test_numbered_stays_within_limit() -> None:
    name = numbered("x" * 100, 12)
    assert name.endswith(" (12)") and len(name) == 100
