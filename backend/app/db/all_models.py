"""
Import every model module so SQLAlchemy can resolve string foreign keys like "users.id".
Any process that does not import the full API (the ARQ worker, Alembic) imports this first.
Add new model modules here.
"""

from __future__ import annotations

import app.modules.admin.models  # noqa: F401
import app.modules.auth.models  # noqa: F401
import app.modules.chat.models  # noqa: F401
import app.modules.documents.models  # noqa: F401
import app.modules.spaces.models  # noqa: F401
import app.modules.study.models  # noqa: F401
import app.modules.usage.models  # noqa: F401
import app.modules.users.models  # noqa: F401
