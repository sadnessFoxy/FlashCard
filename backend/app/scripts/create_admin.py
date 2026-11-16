"""
Make an existing account an admin (A1): there is no public admin sign-up.

    python -m app.scripts.create_admin someone@example.com

The account must already exist (sign up in the app first). Run it on the server only.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select

import app.db.all_models  # noqa: F401 - resolve every model before querying
from app.db.session import AsyncSessionLocal
from app.modules.auth.email import normalize_email
from app.modules.users.models import User


async def promote(email: str) -> str:
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == normalize_email(email)))
        if user is None:
            return "No account with this email. Sign up in the app first."
        if user.role == "admin":
            return "Already an admin."
        user.role = "admin"
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
        await session.commit()
        return "Done: this account is now an admin."


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.create_admin <email>")
        raise SystemExit(2)
    print(asyncio.run(promote(sys.argv[1])))


if __name__ == "__main__":
    main()
