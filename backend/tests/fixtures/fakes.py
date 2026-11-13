"""Test doubles for storage and the job queue."""

from __future__ import annotations

import re
import uuid

from app.integrations.email import OutgoingEmail
from app.integrations.object_storage import StorageError


class InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail = False
        self.downloads = 0

    async def upload_file(self, key: str, data: bytes, content_type: str = "") -> str:
        if self.fail:
            raise StorageError()
        self.objects[key] = data
        return key

    async def download_file(self, key: str) -> bytes:
        self.downloads += 1
        if self.fail or key not in self.objects:
            raise StorageError()
        return self.objects[key]

    async def delete_file(self, key: str) -> None:
        self.objects.pop(key, None)


class RecordingQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[uuid.UUID, float]] = []
        self.purges: list[tuple[uuid.UUID, str]] = []

    async def enqueue_ingest(self, document_id: uuid.UUID, defer_seconds: float = 0) -> None:
        self.jobs.append((document_id, defer_seconds))

    async def enqueue_purge(self, document_id: uuid.UUID, storage_key: str) -> None:
        self.purges.append((document_id, storage_key))


class RecordingMailer:
    """Keeps sent emails in memory; tests read codes from them."""

    def __init__(self) -> None:
        self.sent: list[OutgoingEmail] = []

    async def send(self, email: OutgoingEmail) -> None:
        self.sent.append(email)

    def last_code(self, to: str) -> str:
        for email in reversed(self.sent):
            if email.to == to:
                match = re.search(r"\b(\d{6})\b", email.text)
                if match:
                    return match.group(1)
        raise AssertionError(f"no code sent to {to}")
