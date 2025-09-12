"""OpenTelemetry configuration for distributed tracing and metrics."""

import os
from typing import Dict, Any, Optional
import logging

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    
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
    
    def __init__(self, service_name: str = "proxy-api", service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self._initialized = False
        
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
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: self.service_version,
            })
            
            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)
            
            # Configure OTLP exporter if endpoint is provided
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            if otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                span_processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(span_processor)
                
            self._initialized = True
            return True
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to configure OpenTelemetry: {e}")
            return False
    
    def get_tracer(self, name: str) -> Optional[Any]:
        """Get a tracer instance."""
        if not self._initialized or not OTEL_AVAILABLE:
            return None
        return trace.get_tracer(name)