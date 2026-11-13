"""Document state machine (docs/DATA_MODEL.md, R6). Only these transitions are allowed."""

from __future__ import annotations

from typing import Final

UPLOADED: Final = "UPLOADED"
QUEUED: Final = "QUEUED"
PROCESSING: Final = "PROCESSING"
READY: Final = "READY"
FAILED: Final = "FAILED"
PAUSED_QUOTA: Final = "PAUSED_QUOTA"
DELETING: Final = "DELETING"

ALL_STATUSES = (UPLOADED, QUEUED, PROCESSING, READY, FAILED, PAUSED_QUOTA, DELETING)

TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    UPLOADED: frozenset({QUEUED, DELETING}),
    QUEUED: frozenset({PROCESSING, DELETING}),
    # PROCESSING -> QUEUED: a transient failure waiting for its next attempt (added in F5).
    PROCESSING: frozenset({READY, FAILED, PAUSED_QUOTA, QUEUED, DELETING}),
    READY: frozenset({DELETING}),
    FAILED: frozenset({QUEUED, DELETING}),
    PAUSED_QUOTA: frozenset({QUEUED, DELETING}),
    DELETING: frozenset(),
}

# Statuses that still count toward the per-user document limit.
COUNTED = frozenset(ALL_STATUSES) - {DELETING}
# Statuses the UI keeps polling for.
IN_PROGRESS = frozenset({UPLOADED, QUEUED, PROCESSING})


def sources_for(target: str) -> frozenset[str]:
    """Statuses from which `target` may be entered."""
    return frozenset(src for src, targets in TRANSITIONS.items() if target in targets)


def can_transition(source: str, target: str) -> bool:
    return target in TRANSITIONS.get(source, frozenset())
