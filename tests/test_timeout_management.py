"""
Comprehensive tests for timeout management across external service calls
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import httpx
import aiohttp
from src.core.http_client import OptimizedHTTPClient
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig as UnifiedProviderConfig, ProviderType
from src.providers.openai import OpenAIProvider
from src.core.exceptions import ProviderError


class TestHTTPClientTimeoutManagement:
    """Test timeout management in HTTP client"""

    @pytest.fixture
    def timeout_http_client(self):
        """Create HTTP client with specific timeout settings"""
        return OptimizedHTTPClient(
            timeout=2.0,  # Short timeout for testing
            connect_timeout=1.0,
            retry_attempts=1,
            retry_backoff_factor=0.1
        )

    @pytest.mark.asyncio
    async def test_http_client_connect_timeout(self, timeout_http_client):
        """Test connection timeout handling"""
        with patch.object(timeout_http_client._client, 'request', side_effect=httpx.ConnectTimeout("Connect timeout")):
            start_time = time.time()
            with pytest.raises(httpx.ConnectTimeout):
                await timeout_http_client.request("GET", "https://api.test.com/data")
            end_time = time.time()

            # Should fail quickly due to short connect timeout
            assert end_time - start_time < 1.5

    @pytest.mark.asyncio
    async def test_http_client_read_timeout(self, timeout_http_client):
        """Test read timeout handling"""
        with patch.object(timeout_http_client._client, 'request', side_effect=httpx.ReadTimeout("Read timeout")):
            start_time = time.time()
            with pytest.raises(httpx.ReadTimeout):
                await timeout_http_client.request("GET", "https://api.test.com/data")
            end_time = time.time()

            # Should fail within timeout period
            assert end_time - start_time < 3.0

    @pytest.mark.asyncio
    async def test_http_client_write_timeout(self, timeout_http_client):
        """Test write timeout handling"""
        with patch.object(timeout_http_client._client, 'request', side_effect=httpx.WriteTimeout("Write timeout")):
            start_time = time.time()
            with pytest.raises(httpx.WriteTimeout):
                await timeout_http_client.request("GET", "https://api.test.com/data")
            end_time = time.time()

            # Should fail within timeout period
            assert end_time - start_time < 3.0

    @pytest.mark.asyncio
    async def test_http_client_pool_timeout(self, timeout_http_client):
        """Test pool timeout handling"""
        with patch.object(timeout_http_client._client, 'request', side_effect=httpx.PoolTimeout("Pool timeout")):
            start_time = time.time()
            with pytest.raises(httpx.PoolTimeout):
                await timeout_http_client.request("GET", "https://api.test.com/data")
            end_time = time.time()

            # Should fail quickly
            assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_http_client_timeout_with_retry(self, timeout_http_client):
        """Test timeout with retry logic"""
        call_count = 0

        async def timeout_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(3)  # Longer than timeout
                raise httpx.TimeoutException("Timeout")
            else:
                response = MagicMock()
                response.status_code = 200
                return response

        with patch.object(timeout_http_client._client, 'request', side_effect=timeout_then_success):
            with patch('asyncio.sleep'):  # Speed up retry delay
                start_time = time.time()
                response = await timeout_http_client.request("GET", "https://api.test.com/data")
                end_time = time.time()

                assert response.status_code == 200
                assert call_count == 2  # Initial + 1 retry
                # Should take longer due to retry
                assert end_time - start_time >= 2.0

    @pytest.mark.asyncio
    async def test_http_client_timeout_exhaustion(self, timeout_http_client):
        """Test timeout retry exhaustion"""
        with patch.object(timeout_http_client._client, 'request', side_effect=httpx.TimeoutException("Persistent timeout")):
            with patch('asyncio.sleep'):  # Speed up retries
                start_time = time.time()
                with pytest.raises(httpx.TimeoutException):
                    await timeout_http_client.request("GET", "https://api.test.com/data")
                end_time = time.time()

                # Should take time for retries
                assert end_time - start_time >= 2.0  # Initial + retry

    @pytest.mark.asyncio
    async def test_http_client_different_timeout_configs(self):
        """Test HTTP client with different timeout configurations"""
        configs = [
            {"timeout": 1.0, "connect_timeout": 0.5},
            {"timeout": 5.0, "connect_timeout": 2.0},
            {"timeout": 10.0, "connect_timeout": 5.0}
        ]

        for config in configs:
            client = OptimizedHTTPClient(**config)

            with patch.object(client._client, 'request', side_effect=httpx.TimeoutException("Timeout")):
                start_time = time.time()
                with pytest.raises(httpx.TimeoutException):
                    await client.request("GET", "https://api.test.com/data")
                end_time = time.time()

                # Should respect the configured timeout
                assert end_time - start_time < config["timeout"] + 1.0


class TestModelDiscoveryTimeoutManagement:
    """Test timeout management in model discovery"""

    @pytest.fixture
    def timeout_discovery_config(self):
        """Create discovery config with short timeout"""
        return ProviderConfig(
            name="timeout_test_provider",
            base_url="https://api.test-provider.com",
            api_key="test-key",
            timeout=1,  # Very short timeout
            max_retries=1
        )

    @pytest.fixture
    def discovery_service(self):
        """Create model discovery service"""
        return ModelDiscoveryService()

    @pytest.mark.asyncio
    async def test_model_discovery_connect_timeout(self, discovery_service, timeout_discovery_config):
        """Test connection timeout in model discovery"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.side_effect = asyncio.TimeoutError("Connect timeout")

            start_time = time.time()
            with pytest.raises(ProviderError) as exc_info:
                await discovery_service.discover_models(timeout_discovery_config)
            end_time = time.time()

            assert "Timeout connecting" in str(exc_info.value)
            # Should fail quickly due to short timeout
            assert end_time - start_time < 2.0

    @pytest.mark.asyncio
    async def test_model_discovery_read_timeout(self, discovery_service, timeout_discovery_config):
        """Test read timeout in model discovery"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            async def slow_response(*args, **kwargs):
                await asyncio.sleep(2)  # Longer than timeout
                raise asyncio.TimeoutError("Read timeout")

            mock_session.get.side_effect = slow_response

            start_time = time.time()
            with pytest.raises(ProviderError) as exc_info:
                await discovery_service.discover_models(timeout_discovery_config)
            end_time = time.time()

            assert "Timeout connecting" in str(exc_info.value)
            assert end_time - start_time >= 1.0  # At least the timeout duration

    @pytest.mark.asyncio
    async def test_model_discovery_timeout_with_retry(self, discovery_service, timeout_discovery_config):
        """Test timeout with retry in model discovery"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            call_count = 0
            async def timeout_then_success(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    await asyncio.sleep(2)  # Trigger timeout
                    raise asyncio.TimeoutError("Timeout")
                else:
                    response = AsyncMock()
                    response.status = 200
                    response.json.return_value = {
                        "data": [{"id": "gpt-4", "object": "model", "created": 1234567890, "owned_by": "openai"}]
                    }
                    return response

            mock_session.get.side_effect = timeout_then_success

            with patch('asyncio.sleep'):  # Speed up retry delay
                start_time = time.time()
                models = await discovery_service.discover_models(timeout_discovery_config)
                end_time = time.time()

                assert len(models) == 1
                assert models[0].id == "gpt-4"
                assert call_count == 2  # Initial + retry
                # Should take longer due to retry
                assert end_time - start_time >= 2.0

    @pytest.mark.asyncio
    async def test_model_discovery_timeout_exhaustion(self, discovery_service, timeout_discovery_config):
        """Test timeout retry exhaustion in model discovery"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.side_effect = asyncio.TimeoutError("Persistent timeout")

            with patch('asyncio.sleep'):  # Speed up retries
                start_time = time.time()
                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(timeout_discovery_config)
                end_time = time.time()

                assert "Timeout connecting" in str(exc_info.value)
                # Should take time for retries
                assert end_time - start_time >= 1.0

    @pytest.mark.asyncio
    async def test_model_discovery_different_timeout_configs(self, discovery_service):
        """Test model discovery with different timeout configurations"""
        timeout_configs = [1, 3, 5]  # Different timeout values

        for timeout_val in timeout_configs:
            config = ProviderConfig(
                name=f"timeout_{timeout_val}_provider",
                base_url="https://api.test-provider.com",
                api_key="test-key",
                timeout=timeout_val,
                max_retries=0  # No retries for cleaner timing
            )

            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                async def delayed_timeout(*args, **kwargs):
                    await asyncio.sleep(timeout_val + 0.5)  # Slightly longer than timeout
                    raise asyncio.TimeoutError("Timeout")

                mock_session.get.side_effect = delayed_timeout

                start_time = time.time()
                with pytest.raises(ProviderError):
                    await discovery_service.discover_models(config)
                end_time = time.time()

                # Should respect the configured timeout
                assert end_time - start_time >= timeout_val
                assert end_time - start_time < timeout_val + 2.0


class TestProviderTimeoutManagement:
    """Test timeout management in providers"""

    @pytest.fixture
    def timeout_provider_config(self):
        """Create provider config with short timeout"""
        return UnifiedProviderConfig(
            name="timeout_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=2  # Short timeout
        )

    @pytest.mark.asyncio
    async def test_provider_health_check_timeout(self, timeout_provider_config):
        """Test timeout in provider health check"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(timeout_provider_config)

            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Health check timeout")):
                start_time = time.time()
                health_result = await provider.health_check()
                end_time = time.time()

                assert health_result["healthy"] is False
                assert "Health check timeout" in health_result["error"]
                assert provider.status.name == "UNHEALTHY"
                # Should fail within reasonable time
                assert end_time - start_time < 3.0

    @pytest.mark.asyncio
    async def test_provider_completion_timeout(self, timeout_provider_config):
        """Test timeout in provider completion request"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(timeout_provider_config)

            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Completion timeout")):
                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                with pytest.raises(Exception):  # Should raise timeout error
                    await provider.create_completion(request)
                end_time = time.time()

                # Should fail within timeout period
                assert end_time - start_time < 3.0

    @pytest.mark.asyncio
    async def test_provider_timeout_with_retry(self, timeout_provider_config):
        """Test timeout with retry in provider"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(timeout_provider_config)

            call_count = 0
            async def timeout_then_success(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    await asyncio.sleep(3)  # Trigger timeout
                    raise asyncio.TimeoutError("Timeout")
                else:
                    response = MagicMock()
                    response.status_code = 200
                    response.json.return_value = {"choices": [{"message": {"content": "Success"}}]}
                    return response

            with patch.object(provider, 'make_request', side_effect=timeout_then_success):
                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                result = await provider.create_completion(request)
                end_time = time.time()

                assert result["choices"][0]["message"]["content"] == "Success"
                assert call_count == 2  # Initial + retry
                # Should take longer due to retry
                assert end_time - start_time >= 2.0

    @pytest.mark.asyncio
    async def test_provider_different_timeout_configs(self):
        """Test provider with different timeout configurations"""
        timeout_configs = [1, 3, 5]

        for timeout_val in timeout_configs:
            config = UnifiedProviderConfig(
                name=f"timeout_{timeout_val}_provider",
                type=ProviderType.OPENAI,
                base_url="https://api.test-provider.com",
                api_key_env="TEST_API_KEY",
                models=["gpt-4"],
                enabled=True,
                priority=1,
                timeout=timeout_val
            )

            with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
                provider = OpenAIProvider(config)

                with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Timeout")):
                    request = {
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Hello"}]
                    }

                    start_time = time.time()
                    with pytest.raises(Exception):
                        await provider.create_completion(request)
                    end_time = time.time()

                    # Should respect the configured timeout
                    assert end_time - start_time >= timeout_val
                    assert end_time - start_time < timeout_val + 2.0


class TestTimeoutCascadingEffects:
    """Test timeout effects cascading through multiple layers"""

    @pytest.fixture
    def cascading_config(self):
        """Create config for cascading timeout tests"""
        return UnifiedProviderConfig(
            name="cascading_timeout_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=3  # Moderate timeout
        )

    @pytest.mark.asyncio
    async def test_timeout_cascading_health_to_discovery(self, cascading_config):
        """Test timeout cascading from health check to model discovery"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(cascading_config)
            discovery_service = ModelDiscoveryService()

            # Health check times out
            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Health timeout")):
                health_result = await provider.health_check()
                assert health_result["healthy"] is False
                assert provider.status.name == "UNHEALTHY"

            # Model discovery should also be affected by provider being unhealthy
            discovery_config = ProviderConfig(
                name="cascading_timeout_provider",
                base_url="https://api.test-provider.com",
                api_key="test-key",
                timeout=3,
                max_retries=0
            )

            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.get.side_effect = asyncio.TimeoutError("Discovery timeout")

                start_time = time.time()
                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(discovery_config)
                end_time = time.time()

                assert "Timeout connecting" in str(exc_info.value)
                assert end_time - start_time >= 3.0

    @pytest.mark.asyncio
    async def test_timeout_cascading_with_http_client(self, cascading_config):
        """Test timeout cascading with HTTP client layers"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(cascading_config)

            # Mock HTTP client timeout
            with patch('src.core.provider_factory.get_advanced_http_client') as mock_get_client:
                mock_http_client = AsyncMock()
                mock_http_client.request.side_effect = asyncio.TimeoutError("HTTP client timeout")
                mock_get_client.return_value = mock_http_client

                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                with pytest.raises(Exception):
                    await provider.create_completion(request)
                end_time = time.time()

                # Should respect provider timeout
                assert end_time - start_time >= 3.0
                assert end_time - start_time < 5.0

    @pytest.mark.asyncio
    async def test_timeout_cascading_multiple_retries(self, cascading_config):
        """Test timeout cascading with multiple retry layers"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(cascading_config)

            call_count = 0
            async def cascading_timeout(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                await asyncio.sleep(1)  # Contribute to timeout
                if call_count <= 2:  # First two calls timeout
                    raise asyncio.TimeoutError(f"Timeout {call_count}")
                else:
                    response = MagicMock()
                    response.status_code = 200
                    response.json.return_value = {"choices": [{"message": {"content": "Success"}}]}
                    return response

            with patch.object(provider, 'make_request', side_effect=cascading_timeout):
                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                result = await provider.create_completion(request)
                end_time = time.time()

                assert result["choices"][0]["message"]["content"] == "Success"
                assert call_count == 3  # Initial + 2 retries
                # Should take significant time due to retries
                assert end_time - start_time >= 6.0  # 3 calls * 2 seconds each


class TestTimeoutConfigurationValidation:
    """Test timeout configuration validation and edge cases"""

    @pytest.mark.asyncio
    async def test_zero_timeout_handling(self):
        """Test handling of zero timeout values"""
        config = UnifiedProviderConfig(
            name="zero_timeout_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=0  # Zero timeout
        )

        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(config)

            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Zero timeout")):
                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                with pytest.raises(Exception):
                    await provider.create_completion(request)
                end_time = time.time()

                # Should fail very quickly with zero timeout
                assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_negative_timeout_handling(self):
        """Test handling of negative timeout values"""
        config = UnifiedProviderConfig(
            name="negative_timeout_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=-1  # Negative timeout
        )

        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(config)

            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Negative timeout")):
                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                with pytest.raises(Exception):
                    await provider.create_completion(request)
                end_time = time.time()

                # Should fail quickly
                assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_very_large_timeout_handling(self):
        """Test handling of very large timeout values"""
        config = UnifiedProviderConfig(
            name="large_timeout_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=300  # 5 minutes
        )

        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(config)

            with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError("Large timeout")):
                request = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                start_time = time.time()
                with pytest.raises(Exception):
                    await provider.create_completion(request)
                end_time = time.time()

                # Should wait for the full timeout period
                assert end_time - start_time >= 300
                assert end_time - start_time < 310  # Allow some margin

    @pytest.mark.asyncio
    async def test_timeout_with_different_request_types(self):
        """Test timeout behavior with different request types"""
        config = UnifiedProviderConfig(
            name="multi_request_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test-provider.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=2
        )

        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = OpenAIProvider(config)

            request_types = [
                {"type": "completion", "data": {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}},
                {"type": "text_completion", "data": {"model": "gpt-4", "prompt": "Complete this"}},
                {"type": "embeddings", "data": {"model": "text-embedding-ada-002", "input": "Test input"}}
            ]

            for request_type in request_types:
                with patch.object(provider, 'make_request', side_effect=asyncio.TimeoutError(f"Timeout for {request_type['type']}")):
                    start_time = time.time()

                    if request_type["type"] == "completion":
                        with pytest.raises(Exception):
                            await provider.create_completion(request_type["data"])
                    elif request_type["type"] == "text_completion":
                        with pytest.raises(Exception):
                            await provider.create_text_completion(request_type["data"])
                    elif request_type["type"] == "embeddings":
                        with pytest.raises(Exception):
                            await provider.create_embeddings(request_type["data"])

                    end_time = time.time()

                    # All should respect the timeout
                    assert end_time - start_time >= 2.0
                    assert end_time - start_time < 4.0


if __name__ == "__main__":
    pytest.main([__file__])