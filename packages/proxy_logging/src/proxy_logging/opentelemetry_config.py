"""OpenTelemetry configuration for distributed tracing and metrics."""

import os
from typing import Dict, Any, Optional
import logging

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBasedSampler

    # Handle different import paths for ResourceAttributes
    try:
        # Newer versions of OpenTelemetry
        from opentelemetry.semconv.resource import ResourceAttributes
    except ImportError:
        try:
            # Older versions or alternative path
            from opentelemetry.semconv.trace import ResourceAttributes
        except ImportError:
            # Fallback: define basic resource attributes
            class ResourceAttributes:
                SERVICE_NAME = "service.name"
                SERVICE_VERSION = "service.version"

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class OpenTelemetryConfig:
    """Configuration for OpenTelemetry tracing and metrics."""

    def __init__(
        self,
        service_name: str = "proxy-api",
        service_version: str = "1.0.0",
        prometheus_exporter=None,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self._initialized = False
        self.prometheus_exporter = prometheus_exporter

    def _get_sampling_rate(self) -> float:
        """Get sampling rate based on environment."""
        env = os.getenv("ENVIRONMENT", "development").lower()

        sampling_rates = {
            "development": 1.0,  # 100%
            "staging": 0.5,  # 50%
            "production": 0.1,  # 10%
        }

        rate = sampling_rates.get(env, 1.0)  # Default to 100% if unknown env
        logging.getLogger(__name__).info(
            f"OpenTelemetry sampling rate for {env} environment: {rate * 100}%"
        )
        return rate

    def configure(self) -> bool:
        """Configure OpenTelemetry if available."""
        if not OTEL_AVAILABLE:
            logging.getLogger(__name__).warning(
                "OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
            )
            return False

        if self._initialized:
            return True

        try:
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: self.service_name,
                    ResourceAttributes.SERVICE_VERSION: self.service_version,
                }
            )

            # Configure sampling based on environment
            sampling_rate = self._get_sampling_rate()
            sampler = TraceIdRatioBasedSampler(sampling_rate)

            provider = TracerProvider(resource=resource, sampler=sampler)
            trace.set_tracer_provider(provider)

            # Configure OTLP exporter if endpoint is provided
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            if otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                span_processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(span_processor)

            self._initialized = True

            # Report sampling rate to Prometheus if exporter is available
            if self.prometheus_exporter:
                sampling_rate = self._get_sampling_rate()
                self.prometheus_exporter.set_telemetry_sampling_rate(sampling_rate)

            return True

        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to configure OpenTelemetry: {e}")
            return False

    def get_tracer(self, name: str) -> Optional[Any]:
        """Get a tracer instance."""
        if not self._initialized or not OTEL_AVAILABLE:
            return None
        return trace.get_tracer(name)

    def get_telemetry_config(self) -> Dict[str, Any]:
        """Get current telemetry configuration for monitoring."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        sampling_rate = self._get_sampling_rate()

        return {
            "environment": env,
            "sampling_rate": sampling_rate,
            "sampling_percentage": sampling_rate * 100,
            "otel_available": OTEL_AVAILABLE,
            "initialized": self._initialized,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        }
