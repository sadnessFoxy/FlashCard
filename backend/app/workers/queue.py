"""
ARQ worker entry point. Run with:  arq app.workers.queue.WorkerSettings
"""

from __future__ import annotations

from typing import Any, ClassVar

from arq import cron, func

import app.db.all_models  # noqa: F401  (resolve cross-module foreign keys)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis
from app.db.session import AsyncSessionLocal, engine
from app.integrations.llm_gateway.gateway import LLMGateway
from app.integrations.object_storage import object_storage
from app.modules.ai.providers.gemini import GeminiProvider
from app.modules.documents.ingestion import IngestionPipeline
from app.modules.documents.queue import ArqJobQueue
from app.workers.document_tasks import process_document, purge_document, resume_stalled_documents
from app.workers.settings import INGEST_FUNCTION, PURGE_FUNCTION, redis_settings

logger = get_logger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging()
    provider = GeminiProvider()
    queue = ArqJobQueue()
    ctx["provider"] = provider
    ctx["queue"] = queue
    ctx["pipeline"] = IngestionPipeline(
        AsyncSessionLocal, object_storage, LLMGateway(provider), queue
    )
    logger.info("Worker started (environment=%s)", settings.ENVIRONMENT)


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["provider"].close()
    await ctx["queue"].close()
    await engine.dispose()
    await close_redis()


class WorkerSettings:
    redis_settings = redis_settings()
    functions: ClassVar = [
        func(process_document, name=INGEST_FUNCTION, keep_result=0),
        func(purge_document, name=PURGE_FUNCTION, keep_result=0, max_tries=10),
    ]
    cron_jobs: ClassVar = [
        cron(
            resume_stalled_documents,
            minute=set(range(0, 60, settings.PAUSED_QUOTA_RESUME_MINUTES)),
            run_at_startup=True,
        )
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 4
    job_timeout = 900  # seconds; a 200-page PDF with rate-limit waits stays well inside
