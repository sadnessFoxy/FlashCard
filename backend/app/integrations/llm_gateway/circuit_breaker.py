"""
Circuit breaker for the LLM gateway.
Stops hammering the AI provider while it is failing.
"""

from __future__ import annotations

import time
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # normal operation
    OPEN = "open"  # rejecting all calls
    HALF_OPEN = "half_open"  # probing for recovery


class CircuitBreaker:
    """
    Circuit breaker for AI calls.

    - CLOSED: normal; counts consecutive failures
    - OPEN: too many failures; reject calls until recovery_timeout
    - HALF_OPEN: after recovery_timeout, let one trial call through
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0

    @property
    def state(self) -> CircuitState:
        """Current state; moves OPEN -> HALF_OPEN once the timeout passes."""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker transitioning OPEN -> HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        """Record a success."""
        if self._state != CircuitState.CLOSED:
            logger.info(
                "Circuit breaker transitioning %s -> CLOSED after success",
                self._state.value,
            )
        self._state = CircuitState.CLOSED
        self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failure."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                logger.warning(
                    "Circuit breaker OPEN after %d consecutive failures",
                    self._failure_count,
                )
            self._state = CircuitState.OPEN

    def trip(self) -> None:
        """Open immediately (quota or billing exhausted: more calls cannot succeed)."""
        if self._state != CircuitState.OPEN:
            logger.warning("Circuit breaker OPEN: provider quota exhausted")
        self._state = CircuitState.OPEN
        self._failure_count = max(self._failure_count, self.failure_threshold)
        self._last_failure_time = time.monotonic()

    def reset(self) -> None:
        """Reset to CLOSED."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
