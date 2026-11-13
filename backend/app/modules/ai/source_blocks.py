"""
Numbered `<source>` blocks for prompts built from the learner's documents.
Source text is untrusted (R7): it is escaped so it cannot close or fake a tag.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from typing import Protocol


class SourceLike(Protocol):
    @property
    def document_name(self) -> str: ...
    @property
    def page_start(self) -> int: ...
    @property
    def page_end(self) -> int: ...
    @property
    def content(self) -> str: ...


def page_label(source: SourceLike) -> str:
    if source.page_start == source.page_end:
        return str(source.page_start)
    return f"{source.page_start}-{source.page_end}"


def format_sources(sources: Sequence[SourceLike]) -> list[str]:
    """One block per source, numbered from 1 in the given order."""
    return [
        f'<source id="{i}" document="{escape(s.document_name)}" pages="{page_label(s)}">\n'
        f"{escape(s.content, quote=False)}\n</source>"
        for i, s in enumerate(sources, start=1)
    ]
