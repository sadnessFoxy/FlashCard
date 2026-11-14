"""
Split a document into chapters for summaries (U15 step 2): chapter and section headings
found by the same detector chunking uses; without usable headings, fixed page ranges.
Pure functions, so the rules are easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.documents.chunking import split_paragraphs


@dataclass(frozen=True)
class SectionDraft:
    title: str | None  # None for a page-range part
    page_start: int
    page_end: int


def find_sections(
    pages: list[str], *, pages_per_part: int, max_sections: int
) -> list[SectionDraft]:
    headings = _headings(pages)
    if not headings or len(headings) > max_sections:
        return page_parts(len(pages), pages_per_part)

    sections: list[SectionDraft] = []
    first_page = headings[0][1]
    if first_page > 1:  # text before the first heading (preface, contents...)
        sections.append(SectionDraft(None, 1, first_page - 1))
    for i, (title, start) in enumerate(headings):
        next_start = headings[i + 1][1] if i + 1 < len(headings) else len(pages) + 1
        sections.append(SectionDraft(title, start, max(start, next_start - 1)))
    return sections


def page_parts(page_count: int, pages_per_part: int) -> list[SectionDraft]:
    size = max(1, pages_per_part)
    return [
        SectionDraft(None, start, min(start + size - 1, page_count))
        for start in range(1, max(page_count, 1) + 1, size)
    ]


def _headings(pages: list[str]) -> list[tuple[str, int]]:
    """(title, 1-based page) of every heading, in reading order."""
    found = []
    for number, text in enumerate(pages, start=1):
        for paragraph, is_heading in split_paragraphs(text):
            if is_heading:
                found.append((paragraph, number))
    return found
