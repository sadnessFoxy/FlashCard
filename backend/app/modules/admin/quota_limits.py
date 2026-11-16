"""The daily question limit of one user: an admin override if active, else the runtime default."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select

from app.db.session import AsyncSessionLocal
from app.modules.admin.models import UserQuotaOverride
from app.modules.admin.runtime_config import runtime_config


async def question_limit(user_id: uuid.UUID) -> int:
    async with AsyncSessionLocal() as session:
        override = await session.scalar(
            select(UserQuotaOverride.daily_limit).where(
                UserQuotaOverride.user_id == user_id,
                or_(
                    UserQuotaOverride.expires_at.is_(None),
                    UserQuotaOverride.expires_at > datetime.now(UTC),
                ),
            )
        )
    if override is not None:
        return int(override)
    return int(await runtime_config.get("user_daily_query_limit"))
