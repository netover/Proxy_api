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

    def get_all_stats(self) -> Dict[str, Any]:
        """
        Returns all stats. Placeholder returns an empty dict.
        """
        return {}

    def record_request(self, provider_name: str, success: bool, response_time: float, **kwargs) -> None:
        """
        Record a request metric.

        Args:
            provider_name: Name of the provider
            success: Whether the request was successful
            response_time: Response time in milliseconds
            **kwargs: Additional metrics (tokens, error_type, etc.)
        """
        metric_name = f"request_{provider_name}"

        if success:
            self.increment(f"{metric_name}_success", 1)
        else:
            self.increment(f"{metric_name}_failure", 1)

        self.histogram(f"{metric_name}_response_time", response_time)

        # Record additional metrics if provided
        if "tokens" in kwargs:
            self.gauge(f"{metric_name}_tokens", kwargs["tokens"])

        if "error_type" in kwargs:
            self.increment(f"{metric_name}_error_{kwargs['error_type']}", 1)

    def get_prometheus_metrics(self) -> str:
        """
        Returns metrics in Prometheus format. Placeholder returns an empty string.
        """
        return ""

# Create a single global instance for the application to use
metrics_collector = MetricsCollector()
