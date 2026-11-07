"""
Object storage interface (S3-compatible / MinIO).
Tuân thủ R3: S3 credentials từ env vars.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ObjectStorage:
    """
    Interface cho S3-compatible object storage.
    Dùng MinIO ở local dev; chuyển sang S3/R2 chỉ bằng đổi config.
    """

    def __init__(self) -> None:
        # Credentials từ config - R3
        self._endpoint = settings.S3_ENDPOINT_URL
        self._bucket = settings.S3_BUCKET_NAME
        self._access_key = settings.S3_ACCESS_KEY
        self._secret_key = settings.S3_SECRET_KEY

    async def upload_file(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file lên storage.
        Trả về key đã upload.
        """
        # TODO (giai đoạn F5): implement với aiobotocore hoặc httpx
        logger.debug("ObjectStorage.upload_file key=%s size=%d", key, len(data))
        return key

    async def download_file(self, key: str) -> bytes:
        """Download file từ storage."""
        # TODO (giai đoạn F5): implement
        raise NotImplementedError

    async def delete_file(self, key: str) -> None:
        """Xóa file khỏi storage."""
        # TODO (giai đoạn F5): implement
        logger.debug("ObjectStorage.delete_file key=%s", key)

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Tạo presigned URL để client download trực tiếp."""
        # TODO (giai đoạn F5): implement
        return f"{self._endpoint}/{self._bucket}/{key}"


object_storage = ObjectStorage()
