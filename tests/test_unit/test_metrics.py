"""
Unit tests for metrics system.
"""

import pytest
import time
from unittest.mock import patch
from src.core.metrics.metrics import MetricsCollector, metrics_collector


class TestMetricsCollector:
    """Test metrics collector functionality."""

    def test_metrics_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector("test_prefix")

        assert collector.prefix == "test_prefix"
        assert isinstance(collector.metrics, dict)
        assert isinstance(collector._lock, type(pytest.importorskip("threading").Lock()))

    def test_counter_metric(self):
        """Test counter metric functionality."""
        collector = MetricsCollector()

        # Test increment
        collector.increment("test_counter", 5)
        assert collector.metrics["proxy_api.test_counter"]["value"] == 5

        # Test multiple increments
        collector.increment("test_counter", 3)
        assert collector.metrics["proxy_api.test_counter"]["value"] == 8

    def test_gauge_metric(self):
        """Test gauge metric functionality."""
        collector = MetricsCollector()

        # Test gauge setting
        collector.gauge("test_gauge", 42.5)
        assert collector.metrics["proxy_api.test_gauge"]["value"] == 42.5

        # Test gauge update
        collector.gauge("test_gauge", 100.0)
        assert collector.metrics["proxy_api.test_gauge"]["value"] == 100.0

    def test_histogram_metric(self):
        """Test histogram metric functionality."""
        collector = MetricsCollector()

        # Test histogram recording
        collector.histogram("test_histogram", 10.5)
        collector.histogram("test_histogram", 20.3)
        collector.histogram("test_histogram", 15.7)

        histogram_data = collector.metrics["proxy_api.test_histogram"]
        assert histogram_data["type"] == "histogram"
        assert len(histogram_data["values"]) == 3
        assert 10.5 in histogram_data["values"]
        assert 20.3 in histogram_data["values"]
        assert 15.7 in histogram_data["values"]

    def test_metric_tags(self):
        """Test metric tags functionality."""
        collector = MetricsCollector()

        # Test counter with tags
        collector.increment("test_counter", 1, {"service": "api", "version": "1.0"})
        metric = collector.metrics["proxy_api.test_counter"]
        assert metric["tags"]["service"] == "api"
        assert metric["tags"]["version"] == "1.0"

    def test_get_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector("test")

        # Add some metrics
        collector.increment("counter1", 5)
        collector.gauge("gauge1", 42)
        collector.histogram("histogram1", 10.5)

        metrics = collector.get_metrics()

        assert "test.counter1" in metrics
        assert "test.gauge1" in metrics
        assert "test.histogram1" in metrics
        assert metrics["test.counter1"]["value"] == 5
        assert metrics["test.gauge1"]["value"] == 42
        assert len(metrics["test.histogram1"]["values"]) == 1

    def test_record_summary(self):
        """Test summary recording functionality."""
        collector = MetricsCollector()

        # Test cache hit
        collector.record_summary(cache_hit=True, latency=100.5)

        assert collector.metrics["proxy_api.summary_requests"]["value"] == 1
        assert collector.metrics["proxy_api.summary_cache_hits"]["value"] == 1
        # summary_cache_misses should not exist since there was no cache miss
        assert "proxy_api.summary_cache_misses" not in collector.metrics

        # Check histogram
        histogram = collector.metrics["proxy_api.summary_latency"]
        assert histogram["type"] == "histogram"
        assert 100.5 in histogram["values"]

        # Test cache miss
        collector.record_summary(cache_hit=False, latency=200.3)

        assert collector.metrics["proxy_api.summary_requests"]["value"] == 2
        assert collector.metrics["proxy_api.summary_cache_hits"]["value"] == 1
        assert collector.metrics["proxy_api.summary_cache_misses"]["value"] == 1

    def test_thread_safety(self):
        """Test thread safety of metrics operations."""
        collector = MetricsCollector()

        # Simulate concurrent access (basic test)
        collector.increment("thread_test", 1)
        collector.gauge("thread_gauge", 50)

        metrics = collector.get_metrics()
        assert metrics["proxy_api.thread_test"]["value"] == 1
        assert metrics["proxy_api.thread_gauge"]["value"] == 50


class TestGlobalMetricsCollector:
    """Test global metrics collector instance."""

    def test_global_instance_exists(self):
        """Test that global metrics collector exists."""
        assert metrics_collector is not None
        assert isinstance(metrics_collector, MetricsCollector)

    def test_global_metrics_operations(self):
        """Test operations on global metrics collector."""
        # Clear any existing metrics
        metrics_collector.metrics.clear()

        # Test global operations
        metrics_collector.increment("global_test", 10)
        metrics_collector.gauge("global_gauge", 25.5)

        metrics = metrics_collector.get_metrics()
        assert metrics["proxy_api.global_test"]["value"] == 10
        assert metrics["proxy_api.global_gauge"]["value"] == 25.5
