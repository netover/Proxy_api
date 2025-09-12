"""Prometheus metrics exporter for monitoring and observability."""

import os
import time
from typing import Dict, Any, Optional
import logging

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class PrometheusExporter:
    """Prometheus metrics exporter for the proxy API."""
    
    def __init__(self, port: int = 8000, registry: Optional[Any] = None):
        self.port = port
        self.registry = registry or self._create_registry()
        self._initialized = False
        self._setup_metrics()
        
    def _create_registry(self) -> Any:
        """Create a new Prometheus registry."""
        if not PROMETHEUS_AVAILABLE:
            return None
        return CollectorRegistry()
        
    def _setup_metrics(self) -> None:
        """Setup Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        # Request metrics
        self.request_count = Counter(
            'proxy_api_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'proxy_api_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Provider metrics
        self.provider_requests = Counter(
            'proxy_api_provider_requests_total',
            'Total provider requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.provider_latency = Histogram(
            'proxy_api_provider_latency_seconds',
            'Provider response latency',
            ['provider', 'model'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'proxy_api_cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'proxy_api_cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Memory metrics
        self.memory_usage = Gauge(
            'proxy_api_memory_usage_bytes',
            'Current memory usage in bytes',
            registry=self.registry
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'proxy_api_circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half-open)',
            ['provider'],
            registry=self.registry
        )

        # Telemetry overhead metrics
        self.telemetry_overhead_ratio = Gauge(
            'proxy_api_telemetry_overhead_ratio',
            'Telemetry overhead as percentage of total request time',
            registry=self.registry
        )

        self.telemetry_sampling_rate = Gauge(
            'proxy_api_telemetry_sampling_rate',
            'Current telemetry sampling rate (0.0 to 1.0)',
            registry=self.registry
        )

        self.telemetry_span_count = Counter(
            'proxy_api_telemetry_spans_total',
            'Total number of telemetry spans created',
            ['sampled'],
            registry=self.registry
        )

        self.telemetry_processing_time = Histogram(
            'proxy_api_telemetry_processing_time_seconds',
            'Time spent processing telemetry data',
            registry=self.registry
        )
        
    def start_server(self) -> bool:
        """Start the Prometheus metrics server."""
        if not PROMETHEUS_AVAILABLE:
            logging.getLogger(__name__).warning(
                "Prometheus client not available. Install with: pip install prometheus-client"
            )
            return False
            
        try:
            start_http_server(self.port, registry=self.registry)
            self._initialized = True
            logging.getLogger(__name__).info(f"Prometheus metrics server started on port {self.port}")
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to start Prometheus server: {e}")
            return False
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float) -> None:
        """Record a request metric."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
            
        self.request_count.labels(
            method=method.upper(),
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.request_duration.labels(
            method=method.upper(),
            endpoint=endpoint
        ).observe(duration)
    
    def record_provider_request(self, provider: str, model: str, status: str, latency: float) -> None:
        """Record a provider request metric."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
            
        self.provider_requests.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        self.provider_latency.labels(
            provider=provider,
            model=model
        ).observe(latency)
    
    def record_cache_hit(self, cache_type: str) -> None:
        """Record a cache hit."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str) -> None:
        """Record a cache miss."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.cache_misses.labels(cache_type=cache_type).inc()
    
    def set_memory_usage(self, bytes_used: int) -> None:
        """Set current memory usage."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.memory_usage.set(bytes_used)
    
    def set_circuit_breaker_state(self, provider: str, state: int) -> None:
        """Set circuit breaker state."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.circuit_breaker_state.labels(provider=provider).set(state)

    def record_telemetry_overhead(self, overhead_ratio: float) -> None:
        """Record telemetry overhead ratio."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.telemetry_overhead_ratio.set(overhead_ratio)

    def set_telemetry_sampling_rate(self, sampling_rate: float) -> None:
        """Set current telemetry sampling rate."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.telemetry_sampling_rate.set(sampling_rate)

    def record_telemetry_span(self, sampled: bool) -> None:
        """Record a telemetry span creation."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.telemetry_span_count.labels(sampled=str(sampled).lower()).inc()

    def record_telemetry_processing_time(self, duration: float) -> None:
        """Record time spent processing telemetry."""
        if not self._initialized or not PROMETHEUS_AVAILABLE:
            return
        self.telemetry_processing_time.observe(duration)