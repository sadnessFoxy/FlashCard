"""
FastAPI application entry point.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from app.api.errors import app_error_handler, generic_error_handler, validation_error_handler
from app.api.middleware import RequestIdMiddleware, TimingMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.db.session import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup và shutdown lifecycle."""
    configure_logging()
    logger.info(
        "Starting FlashCard API (environment=%s)", settings.ENVIRONMENT
    )

    # Startup: có thể kiểm tra kết nối DB, Redis, v.v.
    yield

    # Shutdown: đóng connection pool
    await engine.dispose()
    logger.info("FlashCard API shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FlashCard API",
        description="API for FlashCard learning assistant app",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS - đọc allowed origins từ config (không hardcode)
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
    app.add_exception_handler(PydanticValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)

    # Routers
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
        }

    return app


app = create_app()
