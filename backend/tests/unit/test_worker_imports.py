"""The worker runs in its own process; its imports alone must configure every mapper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_worker_module_configures_mappers_in_a_fresh_process() -> None:
    code = (
        "import app.workers.queue\n"
        "from sqlalchemy.orm import configure_mappers\n"
        "configure_mappers()\n"
        "from app.db.base import Base\n"
        "assert {'users', 'documents', 'document_chunks'} <= set(Base.metadata.tables)\n"
    )
    result = subprocess.run(  # noqa: S603 - fixed interpreter and inline code
        [sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr[-2000:]
