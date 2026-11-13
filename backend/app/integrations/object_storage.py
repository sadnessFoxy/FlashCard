"""
S3-compatible object storage (SeaweedFS locally; S3/R2 is a config change). R3: keys from env.
boto3 is synchronous, so calls run in a worker thread.
"""

from __future__ import annotations

import asyncio
from functools import cached_property
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = get_logger(__name__)


class StorageError(Exception):
    """Object storage unavailable or the operation failed."""


class ObjectStorage:
    def __init__(self) -> None:
        self._bucket = settings.S3_BUCKET_NAME
        self._bucket_checked = False

    @cached_property
    def _client(self) -> S3Client:
        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=5,
                read_timeout=60,
            ),
        )

    def _ensure_bucket(self) -> None:
        if self._bucket_checked:
            return
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            if not settings.is_development:
                raise
            # Local dev convenience; real buckets are provisioned explicitly.
            self._client.create_bucket(Bucket=self._bucket)
            logger.info("Created storage bucket for development")
        self._bucket_checked = True

    async def _run(self, fn: object, *args: object, **kwargs: object) -> object:
        def call() -> object:
            self._ensure_bucket()
            return fn(*args, **kwargs)  # type: ignore[operator]

        try:
            return await asyncio.to_thread(call)
        except (BotoCoreError, ClientError) as exc:
            logger.warning("Object storage error: %s", type(exc).__name__)
            raise StorageError() from exc

    async def upload_file(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        await self._run(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    async def download_file(self, key: str) -> bytes:
        response = await self._run(self._client.get_object, Bucket=self._bucket, Key=key)
        body = response["Body"]  # type: ignore[index]
        return await asyncio.to_thread(body.read)

    async def delete_file(self, key: str) -> None:
        await self._run(self._client.delete_object, Bucket=self._bucket, Key=key)


object_storage = ObjectStorage()


def get_storage() -> ObjectStorage:
    return object_storage
