"""
Vector retrieval over the owner's READY documents (docs/specs/f7-qa.md, R4).

Ownership, space, READY status and the selected document set are SQL filters applied
before ranking, so nothing outside them can ever reach the AI context.
"""

from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, DocumentChunk
from app.modules.documents.states import READY


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_start: int
    page_end: int
    content: str
    distance: float


async def search_chunks(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    space_id: uuid.UUID,
    query_vector: list[float],
    document_ids: list[uuid.UUID] | None,
    candidates: int,
) -> list[RetrievedChunk]:
    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            Document.filename,
            DocumentChunk.page_start,
            DocumentChunk.page_end,
            DocumentChunk.content,
            distance,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.owner_id == owner_id,
            Document.owner_id == owner_id,
            Document.space_id == space_id,
            Document.status == READY,
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(candidates)
    )
    if document_ids is not None:
        stmt = stmt.where(Document.id.in_(document_ids))
    rows = (await session.execute(stmt)).all()
    return [
        RetrievedChunk(
            chunk_id=r[0],
            document_id=r[1],
            document_name=r[2],
            page_start=r[3],
            page_end=r[4],
            content=r[5],
            distance=float(r[6]),
        )
        for r in rows
    ]


def select_sources(
    candidates: list[RetrievedChunk], *, max_distance: float, top_k: int, per_document: int
) -> list[RetrievedChunk]:
    """Relevant chunks only, best first, at most `per_document` from any one document."""
    picked: list[RetrievedChunk] = []
    per_doc: Counter[uuid.UUID] = Counter()
    for chunk in sorted(candidates, key=lambda c: c.distance):
        if chunk.distance > max_distance:
            break
        if per_doc[chunk.document_id] >= per_document:
            continue
        picked.append(chunk)
        per_doc[chunk.document_id] += 1
        if len(picked) == top_k:
            break
    return picked


async def ready_document_ids(
    session: AsyncSession, owner_id: uuid.UUID, space_id: uuid.UUID
) -> list[uuid.UUID]:
    result = await session.execute(
        select(Document.id).where(
            Document.owner_id == owner_id, Document.space_id == space_id, Document.status == READY
        )
    )
    return list(result.scalars())


_WORD = re.compile(r"\w{3,}")


async def keyword_search(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    space_id: uuid.UUID,
    question: str,
    document_ids: list[uuid.UUID] | None,
    limit: int,
) -> list[RetrievedChunk]:
    """Lexical fallback when the query cannot be embedded (AI down, U8). Same R4 filters."""
    words = list(dict.fromkeys(w.lower() for w in _WORD.findall(question)))[:20]
    if not words:
        return []
    # Words are \w only, so joining them cannot inject tsquery operators.
    query = func.to_tsquery("simple", " | ".join(words))
    vector = func.to_tsvector("simple", DocumentChunk.content)
    rank = func.ts_rank(vector, query).label("rank")
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            Document.filename,
            DocumentChunk.page_start,
            DocumentChunk.page_end,
            DocumentChunk.content,
            rank,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.owner_id == owner_id,
            Document.owner_id == owner_id,
            Document.space_id == space_id,
            Document.status == READY,
            vector.op("@@")(query),
        )
        .order_by(rank.desc())
        .limit(limit)
    )
    if document_ids is not None:
        stmt = stmt.where(Document.id.in_(document_ids))
    rows = (await session.execute(stmt)).all()
    # Rank order is kept by mapping it onto an increasing pseudo-distance.
    return [
        RetrievedChunk(
            chunk_id=r[0],
            document_id=r[1],
            document_name=r[2],
            page_start=r[3],
            page_end=r[4],
            content=r[5],
            distance=i / max(1, len(rows)),
        )
        for i, r in enumerate(rows)
    ]
