"""
Metrics placeholder cho Prometheus.
Full implementation in phase 5 (performance).
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """
    Placeholder metrics collector.
    prometheus_client integration comes in phase 5.
    """

    def increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        pass

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        pass

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        pass


metrics = MetricsCollector()
