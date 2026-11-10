"""Data access for `spaces`. Every query is scoped to the owner (R4)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.spaces.models import Space


class SpaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_owner(self, owner_id: uuid.UUID) -> list[Space]:
        result = await self._session.execute(
            select(Space)
            .where(Space.owner_id == owner_id)
            .order_by(Space.updated_at.desc(), Space.id)
        )
        return list(result.scalars())

    async def get_for_owner(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> Space | None:
        result = await self._session.execute(
            select(Space).where(Space.id == space_id, Space.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def names_like(self, owner_id: uuid.UUID, base: str) -> set[str]:
        """Lowercased names starting with `base` (for picking a free default name)."""
        result = await self._session.execute(
            select(func.lower(Space.name)).where(
                Space.owner_id == owner_id,
                func.lower(Space.name).startswith(base.lower(), autoescape=True),
            )
        )
        return set(result.scalars())

    async def add(self, space: Space) -> Space:
        self._session.add(space)
        await self._session.flush()
        return space

    async def delete(self, space: Space) -> None:
        await self._session.delete(space)
        await self._session.flush()
