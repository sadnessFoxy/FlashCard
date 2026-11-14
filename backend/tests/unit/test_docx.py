"""F13: reading Word files safely and by page."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.modules.documents import docx
from app.modules.documents.formats import UnsupportedFileError, extract_page, inspect_file
from tests.fixtures.docx import make_docx
from tests.fixtures.pdfs import make_pdf


def test_pages_follow_recorded_page_breaks() -> None:
    data = make_docx([["Chương 1. Giới hạn", "Giới hạn mô tả..."], ["Chương 2. Đạo hàm"]])
    assert docx.extract_pages(data) == [
        "Chương 1. Giới hạn\n\nGiới hạn mô tả...",
        "Chương 2. Đạo hàm",
    ]


def test_without_breaks_pages_are_cut_by_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "DOCX_CHARS_PER_PAGE", 25)
    data = make_docx([["a" * 20, "b" * 20, "c" * 3]], record_breaks=False)
    assert docx.extract_pages(data) == ["a" * 20, "b" * 20 + "\n\n" + "c" * 3]


def test_format_is_detected_from_content_not_name() -> None:
    assert inspect_file(make_docx([["x"], ["y"]])).kind == "docx"
    assert inspect_file(make_docx([["x"], ["y"]])).page_count == 2
    assert inspect_file(make_pdf(["p1"])).kind == "pdf"
    with pytest.raises(UnsupportedFileError):
        inspect_file(b"PK\x03\x04 not really a zip")
    with pytest.raises(UnsupportedFileError):
        inspect_file(b"plain text")


def test_xml_entities_are_refused() -> None:
    evil = (
        '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "aaaaaaaaaa">]>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>&a;</w:t></w:r></w:p></w:body></w:document>"
    )
    with pytest.raises(docx.NotADocxError):
        docx.extract_pages(make_docx([], body=evil))


def test_oversized_body_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "DOCX_MAX_BODY_BYTES", 100)
    with pytest.raises(docx.NotADocxError):
        docx.extract_pages(make_docx([["x" * 500]]))


def test_single_page_for_the_citation_view() -> None:
    data = make_docx([["Một."], ["Hai."]])
    assert extract_page(data, "docx", 2) == "Hai."
    assert extract_page(data, "docx", 9) == ""
