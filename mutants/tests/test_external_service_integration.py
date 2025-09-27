"""
Integration tests for external service error scenarios
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

import httpx
import aiohttp
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig
from src.core.provider_factory import BaseProvider, ProviderStatus
from src.core.unified_config import ProviderConfig as UnifiedProviderConfig, ProviderType
from src.core.exceptions import ProviderError, APIConnectionError, AuthenticationError, RateLimitError
from src.providers.openai import OpenAIProvider
from src.core.http_client import OptimizedHTTPClient


class TestExternalServiceErrorIntegration:
    """Integration tests for external service error scenarios"""

    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration"""
        return UnifiedProviderConfig(
            name="integration_test_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def discovery_config(self):
        """Create discovery provider configuration"""
        return ProviderConfig(
            name="integration_test_provider",
            base_url="https://api.test-provider.com",
            api_key="test-api-key",
            timeout=30,
            max_retries=2
        )

    @pytest.mark.asyncio
    async def test_complete_service_outage_scenario(self, provider_config, discovery_config):
        """Test complete service outage affecting multiple components"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Mock complete service outage
            with patch.object(provider, 'make_request', side_effect=httpx.ConnectError("Service completely down")):
                # Health check should fail
                health_result = await provider.health_check()
                assert health_result["status"] == "unhealthy"
                assert health_result["healthy"] is False
                assert "Service completely down" in health_result["error"]
                assert provider.status == ProviderStatus.UNHEALTHY

                # Model discovery should fail
                with patch('aiohttp.ClientSession') as mock_session_class:
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session
                    mock_session.get.side_effect = aiohttp.ClientError("Connection failed")

                    with pytest.raises(ProviderError) as exc_info:
                        await discovery_service.discover_models(discovery_config)

                    assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authentication_failure_cascade(self, provider_config, discovery_config):
        """Test authentication failure affecting multiple operations"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'invalid-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Mock authentication failures
            auth_error = httpx.HTTPStatusError(
                "401 Unauthorized",
                response=MagicMock(status_code=401),
                request=MagicMock()
            )

            with patch.object(provider, 'make_request', side_effect=auth_error):
                # Health check should detect auth failure
                health_result = await provider.health_check()
                assert health_result["status"] == "unhealthy"
                assert health_result["healthy"] is False
                assert provider.status == ProviderStatus.UNHEALTHY

                # Model discovery should fail with auth error
                with patch('aiohttp.ClientSession') as mock_session_class:
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session

                    mock_response = AsyncMock()
                    mock_response.status = 401
                    mock_session.get.return_value.__aenter__.return_value = mock_response

                    with pytest.raises(ProviderError) as exc_info:
                        await discovery_service.discover_models(discovery_config)

                    assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_and_recovery_scenario(self, provider_config, discovery_config):
        """Test rate limiting and recovery across components"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Mock rate limit then recovery
            call_count = 0
            async def rate_limit_then_success(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    # First two calls get rate limited
                    response = MagicMock()
                    response.status_code = 429
                    response.headers = {"Retry-After": "1"}
                    raise httpx.HTTPStatusError(
                        "429 Too Many Requests",
                        response=response,
                        request=MagicMock()
                    )
                else:
                    # Third call succeeds
                    response = MagicMock()
                    response.status_code = 200
                    response.json.return_value = {
                        "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                    }
                    return response

            with patch.object(provider, 'make_request', side_effect=rate_limit_then_success):
                # Health check with rate limit
                health_result = await provider.health_check()
                # Should eventually succeed after retries
                assert health_result["healthy"] is True
                assert provider.status == ProviderStatus.HEALTHY

            # Model discovery with rate limit and retry
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Rate limited responses then success
                responses = []
                for i in range(3):
                    response = AsyncMock()
                    if i < 2:
                        response.status = 429
                    else:
                        response.status = 200
                        response.json.return_value = {
                            "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                        }
                    responses.append(response)

                mock_session.get.side_effect = responses

                with patch('asyncio.sleep'):  # Speed up retries
                    models = await discovery_service.discover_models(discovery_config)

                    assert len(models) == 1
                    assert models[0].id == "gpt-4"

    @pytest.mark.asyncio
    async def test_network_instability_scenario(self, provider_config, discovery_config):
        """Test network instability affecting service reliability"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Mock intermittent network failures
            call_count = 0
            async def intermittent_failure(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Every 3rd call succeeds
                    response = MagicMock()
                    response.status_code = 200
                    response.json.return_value = {
                        "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                    }
                    return response
                else:
                    raise httpx.ConnectError("Intermittent network failure")

            with patch.object(provider, 'make_request', side_effect=intermittent_failure):
                # Health check should eventually succeed
                health_result = await provider.health_check()
                assert health_result["healthy"] is True
                assert provider.status == ProviderStatus.HEALTHY

            # Model discovery with intermittent failures
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                call_count = 0
                async def intermittent_http_failure(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count % 4 == 0:  # Every 4th call succeeds
                        response = AsyncMock()
                        response.status = 200
                        response.json.return_value = {
                            "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                        }
                        return response
                    else:
                        raise aiohttp.ClientError("Network instability")

                mock_session.get.side_effect = intermittent_http_failure

                with patch('asyncio.sleep'):  # Speed up retries
                    models = await discovery_service.discover_models(discovery_config)

                    assert len(models) == 1
                    assert models[0].id == "gpt-4"

    @pytest.mark.asyncio
    async def test_service_degradation_and_recovery(self, provider_config, discovery_config):
        """Test service degradation and eventual recovery"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Phase 1: Service degradation (slow responses)
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(2)  # Slow response
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {
                    "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                }
                return response

            with patch.object(provider, 'make_request', side_effect=slow_response):
                health_result = await provider.health_check()
                assert health_result["healthy"] is True  # Still healthy but slow
                assert health_result["response_time"] >= 2.0
                assert provider.status == ProviderStatus.HEALTHY

            # Phase 2: Service failure
            with patch.object(provider, 'make_request', side_effect=httpx.ConnectError("Service failed")):
                health_result = await provider.health_check()
                assert health_result["healthy"] is False
                assert provider.status == ProviderStatus.UNHEALTHY

                # Model discovery should fail
                with patch('aiohttp.ClientSession') as mock_session_class:
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session
                    mock_session.get.side_effect = aiohttp.ClientError("Service down")

                    with pytest.raises(ProviderError):
                        await discovery_service.discover_models(discovery_config)

            # Phase 3: Service recovery
            with patch.object(provider, 'make_request', return_value=MagicMock(status_code=200)):
                health_result = await provider.health_check()
                assert health_result["healthy"] is True
                assert provider.status == ProviderStatus.HEALTHY

                # Model discovery should work again
                with patch('aiohttp.ClientSession') as mock_session_class:
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session

                    mock_response = AsyncMock()
                    mock_response.status = 200
                    mock_response.json.return_value = {
                        "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                    }
                    mock_session.get.return_value.__aenter__.return_value = mock_response

                    models = await discovery_service.discover_models(discovery_config)
                    assert len(models) == 1

    @pytest.mark.asyncio
    async def test_cascading_failure_protection(self, provider_config, discovery_config):
        """Test protection against cascading failures"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Simulate cascading failure: multiple rapid failures
            failure_count = 0
            async def cascading_failure(*args, **kwargs):
                nonlocal failure_count
                failure_count += 1
                raise httpx.ConnectError(f"Cascading failure #{failure_count}")

            with patch.object(provider, 'make_request', side_effect=cascading_failure):
                # Multiple health check failures
                for i in range(5):
                    health_result = await provider.health_check()
                    assert health_result["healthy"] is False
                    assert provider.status == ProviderStatus.UNHEALTHY
                    assert health_result["error_count"] == i + 1

                # Provider should be marked as unhealthy
                assert provider.status == ProviderStatus.UNHEALTHY

            # Model discovery should fail fast due to unhealthy provider
            with pytest.raises(ProviderError):
                await discovery_service.discover_models(discovery_config)

    @pytest.mark.asyncio
    async def test_timeout_cascading_effects(self, provider_config, discovery_config):
        """Test timeout effects across different operations"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Mock timeouts
            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Request timeout")):
                # Health check timeout
                health_result = await provider.health_check()
                assert health_result["healthy"] is False
                assert "Request timeout" in health_result["error"]
                assert provider.status == ProviderStatus.UNHEALTHY

            # Model discovery timeout
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.get.side_effect = asyncio.TimeoutError("Discovery timeout")

                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(discovery_config)

                assert "Timeout connecting" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_mixed_error_types_integration(self, provider_config, discovery_config):
        """Test integration with mixed error types"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Test different HTTP error codes
            error_scenarios = [
                (400, "Bad Request", "Invalid request"),
                (401, "Unauthorized", "Authentication failed"),
                (403, "Forbidden", "Access forbidden"),
                (429, "Too Many Requests", "Rate limit exceeded"),
                (500, "Internal Server Error", "Server error"),
                (502, "Bad Gateway", "Gateway error"),
                (503, "Service Unavailable", "Service unavailable"),
                (504, "Gateway Timeout", "Gateway timeout")
            ]

            for status_code, status_text, expected_error in error_scenarios:
                with patch('aiohttp.ClientSession') as mock_session_class:
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session

                    mock_response = AsyncMock()
                    mock_response.status = status_code
                    mock_session.get.return_value.__aenter__.return_value = mock_response

                    with pytest.raises(ProviderError) as exc_info:
                        await discovery_service.discover_models(discovery_config)

                    assert expected_error in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, provider_config, discovery_config):
        """Test concurrent operations under error conditions"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Mock concurrent failures
            async def concurrent_failure(*args, **kwargs):
                await asyncio.sleep(0.01)  # Small delay to simulate processing
                raise httpx.ConnectError("Concurrent failure")

            with patch.object(provider, 'make_request', side_effect=concurrent_failure):
                # Run multiple health checks concurrently
                tasks = [provider.health_check() for _ in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All should fail
                for result in results:
                    assert isinstance(result, dict)
                    assert result["healthy"] is False
                    assert "Concurrent failure" in result["error"]

                # Provider should be unhealthy
                assert provider.status == ProviderStatus.UNHEALTHY

            # Concurrent model discovery attempts
            async def concurrent_discovery_failure(*args, **kwargs):
                await asyncio.sleep(0.01)
                raise aiohttp.ClientError("Concurrent discovery failure")

            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.get.side_effect = concurrent_discovery_failure

                # Run multiple discovery attempts concurrently
                tasks = [discovery_service.discover_models(discovery_config) for _ in range(3)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All should fail
                for result in results:
                    assert isinstance(result, ProviderError)
                    assert "Failed to connect" in str(result)

    @pytest.mark.asyncio
    async def test_error_recovery_patterns(self, provider_config, discovery_config):
        """Test various error recovery patterns"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(provider_config)
            discovery_service = ModelDiscoveryService()

            # Pattern 1: Fail, fail, succeed
            call_count = 0
            async def fail_fail_succeed(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise httpx.ConnectError(f"Failure {call_count}")
                else:
                    response = MagicMock()
                    response.status_code = 200
                    response.json.return_value = {
                        "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                    }
                    return response

            with patch.object(provider, 'make_request', side_effect=fail_fail_succeed):
                # Should eventually succeed
                health_result = await provider.health_check()
                assert health_result["healthy"] is True
                assert provider.status == ProviderStatus.HEALTHY

            # Pattern 2: Success after cache miss
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                call_count = 0
                async def cache_miss_then_success(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    response = AsyncMock()
                    response.status = 200
                    response.json.return_value = {
                        "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                    }
                    return response

                mock_session.get.side_effect = cache_miss_then_success

                # First call (cache miss)
                models1 = await discovery_service.discover_models(discovery_config)
                assert len(models1) == 1

                # Second call (cache hit)
                models2 = await discovery_service.discover_models(discovery_config)
                assert models2 == models1  # Same result from cache


class TestHTTPClientExternalServiceIntegration:
    """Test HTTP client integration with external services"""

    @pytest.fixture
    def http_client(self):
        """Create HTTP client for testing"""
        return OptimizedHTTPClient(
            timeout=5.0,
            retry_attempts=2,
            retry_backoff_factor=0.1
        )

    @pytest.mark.asyncio
    async def test_http_client_external_service_integration(self, http_client):
        """Test HTTP client with simulated external service"""
        # Mock successful external API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": "test"}

        with patch.object(http_client._client, 'request', return_value=mock_response) as mock_request:
            response = await http_client.request("GET", "https://api.external-service.com/data")

            assert response.status_code == 200
            assert response.json() == {"status": "success", "data": "test"}

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_client_external_service_failure(self, http_client):
        """Test HTTP client with external service failure"""
        with patch.object(http_client._client, 'request', side_effect=httpx.ConnectError("External service down")):
            with pytest.raises(httpx.ConnectError):
                await http_client.request("GET", "https://api.external-service.com/data")

    @pytest.mark.asyncio
    async def test_http_client_external_service_timeout(self, http_client):
        """Test HTTP client with external service timeout"""
        with patch.object(http_client._client, 'request', side_effect=httpx.TimeoutException("External service timeout")):
            with pytest.raises(httpx.TimeoutException):
                await http_client.request("GET", "https://api.external-service.com/data")


if __name__ == "__main__":
    pytest.main([__file__])