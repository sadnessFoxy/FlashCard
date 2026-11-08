"""
ARQ tasks cho xử lý tài liệu nền.
Trích văn bản, chia đoạn, embedding, cập nhật trạng thái.
Tuân thủ R6: trạng thái chỉ đổi theo máy trạng thái trong DATA_MODEL.md.
Tuân thủ R8: lỗi hết hạn mức -> PAUSED_QUOTA, không FAILED.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


async def process_document(ctx: dict, document_id: str) -> None:  # type: ignore[type-arg]
    """
    Xử lý tài liệu: trích văn bản, chia đoạn, embedding.
    Trạng thái: PENDING -> PROCESSING -> READY (hoặc FAILED/PAUSED_QUOTA).
    """
    logger.info("Processing document document_id=%s", document_id)
    # TODO (giai đoạn F5): implement full pipeline
    # 1. Tải file từ object storage
    # 2. Trích văn bản (PDF/Word/scan)
    # 3. Chia đoạn
    # 4. Gọi gateway.embed() -> nếu AiRateLimitedError: set PAUSED_QUOTA (R8)
    # 5. Lưu vectors vào pgvector
    # 6. Cập nhật trạng thái -> READY
