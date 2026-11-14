"""
The page texts of a stored document, whatever their origin (docs/specs/f14-scans.md).

Text-layer PDFs and Word files are read from the file itself. For scanned PDFs the AI
transcription is kept next to the file as JSON (`<storage_key>.ocr.json`), because the
PDF has no text to read again. Purging a document removes both objects.
"""

from __future__ import annotations

import json

from app.integrations.object_storage import ObjectStorage
from app.modules.documents.formats import UnsupportedFileError, extract_page, extract_pages
from app.modules.documents.models import Document

AI_OCR = "ai_ocr"


def ocr_text_key(storage_key: str) -> str:
    return f"{storage_key}.ocr.json"


async def save_ocr_text(storage: ObjectStorage, storage_key: str, pages: list[str]) -> None:
    payload = json.dumps(pages, ensure_ascii=False).encode()
    await storage.upload_file(ocr_text_key(storage_key), payload, "application/json")


async def document_pages(storage: ObjectStorage, document: Document) -> list[str]:
    """Every page's text; UnsupportedFileError when the file cannot be read."""
    if document.text_source == AI_OCR:
        return await _ocr_pages(storage, document)
    return extract_pages(await storage.download_file(document.storage_key), document.file_kind)


async def document_page(storage: ObjectStorage, document: Document, page: int) -> str:
    """One 1-based page's text ("" when out of range)."""
    if document.text_source == AI_OCR:
        pages = await _ocr_pages(storage, document)
        return pages[page - 1] if 1 <= page <= len(pages) else ""
    data = await storage.download_file(document.storage_key)
    return extract_page(data, document.file_kind, page)


async def _ocr_pages(storage: ObjectStorage, document: Document) -> list[str]:
    raw = await storage.download_file(ocr_text_key(document.storage_key))
    try:
        pages = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UnsupportedFileError from exc
    return [str(p) for p in pages]
