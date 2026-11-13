"""
Citation snapshots stored with assistant messages (docs/specs/f7-qa.md section 4).
A snapshot keeps name, pages and snippet so it still renders after the document is deleted.
"""

from __future__ import annotations

from typing import Any

from app.modules.chat.prompts import cited_indexes
from app.modules.documents.retrieval import RetrievedChunk

SNIPPET_CHARS = 600

Citation = dict[str, Any]


def snapshot(index: int, chunk: RetrievedChunk) -> Citation:
    snippet = chunk.content.strip()
    if len(snippet) > SNIPPET_CHARS:
        snippet = snippet[:SNIPPET_CHARS].rstrip() + "…"
    return {
        "index": index,
        "document_id": str(chunk.document_id),
        "document_name": chunk.document_name,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "snippet": snippet,
    }


def snapshots(sources: list[RetrievedChunk]) -> list[Citation]:
    """Numbered 1..n in the order the sources were given to the model."""
    return [snapshot(i, s) for i, s in enumerate(sources, start=1)]


def keep_cited(answer: str, citations: list[Citation]) -> list[Citation]:
    """Only the sources the answer cites; all of them when it cites none."""
    cited = cited_indexes(answer, len(citations))
    return [citations[i - 1] for i in cited] if cited else citations


def mark_deleted(citations: list[Citation], live_document_ids: set[str]) -> list[Citation]:
    """Null `document_id` for documents that no longer exist."""
    return [
        {
            **c,
            "document_id": c["document_id"] if c.get("document_id") in live_document_ids else None,
        }
        for c in citations
    ]


def cited_document_ids(citations: list[Citation]) -> set[str]:
    return {c["document_id"] for c in citations if c.get("document_id")}
