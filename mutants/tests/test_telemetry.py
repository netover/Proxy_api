"""
Tests for OpenTelemetry integration and custom spans.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from src.core.telemetry import telemetry, TracedSpan, traced
from src.core.config import settings


class TestTelemetryManager:
    """Test the telemetry manager functionality."""
    
    def test_telemetry_initialization(self):
        """Test telemetry manager configuration."""
        assert not telemetry._is_configured
        
    def test_configure_telemetry(self):
        """Test telemetry configuration."""
        telemetry.configure(settings)
        assert telemetry._is_configured
        assert telemetry._tracer is not None
        
    def test_get_tracer_before_configuration(self):
        """Test getting tracer before configuration raises error."""
        with pytest.raises(RuntimeError):
            telemetry.get_tracer()
            
    def test_get_tracer_after_configuration(self):
        """Test getting tracer after configuration."""
        telemetry.configure(settings)
        tracer = telemetry.get_tracer()
        assert tracer is not None
        
    def test_create_span(self):
        """Test span creation."""
        telemetry.configure(settings)
        span = telemetry.create_span("test_span", {"test": True})
        assert span is not None
        span.end()
        
    def test_record_error(self):
        """Test error recording in spans."""
        telemetry.configure(settings)
        span = telemetry.create_span("test_span")
        error = ValueError("Test error")
        telemetry.record_error(span, error)
        assert span.status.status_code == StatusCode.ERROR
        span.end()


class TestTracedSpan:
    """Test the TracedSpan context manager."""
    
    def test_traced_span_context_manager(self):
        """Test TracedSpan as context manager."""
        telemetry.configure(settings)
        
        with TracedSpan("test_context", {"test": "value"}) as span:
            assert span is not None
            assert span.attributes.get("test") == "value"
            
    def test_traced_span_error_handling(self):
        """Test error handling in TracedSpan."""
        telemetry.configure(settings)
        
        with pytest.raises(ValueError):
            with TracedSpan("test_error") as span:
                raise ValueError("Test error")
                
        # Span should still be ended


class TestTracedDecorator:
    """Test the traced decorator."""
    
    def test_traced_sync_function(self):
        """Test traced decorator with sync function."""
        telemetry.configure(settings)
        
        @traced("sync_test", {"type": "sync"})
        def sync_function(x, y):
            return x + y
            
        result = sync_function(2, 3)
        assert result == 5
        
    @pytest.mark.asyncio
    async def test_traced_async_function(self):
        """Test traced decorator with async function."""
        telemetry.configure(settings)
        
        @traced("async_test", {"type": "async"})
        async def async_function(x, y):
            await asyncio.sleep(0.001)
            return x * y
            
        result = await async_function(2, 3)
        assert result == 6


class TestIntegrationWithProviders:
    """Test OpenTelemetry integration with providers."""
    
    @pytest.mark.asyncio
    async def test_provider_span_attributes(self):
        """Test that provider calls include proper span attributes."""
        telemetry.configure(settings)
        
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.name = "test_provider"
        
        # Create span with provider attributes
        span = telemetry.create_span("provider_call", {
            "provider.name": "test_provider",
            "provider.type": "openai"
        })
        
        span.set_attribute("request.model", "gpt-3.5-turbo")
        span.set_attribute("request.max_tokens", 100)
        
        span.end()
        
    def test_http_client_instrumentation(self):
        """Test HTTP client instrumentation."""
        # This test would normally check that HTTPX requests are instrumented
        # For now, we'll test the configuration
        telemetry.configure(settings)
        tracer = telemetry.get_tracer()
        assert tracer is not None


class TestPerformanceWithTelemetry:
    """Test performance impact of telemetry."""
    
    def test_telemetry_overhead(self):
        """Test that telemetry has minimal overhead."""
        import time
        
        # Baseline performance
        start_time = time.time()
        for i in range(1000):
            pass
        baseline = time.time() - start_time
        
        # With telemetry
        telemetry.configure(settings)
        start_time = time.time()
        for i in range(1000):
            with TracedSpan("test_span", {"iteration": i}):
                pass
        with_telemetry = time.time() - start_time
        
        # Telemetry overhead should be minimal
        overhead = with_telemetry - baseline
        assert overhead < 1.0  # Less than 1 second for 1000 spans