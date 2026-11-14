"""
Word (.docx) text by page, with the standard library only (docs/specs/f13-word.md).

A .docx is a zip with the body in word/document.xml. Pages follow the page breaks Word
records (explicit breaks and the "last rendered" breaks it saves); a file without any
is cut into pages of about DOCX_CHARS_PER_PAGE characters. User files are untrusted:
XML with a DTD or entities is refused (no entity expansion) and the unzipped body size
is capped (no zip bombs).
"""

from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree

from app.core.config import settings

BODY = "word/document.xml"
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_ZIP_MAGIC = b"PK\x03\x04"


class NotADocxError(Exception):
    """Bytes are not a readable .docx."""


def looks_like_docx(data: bytes) -> bool:
    if not data.startswith(_ZIP_MAGIC):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            return BODY in archive.namelist()
    except zipfile.BadZipFile:
        return False


def extract_pages(data: bytes) -> list[str]:
    """Text of every page, in order; paragraphs separated by blank lines."""
    pages = _pages_from_breaks(_paragraphs(_body(data)))
    if len(pages) == 1:
        return _pages_by_length(pages[0])
    return [p.strip() for p in pages]


def _body(data: bytes) -> ElementTree.Element:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo(BODY)
            if info.file_size > settings.DOCX_MAX_BODY_BYTES:
                raise NotADocxError("body too large")
            xml = archive.read(BODY)
    except (zipfile.BadZipFile, KeyError) as exc:
        raise NotADocxError from exc
    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
        raise NotADocxError("DTD not allowed")
    try:
        # Safe: DTDs and entities are refused above, which is what defusedxml guards against.
        return ElementTree.fromstring(xml)  # noqa: S314
    except ElementTree.ParseError as exc:
        raise NotADocxError from exc


def _paragraphs(root: ElementTree.Element) -> list[tuple[str, bool]]:
    """(text, page break before it) for every paragraph in reading order."""
    out: list[tuple[str, bool]] = []
    for paragraph in root.iter(f"{_W}p"):
        parts: list[str] = []
        breaks_page = False
        for node in paragraph.iter():
            if node.tag == f"{_W}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{_W}tab":
                parts.append("\t")
            elif node.tag == f"{_W}br" and node.get(f"{_W}type") == "page":
                breaks_page = breaks_page or not parts
            elif node.tag == f"{_W}lastRenderedPageBreak":
                breaks_page = breaks_page or not parts
        out.append(("".join(parts), breaks_page))
    return out


def _pages_from_breaks(paragraphs: list[tuple[str, bool]]) -> list[str]:
    pages: list[list[str]] = [[]]
    for text, breaks_page in paragraphs:
        if breaks_page and any(p.strip() for p in pages[-1]):
            pages.append([])
        if text.strip():
            pages[-1].append(text)
    return ["\n\n".join(page) for page in pages]


def _pages_by_length(text: str) -> list[str]:
    """No recorded page breaks: pack whole paragraphs into pages of about N characters."""
    limit = settings.DOCX_CHARS_PER_PAGE
    pages: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if current and len(current) + len(paragraph) > limit:
            pages.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    pages.append(current)
    return [p.strip() for p in pages]
