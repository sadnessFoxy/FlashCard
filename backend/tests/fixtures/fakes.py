"""Test doubles for storage and the job queue."""

from __future__ import annotations

import uuid

from app.integrations.object_storage import StorageError


class InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail = False

    async def upload_file(self, key: str, data: bytes, content_type: str = "") -> str:
        if self.fail:
            raise StorageError()
        self.objects[key] = data
        return key

    async def download_file(self, key: str) -> bytes:
        if self.fail or key not in self.objects:
            raise StorageError()
        return self.objects[key]

    async def delete_file(self, key: str) -> None:
        self.objects.pop(key, None)


class RecordingQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[uuid.UUID, float]] = []

    async def enqueue_ingest(self, document_id: uuid.UUID, defer_seconds: float = 0) -> None:
        self.jobs.append((document_id, defer_seconds))
