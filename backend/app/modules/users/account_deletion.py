"""
Delete an account and its data (U9).

Rows go with the user through ON DELETE CASCADE (spaces, documents, chunks, chats, decks,
cards, reviews, tokens, consents); AI usage rows keep only anonymous totals (SET NULL).
Stored files are removed by purge jobs, which ARQ retries until storage confirms.
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConfirmationMismatchError
from app.core.logging import get_logger
from app.modules.auth.email import normalize_email
from app.modules.auth.reauth import PasswordConfirmation
from app.modules.documents.queue import JobQueue
from app.modules.documents.repository import DocumentRepository
from app.modules.users.models import User

logger = get_logger(__name__)


class AccountDeletion:
    def __init__(self, session: AsyncSession, queue: JobQueue) -> None:
        self._session = session
        self._queue = queue

    async def delete(self, user: User, *, password: str | None, confirm_email: str | None) -> None:
        await self._confirm(user, password, confirm_email)
        files = await DocumentRepository(self._session).all_for_owner(user.id)
        await self._session.execute(delete(User).where(User.id == user.id))
        await self._session.commit()
        for document_id, storage_key in files:
            await self._queue.enqueue_purge(document_id, storage_key)
        logger.info("Account deleted (user_id=%s, files=%d)", user.id, len(files))

    @staticmethod
    async def _confirm(user: User, password: str | None, confirm_email: str | None) -> None:
        """Password accounts re-enter the password; Google-only accounts retype their email."""
        if user.password_hash is not None:
            await PasswordConfirmation().confirm(user, password or "")
        elif normalize_email(confirm_email or "") != user.email:
            raise ConfirmationMismatchError()
