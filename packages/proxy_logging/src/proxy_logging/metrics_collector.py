"""Metrics collection for monitoring and observability."""

from typing import Dict, Any, Optional
import threading


class MetricsCollector:
    """Metrics collection for monitoring and observability."""

    def __init__(self, prefix: str = "proxy_api"):
        self.prefix = prefix
        self.metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter metric."""
        key = f"{self.prefix}.{name}"
        with self._lock:
            if key not in self.metrics:
                self.metrics[key] = {
                    "type": "counter",
                    "value": 0.0,
                    "tags": tags or {},
                }
            self.metrics[key]["value"] += value

    def gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        key = f"{self.prefix}.{name}"
        with self._lock:
            self.metrics[key] = {
                "type": "gauge",
                "value": value,
                "tags": tags or {},
            }

    def histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        key = f"{self.prefix}.{name}"
        with self._lock:
            if key not in self.metrics:
                self.metrics[key] = {
                    "type": "histogram",
                    "values": [],
                    "tags": tags or {},
                }
            self.metrics[key]["values"].append(value)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            return self.metrics.copy()

    def record_summary(self, cache_hit: bool, latency: float) -> None:
        """Record summary metrics."""
        self.increment("summary_requests", 1)
        if cache_hit:
            self.increment("summary_cache_hits", 1)
        else:
            self.increment("summary_cache_misses", 1)
        self.histogram("summary_latency", latency)


def get_metrics_collector(prefix: str = "proxy_api") -> MetricsCollector:
    """Get a metrics collector instance."""
    return MetricsCollector(prefix)
