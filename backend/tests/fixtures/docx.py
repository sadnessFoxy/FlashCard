"""Build small .docx files for tests (word/document.xml inside a zip)."""

from __future__ import annotations

import io
import zipfile
from html import escape

_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
PAGE_BREAK = '<w:r><w:br w:type="page"/></w:r>'


def make_docx(
    pages: list[list[str]], *, record_breaks: bool = True, body: str | None = None
) -> bytes:
    """Each page is a list of paragraphs; pages are joined by Word-style page breaks."""
    if body is None:
        paragraphs = []
        for i, page in enumerate(pages):
            for j, text in enumerate(page):
                brk = PAGE_BREAK if (record_breaks and i > 0 and j == 0) else ""
                paragraphs.append(f"<w:p>{brk}<w:r><w:t>{escape(text)}</w:t></w:r></w:p>")
        body = (
            f'<?xml version="1.0"?><w:document {_NS}>'
            f"<w:body>{''.join(paragraphs)}</w:body></w:document>"
        )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", body)
    return buffer.getvalue()
