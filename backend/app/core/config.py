"""
Settings from environment variables (R3: no hard-coded secrets).
"""

from __future__ import annotations

import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------- Database -------
    DATABASE_URL: str = Field(
        description="PostgreSQL connection URL (asyncpg). Example: postgresql+asyncpg://user:pass@host:5432/db"
    )

    # ------- Redis -------
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )

    # ------- Security -------
    SECRET_KEY: str = Field(
        min_length=32,
        description="Secret key for JWT signing (32+ chars). Generate with: openssl rand -hex 32",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="Access token lifetime in minutes",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        description="Refresh token lifetime in days (sliding: each refresh issues a new one)",
    )
    SESSION_MAX_LIFETIME_DAYS: int = Field(
        default=90,
        description="Absolute session lifetime from sign-in; then the user must sign in again",
    )
    REFRESH_REUSE_GRACE_SECONDS: int = Field(
        default=30,
        description=(
            "A just-rotated refresh token reused within this window is rejected without "
            "revoking the session (concurrent tabs); later reuse revokes it (suspected theft)"
        ),
    )

    # ------- Auth rate limits (docs/specs/f2-email-auth.md) -------
    LOGIN_MAX_FAILURES_PER_EMAIL: int = Field(default=5)
    LOGIN_MAX_FAILURES_PER_IP: int = Field(default=20)
    LOGIN_FAILURE_WINDOW_SECONDS: int = Field(default=15 * 60)
    REGISTER_MAX_PER_IP: int = Field(default=5)
    REGISTER_WINDOW_SECONDS: int = Field(default=60 * 60)

    # ------- AI / Gemini -------
    GEMINI_API_KEY: str = Field(
        description="Google Gemini API key (from Google AI Studio). Never commit."
    )
    GEMINI_CHAT_MODEL: str = Field(
        default="gemini-3.5-flash-lite",
        description="Gemini model for chat/generation",
    )
    GEMINI_EMBEDDING_MODEL: str = Field(
        default="gemini-embedding-2",
        description=(
            "Gemini embedding model id (without 'models/' prefix). "
            "Changing it requires re-embedding."
        ),
    )
    EMBEDDING_DIMENSIONS: int = Field(
        default=768,
        description=(
            "Embedding vector dimensions. Changing this requires re-embedding all documents."
        ),
    )

    # ------- Object Storage (S3-compatible / MinIO) -------
    S3_ENDPOINT_URL: str = Field(
        default="http://localhost:9000",
        description="S3-compatible storage endpoint URL",
    )
    S3_BUCKET_NAME: str = Field(
        default="flashcard",
        description="S3 bucket name for document storage",
    )
    S3_ACCESS_KEY: str = Field(
        default="minioadmin",
        description="S3 access key ID",
    )
    S3_SECRET_KEY: str = Field(description="S3 secret access key")

    # ------- Email (Mailpit for local dev) -------
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=1025)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="noreply@flashcard.local")
    SMTP_USE_TLS: bool = Field(default=False)

    # ------- App -------
    SQL_ECHO: bool = Field(
        default=False,
        description="Log SQL with bound parameters. Local debugging only: leaks emails and hashes.",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="App environment: development | staging | production",
    )
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:8081", "http://localhost:19006"],
        description="Allowed CORS origins as JSON array string",
    )

    # ------- Business rules -------
    MAX_FILE_SIZE_MB: int = Field(
        default=20,
        description="Maximum upload file size in megabytes",
    )
    MAX_PAGES: int = Field(
        default=200,
        description="Maximum pages per document",
    )
    MAX_DOCUMENTS_PER_USER: int = Field(
        default=10,
        description="Maximum documents per user",
    )
    USER_DAILY_QUERY_LIMIT: int = Field(
        default=30,
        description="Maximum AI queries per user per day",
    )

    # ------- Document ingestion (docs/specs/f5-document-upload.md) -------
    AI_CONSENT_VERSION: str = Field(
        default="ai-processing-2026-11",
        description="Current version of the AI data-processing notice; bump to re-ask consent",
    )
    REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD: bool = Field(
        default=False, description="Turn on once email verification (F4) exists"
    )
    CHUNK_TARGET_CHARS: int = Field(default=1200)
    CHUNK_OVERLAP_CHARS: int = Field(default=150)
    CHUNK_MAX_CHARS: int = Field(default=6000)
    SCANNED_MIN_CHARS_PER_PAGE: int = Field(default=20)
    EMBED_BATCH_SIZE: int = Field(default=32)
    INGEST_MAX_ATTEMPTS: int = Field(default=3)
    AI_RATE_LIMIT_MAX_WAIT_SECONDS: int = Field(default=60)
    PAUSED_QUOTA_RESUME_MINUTES: int = Field(default=10)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return [str(origin) for origin in v]
        # JSON array string
        try:
            parsed = json.loads(v)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(origin) for origin in parsed]
        # Otherwise a comma-separated string
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got: {v!r}")
        return v

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cookie_secure(self) -> bool:
        """HTTPS-only cookies except for local http development."""
        return not self.is_development

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
