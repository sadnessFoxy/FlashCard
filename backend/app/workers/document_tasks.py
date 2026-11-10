"""
ARQ tasks for background document processing:
extract text, chunk, embed, update status.
R6: status changes follow the state machine in docs/DATA_MODEL.md.
R8: quota errors -> PAUSED_QUOTA, never FAILED.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


async def process_document(ctx: dict, document_id: str) -> None:  # type: ignore[type-arg]
    """
    Process a document: extract text, chunk, embed.
    Status: QUEUED -> PROCESSING -> READY (or FAILED / PAUSED_QUOTA).
    """
    logger.info("Processing document document_id=%s", document_id)
    # TODO(F5): implement the pipeline
    # 1. Fetch the file from object storage
    # 2. Extract text (PDF / Word / scan)
    # 3. Chunk
    # 4. gateway.embed(); on quota errors set PAUSED_QUOTA (R8)
    # 5. Store vectors in pgvector
    # 6. Set status READY
