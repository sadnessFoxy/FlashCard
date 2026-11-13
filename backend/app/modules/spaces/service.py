"""Space operations (docs/specs/f4b-spaces.md). Logs carry ids only, never names."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, SpaceNameTakenError
from app.core.logging import get_logger
from app.modules.spaces.models import Space
from app.modules.spaces.names import default_name_from_filename, numbered
from app.modules.spaces.repository import SpaceRepository

logger = get_logger(__name__)


class SpaceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SpaceRepository(session)

    async def list(self, owner_id: uuid.UUID) -> list[Space]:
        return await self._repo.list_for_owner(owner_id)

    async def get(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> Space:
        """The owner's space; someone else's space is reported as not found."""
        space = await self._repo.get_for_owner(owner_id, space_id)
        if space is None:
            raise NotFoundError("Space")
        return space

    async def create(self, owner_id: uuid.UUID, name: str) -> Space:
        """`name` must already be validated (see names.validate_name)."""
        space = await self._insert(owner_id, name)
        logger.info("Space created (space_id=%s, user_id=%s)", space.id, owner_id)
        return space

    async def rename(self, owner_id: uuid.UUID, space_id: uuid.UUID, name: str) -> Space:
        space = await self.get(owner_id, space_id)
        if space.name == name:
            return space
        space.name = name
        space.updated_at = datetime.now(UTC)
        try:
            async with self._session.begin_nested():
                await self._session.flush()
        except IntegrityError:
            raise SpaceNameTakenError() from None
        return space

    async def delete(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> None:
        # Callers with documents use DocumentService.delete_space, which purges files first.
        space = await self.get(owner_id, space_id)
        await self._repo.delete(space)
        logger.info("Space deleted (space_id=%s, user_id=%s)", space_id, owner_id)

    async def create_default_for_document(self, owner_id: uuid.UUID, filename: str) -> Space:
        """Default space for a first upload (U16): named after the file, numbered if taken.
        Called by the upload flow in F5."""
        base = default_name_from_filename(filename)
        taken = await self._repo.names_like(owner_id, base)
        name, n = base, 1
        while name.lower() in taken:
            n += 1
            name = numbered(base, n)
        return await self.create(owner_id, name)

    async def _insert(self, owner_id: uuid.UUID, name: str) -> Space:
        try:
            async with self._session.begin_nested():
                return await self._repo.add(Space(owner_id=owner_id, name=name))
        except IntegrityError:
            raise SpaceNameTakenError() from None
