"""
Metrics placeholder cho Prometheus.
Sẽ implement đầy đủ ở giai đoạn 5 (Hiệu năng).
"""
from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """
    Placeholder metrics collector.
    Sẽ tích hợp prometheus_client ở giai đoạn 5.
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
