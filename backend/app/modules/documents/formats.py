"""
Supported document formats behind one interface (PDF, Word .docx).
Everything that reads document content goes through here, so adding a format is local.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.modules.documents import docx, pdf

FileKind = Literal["pdf", "docx"]

CONTENT_TYPES: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class UnsupportedFileError(Exception):
    """Neither a readable PDF nor a readable .docx."""


@dataclass(frozen=True)
class FileInfo:
    kind: FileKind
    page_count: int
    encrypted: bool


def inspect_file(data: bytes) -> FileInfo:
    """Recognize the format from the bytes (never from the file name)."""
    if pdf.looks_like_pdf(data):
        try:
            info = pdf.inspect_pdf(data)
        except pdf.NotAPdfError as exc:
            raise UnsupportedFileError from exc
        return FileInfo("pdf", info.page_count, info.encrypted)
    if docx.looks_like_docx(data):
        try:
            return FileInfo("docx", len(docx.extract_pages(data)), encrypted=False)
        except docx.NotADocxError as exc:
            raise UnsupportedFileError from exc
    raise UnsupportedFileError


def extract_pages(data: bytes, kind: str) -> list[str]:
    """Text of every page; UnsupportedFileError when the file cannot be read."""
    try:
        if kind == "docx":
            return docx.extract_pages(data)
        return pdf.extract_pages(data)
    except (pdf.NotAPdfError, docx.NotADocxError) as exc:
        raise UnsupportedFileError from exc


def extract_page(data: bytes, kind: str, page_number: int) -> str:
    """Text of one 1-based page (PDF parses only that page)."""
    if kind == "pdf":
        try:
            return pdf.extract_page(data, page_number)
        except pdf.NotAPdfError as exc:
            raise UnsupportedFileError from exc
    pages = extract_pages(data, kind)
    return pages[page_number - 1] if 1 <= page_number <= len(pages) else ""
