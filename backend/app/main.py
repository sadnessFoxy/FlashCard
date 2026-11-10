"""
FastAPI application entry point.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.errors import (
    app_error_handler,
    generic_error_handler,
    http_error_handler,
    request_validation_error_handler,
    validation_error_handler,
)
from app.api.middleware import CsrfOriginMiddleware, RequestIdMiddleware, TimingMiddleware
from app.api.router import api_router
from app.api.system import router as system_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis
from app.db.session import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown."""
    configure_logging()
    logger.info("Starting FlashCard API (environment=%s)", settings.ENVIRONMENT)

    yield

    # Close the DB pool and Redis
    await engine.dispose()
    await close_redis()
    logger.info("FlashCard API shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FlashCard API",
        description="API for FlashCard learning assistant app",
        version=__version__,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Added before CORS so it runs inside it
    app.add_middleware(CsrfOriginMiddleware, allowed_origins=settings.CORS_ORIGINS)

    # CORS origins come from config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Exception handlers
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(PydanticValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)

    # Routers
    app.include_router(system_router)
    app.include_router(api_router)

    return app


app = create_app()
