"""
Circuit breaker cho LLM Gateway.
Ngăn gọi liên tục khi AI provider gặp sự cố.
"""
from __future__ import annotations

import time
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Hoạt động bình thường
    OPEN = "open"          # Đang ngăn tất cả requests
    HALF_OPEN = "half_open"  # Đang thử phục hồi


class CircuitBreaker:
    """
    Circuit breaker pattern cho AI calls.

    - CLOSED: Hoạt động bình thường, đếm lỗi liên tiếp
    - OPEN: Đủ lỗi -> ngăn tất cả calls, chờ recovery_timeout
    - HALF_OPEN: Sau recovery_timeout, cho qua một request thử nghiệm
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
        """Trạng thái hiện tại, tự chuyển OPEN -> HALF_OPEN sau timeout."""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker transitioning OPEN -> HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        """Ghi nhận request thành công."""
        if self._state != CircuitState.CLOSED:
            logger.info(
                "Circuit breaker transitioning %s -> CLOSED after success",
                self._state.value,
            )
        self._state = CircuitState.CLOSED
        self._failure_count = 0

    def record_failure(self) -> None:
        """Ghi nhận request thất bại."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                logger.warning(
                    "Circuit breaker OPEN after %d consecutive failures",
                    self._failure_count,
                )
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset circuit breaker về trạng thái ban đầu."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
