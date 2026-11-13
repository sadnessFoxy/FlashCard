"""
Split page texts into chunks that remember their page range (spec f5 section 6).

Structure first, size second (citations must point at the right page, R7):
- a chapter or section heading always starts a new chunk;
- a new page starts a new chunk unless the current one is still small (< target / 4);
- within continuous text, paragraphs are packed up to ~target characters and the next chunk
  starts with ~overlap characters of the previous one. No overlap crosses a heading or page
  boundary, so a chunk never borrows text from another chapter or page.
Oversized paragraphs are split at sentence ends, then hard-cut at max_chars.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?…;:])\s+")
_LINE_ENDS_PARAGRAPH = re.compile(r"[.!?…:;]\s*$")
_HEADING = re.compile(
    r"^(chương|chuong|bài|phần|mục|chapter|section|part|lesson)\s+[\w.]+",
    re.IGNORECASE,
)
_MAX_HEADING_CHARS = 120


@dataclass(frozen=True)
class Chunk:
    page_start: int  # 1-based
    page_end: int
    content: str


@dataclass(frozen=True)
class _Unit:
    page: int
    text: str
    heading: bool = False


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def _is_heading(line: str) -> bool:
    return len(line) <= _MAX_HEADING_CHARS and bool(_HEADING.match(line))


def split_paragraphs(page_text: str) -> list[tuple[str, bool]]:
    """(paragraph, is_heading). Blank lines split paragraphs; without them (common with
    pypdf), a line ending in sentence punctuation does, and headings stand alone."""
    out: list[tuple[str, bool]] = []
    for block in _PARAGRAPH_BREAK.split(page_text.replace("\r\n", "\n")):
        current: list[str] = []
        for raw in block.split("\n"):
            line = _clean(raw)
            if not line:
                continue
            if _is_heading(line):
                if current:
                    out.append((" ".join(current), False))
                    current = []
                out.append((line, True))
                continue
            current.append(line)
            if _LINE_ENDS_PARAGRAPH.search(line):
                out.append((" ".join(current), False))
                current = []
        if current:
            out.append((" ".join(current), False))
    return out


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text):
        while len(sentence) > max_chars:  # no sentence end in range: hard cut
            pieces.append(sentence[:max_chars])
            sentence = sentence[max_chars:]
        if current and len(current) + 1 + len(sentence) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def _tail(text: str, overlap: int) -> str:
    if overlap <= 0:
        return ""
    if len(text) <= overlap:
        return text
    cut = text[-overlap:]
    space = cut.find(" ")
    return cut[space + 1 :] if 0 <= space < len(cut) - 1 else cut


def chunk_pages(
    pages: list[str], *, target_chars: int, overlap_chars: int, max_chars: int
) -> list[Chunk]:
    piece_limit = max(1, max_chars - overlap_chars - 1)
    units = [
        _Unit(page=i + 1, text=piece, heading=heading)
        for i, page in enumerate(pages)
        for para, heading in split_paragraphs(page)
        for piece in _split_long(para, piece_limit)
    ]

    chunks: list[Chunk] = []
    buf: list[_Unit] = []
    prefix = ""  # overlap carried from the previous chunk
    prefix_page = 0
    size = 0

    def flush(carry_overlap: bool) -> None:
        nonlocal buf, prefix, prefix_page, size
        if not buf:
            return
        body = " ".join(u.text for u in buf)
        content = f"{prefix} {body}".strip() if prefix else body
        start = prefix_page if prefix else buf[0].page
        chunks.append(Chunk(page_start=start, page_end=buf[-1].page, content=content[:max_chars]))
        prefix = _tail(body, overlap_chars) if carry_overlap else ""
        prefix_page = buf[-1].page
        buf = []
        size = len(prefix)

    for unit in units:
        if buf:
            new_page = unit.page != buf[-1].page
            if unit.heading or (new_page and size >= target_chars // 4):
                flush(carry_overlap=False)
            elif size + 1 + len(unit.text) > target_chars:
                flush(carry_overlap=True)
        buf.append(unit)
        size += len(unit.text) + 1
    flush(carry_overlap=False)
    return chunks
