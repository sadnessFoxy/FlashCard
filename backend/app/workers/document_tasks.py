"""ARQ task functions for document ingestion (logic lives in documents.ingestion)."""

from __future__ import annotations

import uuid
from typing import Any

from arq import Retry

from app.modules.documents.ingestion import IngestionPipeline


def _pipeline(ctx: dict[str, Any]) -> IngestionPipeline:
    pipeline: IngestionPipeline = ctx["pipeline"]
    return pipeline


async def process_document(ctx: dict[str, Any], document_id: str) -> str | None:
    return await _pipeline(ctx).process(uuid.UUID(document_id))


async def resume_stalled_documents(ctx: dict[str, Any]) -> int:
    return len(await _pipeline(ctx).resume_stalled())


async def purge_document(ctx: dict[str, Any], document_id: str, storage_key: str) -> None:
    if not await _pipeline(ctx).purge(uuid.UUID(document_id), storage_key):
        raise Retry(defer=60)  # storage hiccup: ARQ retries (max_tries)
