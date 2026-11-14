"""PDF inspection and per-page text extraction with pypdf (spec f5 section 6)."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

PDF_MAGIC = b"%PDF-"

# pypdf warns loudly about slightly malformed files; those warnings are not actionable.
logging.getLogger("pypdf").setLevel(logging.ERROR)


class NotAPdfError(Exception):
    """Bytes are not a readable PDF."""


@dataclass(frozen=True)
class PdfInfo:
    page_count: int
    encrypted: bool


def looks_like_pdf(data: bytes) -> bool:
    # The header may follow a few junk bytes; the spec allows it within the first 1 KB.
    return PDF_MAGIC in data[:1024]


def inspect_pdf(data: bytes) -> PdfInfo:
    if not looks_like_pdf(data):
        raise NotAPdfError
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            return PdfInfo(page_count=0, encrypted=True)
        return PdfInfo(page_count=len(reader.pages), encrypted=False)
    except (PdfReadError, ValueError, KeyError, TypeError) as exc:
        raise NotAPdfError from exc


def extract_pages(data: bytes) -> list[str]:
    """Text of every page, in order (empty string for pages without text)."""
    try:
        reader = PdfReader(io.BytesIO(data))
        return [(page.extract_text() or "") for page in reader.pages]
    except (PdfReadError, ValueError, KeyError, TypeError) as exc:
        raise NotAPdfError from exc


def extract_page(data: bytes, page_number: int) -> str:
    """Text of one 1-based page; only that page is parsed."""
    try:
        reader = PdfReader(io.BytesIO(data))
        return reader.pages[page_number - 1].extract_text() or ""
    except (PdfReadError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise NotAPdfError from exc


def split_pages(data: bytes) -> list[bytes]:
    """Each page as its own one-page PDF (for page-by-page AI reading)."""
    try:
        reader = PdfReader(io.BytesIO(data))
        out: list[bytes] = []
        for page in reader.pages:
            writer = PdfWriter()
            writer.add_page(page)
            buffer = io.BytesIO()
            writer.write(buffer)
            out.append(buffer.getvalue())
        return out
    except (PdfReadError, ValueError, KeyError, TypeError) as exc:
        raise NotAPdfError from exc


def looks_scanned(pages: list[str], min_chars_per_page: int) -> bool:
    """No usable text layer: average visible characters per page below the threshold."""
    if not pages:
        return True
    visible = sum(len("".join(p.split())) for p in pages)
    return visible / len(pages) < min_chars_per_page
