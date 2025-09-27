"""
Comprehensive tests for provider health check functionality
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import httpx
from src.core.provider_factory import BaseProvider, ProviderStatus, ProviderInfo
from src.core.unified_config import ProviderConfig, ProviderType
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider
from src.core.exceptions import APIConnectionError, AuthenticationError


class TestBaseProviderHealthCheck:
    """Test base provider health check functionality"""

    @pytest.fixture
    def provider_config(self):
        """Create a test provider configuration"""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def mock_provider(self, provider_config):
        """Create a mock provider for testing"""
        class MockProvider(BaseProvider):
            def __init__(self, config):
                super().__init__(config)
                self.api_key = "test-key"

            async def _perform_health_check(self):
                return {"healthy": True, "details": {"status_code": 200}}

            async def create_completion(self, request):
                pass

            async def create_text_completion(self, request):
                pass

            async def create_embeddings(self, request):
                pass

        return MockProvider(provider_config)

    @pytest.mark.asyncio
    async def test_successful_health_check(self, mock_provider):
        """Test successful health check"""
        result = await mock_provider.health_check()

        assert result["status"] == "healthy"
        assert result["healthy"] is True
        assert "response_time" in result
        assert result["error_count"] == 0
        assert result["last_error"] is None
        assert mock_provider.status == ProviderStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_health_check_caching(self, mock_provider):
        """Test health check result caching"""
        # First check
        result1 = await mock_provider.health_check()
        first_check_time = mock_provider._last_health_check

        # Second check (should be cached)
        result2 = await mock_provider.health_check()

        assert result2["cached"] is True
        assert result2["last_check"] == first_check_time
        assert result1["response_time"] == result2["response_time"]

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_provider):
        """Test health check failure handling"""
        # Mock failed health check
        async def failed_check():
            return {"healthy": False, "error": "Service unavailable"}

        mock_provider._perform_health_check = failed_check

        result = await mock_provider.health_check()

        assert result["status"] == "degraded"
        assert result["healthy"] is False
        assert result["error"] == "Service unavailable"
        assert result["error_count"] == 1
        assert mock_provider.status == ProviderStatus.DEGRADED
        assert mock_provider._last_error == "Service unavailable"

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_provider):
        """Test health check exception handling"""
        # Mock exception in health check
        async def failing_check():
            raise Exception("Network timeout")

        mock_provider._perform_health_check = failing_check

        result = await mock_provider.health_check()

        assert result["status"] == "unhealthy"
        assert result["healthy"] is False
        assert result["error"] == "Network timeout"
        assert result["error_count"] == 1
        assert mock_provider.status == ProviderStatus.UNHEALTHY
        assert mock_provider._last_error == "Network timeout"

    @pytest.mark.asyncio
    async def test_error_count_increment_decrement(self, mock_provider):
        """Test error count increment and decrement"""
        # Start with healthy state
        await mock_provider.health_check()
        assert mock_provider._error_count == 0

        # Failed check
        async def failed_check():
            return {"healthy": False, "error": "Failed"}

        mock_provider._perform_health_check = failed_check
        await mock_provider.health_check()
        assert mock_provider._error_count == 1

        # Another failure
        await mock_provider.health_check()
        assert mock_provider._error_count == 2

        # Successful check should decrement
        async def success_check():
            return {"healthy": True, "details": {"status_code": 200}}

        mock_provider._perform_health_check = success_check
        await mock_provider.health_check()
        assert mock_provider._error_count == 1  # Decremented by 1

    @pytest.mark.asyncio
    async def test_provider_info(self, mock_provider):
        """Test provider info generation"""
        info = mock_provider.info

        assert isinstance(info, ProviderInfo)
        assert info.name == "test_provider"
        assert info.type == ProviderType.OPENAI
        assert info.status == ProviderStatus.HEALTHY
        assert info.models == ["gpt-4"]
        assert info.priority == 1
        assert info.enabled is True
        assert info.forced is False
        assert info.error_count == 0
        assert info.last_error is None

    @pytest.mark.asyncio
    async def test_health_check_metrics_recording(self, mock_provider):
        """Test that health checks record metrics"""
        with patch('src.core.provider_factory.metrics_collector') as mock_collector:
            await mock_provider.health_check()

            mock_collector.record_request.assert_called_once()
            call_args = mock_collector.record_request.call_args
            assert call_args[1]["success"] is True
            assert "response_time" in call_args[1]

    @pytest.mark.asyncio
    async def test_health_check_exception_metrics(self, mock_provider):
        """Test metrics recording on health check exception"""
        async def failing_check():
            raise Exception("Test exception")

        mock_provider._perform_health_check = failing_check

        with patch('src.core.provider_factory.metrics_collector') as mock_collector:
            await mock_provider.health_check()

            mock_collector.record_request.assert_called_once()
            call_args = mock_collector.record_request.call_args
            assert call_args[1]["success"] is False
            assert call_args[1]["error_type"] == "Exception"


class TestOpenAIProviderHealthCheck:
    """Test OpenAI provider health check implementation"""

    @pytest.fixture
    def openai_config(self):
        """Create OpenAI provider configuration"""
        return ProviderConfig(
            name="openai_test",
            type=ProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def openai_provider(self, openai_config):
        """Create OpenAI provider instance"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            return OpenAIProvider(openai_config)

    @pytest.mark.asyncio
    async def test_openai_healthy_response(self, openai_provider):
        """Test OpenAI health check with healthy response"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(openai_provider, 'make_request', return_value=mock_response) as mock_request:
            result = await openai_provider._perform_health_check()

            assert result["healthy"] is True
            assert result["details"]["status_code"] == 200

            # Verify correct endpoint called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][1] == "https://api.openai.com/v1/models"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_openai_unhealthy_response(self, openai_provider):
        """Test OpenAI health check with unhealthy response"""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(openai_provider, 'make_request', return_value=mock_response):
            result = await openai_provider._perform_health_check()

            assert result["healthy"] is False
            assert result["details"]["status_code"] == 500

    @pytest.mark.asyncio
    async def test_openai_health_check_exception(self, openai_provider):
        """Test OpenAI health check with exception"""
        with patch.object(openai_provider, 'make_request', side_effect=httpx.ConnectError("Connection failed")):
            result = await openai_provider._perform_health_check()

            assert result["healthy"] is False
            assert result["error"] == "Connection failed"

    @pytest.mark.asyncio
    async def test_openai_health_check_full_flow(self, openai_provider):
        """Test complete OpenAI health check flow"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(openai_provider, 'make_request', return_value=mock_response):
            # Perform health check
            health_result = await openai_provider.health_check()

            assert health_result["status"] == "healthy"
            assert health_result["healthy"] is True
            assert "response_time" in health_result
            assert openai_provider.status == ProviderStatus.HEALTHY


class TestAnthropicProviderHealthCheck:
    """Test Anthropic provider health check implementation"""

    @pytest.fixture
    def anthropic_config(self):
        """Create Anthropic provider configuration"""
        return ProviderConfig(
            name="anthropic_test",
            type=ProviderType.ANTHROPIC,
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_API_KEY",
            models=["claude-3-sonnet-20240229"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def anthropic_provider(self, anthropic_config):
        """Create Anthropic provider instance"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            return AnthropicProvider(anthropic_config)

    @pytest.mark.asyncio
    async def test_anthropic_healthy_response(self, anthropic_provider):
        """Test Anthropic health check with healthy response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        with patch.object(anthropic_provider, 'make_request', return_value=mock_response) as mock_request:
            result = await anthropic_provider._perform_health_check()

            assert result["healthy"] is True
            assert result["details"]["status_code"] == 200

            # Verify correct endpoint called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert "api.anthropic.com" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_anthropic_unhealthy_response(self, anthropic_provider):
        """Test Anthropic health check with unhealthy response"""
        mock_response = MagicMock()
        mock_response.status_code = 503  # Service unavailable

        with patch.object(anthropic_provider, 'make_request', return_value=mock_response):
            result = await anthropic_provider._perform_health_check()

            assert result["healthy"] is False
            assert result["details"]["status_code"] == 503


class TestProviderHealthCheckErrorScenarios:
    """Test various error scenarios in health checks"""

    @pytest.fixture
    def error_provider_config(self):
        """Create provider config for error testing"""
        return ProviderConfig(
            name="error_test_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def error_provider(self, error_provider_config):
        """Create provider for error testing"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            return OpenAIProvider(error_provider_config)

    @pytest.mark.asyncio
    async def test_authentication_error_health_check(self, error_provider):
        """Test authentication error in health check"""
        with patch.object(error_provider, 'make_request', side_effect=httpx.HTTPStatusError(
            "401 Unauthorized",
            response=MagicMock(status_code=401),
            request=MagicMock()
        )):
            result = await error_provider._perform_health_check()

            assert result["healthy"] is False
            assert "401" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout_error_health_check(self, error_provider):
        """Test timeout error in health check"""
        with patch.object(error_provider, 'make_request', side_effect=asyncio.TimeoutError("Request timed out")):
            result = await error_provider._perform_health_check()

            assert result["healthy"] is False
            assert result["error"] == "Request timed out"

    @pytest.mark.asyncio
    async def test_connection_error_health_check(self, error_provider):
        """Test connection error in health check"""
        with patch.object(error_provider, 'make_request', side_effect=httpx.ConnectError("Connection refused")):
            result = await error_provider._perform_health_check()

            assert result["healthy"] is False
            assert result["error"] == "Connection refused"

    @pytest.mark.asyncio
    async def test_dns_error_health_check(self, error_provider):
        """Test DNS resolution error in health check"""
        with patch.object(error_provider, 'make_request', side_effect=httpx.ConnectError("Name resolution failure")):
            result = await error_provider._perform_health_check()

            assert result["healthy"] is False
            assert "Name resolution failure" in result["error"]

    @pytest.mark.asyncio
    async def test_ssl_error_health_check(self, error_provider):
        """Test SSL certificate error in health check"""
        with patch.object(error_provider, 'make_request', side_effect=httpx.SSLError("Certificate verify failed")):
            result = await error_provider._perform_health_check()

            assert result["healthy"] is False
            assert "Certificate verify failed" in result["error"]


class TestProviderHealthCheckTiming:
    """Test timing aspects of health checks"""

    @pytest.fixture
    def timing_provider_config(self):
        """Create provider config for timing tests"""
        return ProviderConfig(
            name="timing_test_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def timing_provider(self, timing_provider_config):
        """Create provider for timing tests"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            return OpenAIProvider(timing_provider_config)

    @pytest.mark.asyncio
    async def test_health_check_response_time_measurement(self, timing_provider):
        """Test that response time is properly measured"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(timing_provider, 'make_request', return_value=mock_response):
            start_time = time.time()
            result = await timing_provider.health_check()
            end_time = time.time()

            assert "response_time" in result
            assert isinstance(result["response_time"], float)
            assert result["response_time"] >= 0
            assert result["response_time"] <= (end_time - start_time)

    @pytest.mark.asyncio
    async def test_health_check_timing_with_delay(self, timing_provider):
        """Test health check timing with artificial delay"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def delayed_request(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return mock_response

        with patch.object(timing_provider, 'make_request', side_effect=delayed_request):
            result = await timing_provider.health_check()

            assert "response_time" in result
            assert result["response_time"] >= 0.1  # At least the delay
            assert result["response_time"] < 0.2   # But not too much more

    @pytest.mark.asyncio
    async def test_health_check_last_check_timestamp(self, timing_provider):
        """Test that last health check timestamp is updated"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(timing_provider, 'make_request', return_value=mock_response):
            before_check = time.time()
            result = await timing_provider.health_check()
            after_check = time.time()

            assert timing_provider._last_health_check >= before_check
            assert timing_provider._last_health_check <= after_check
            assert result["last_check"] == timing_provider._last_health_check


class TestProviderHealthCheckStatusTransitions:
    """Test provider status transitions based on health check results"""

    @pytest.fixture
    def transition_provider_config(self):
        """Create provider config for status transition tests"""
        return ProviderConfig(
            name="transition_test_provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test.com",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=30
        )

    @pytest.fixture
    def transition_provider(self, transition_provider_config):
        """Create provider for status transition tests"""
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            return OpenAIProvider(transition_provider_config)

    @pytest.mark.asyncio
    async def test_healthy_to_degraded_transition(self, transition_provider):
        """Test transition from healthy to degraded"""
        # Start healthy
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(transition_provider, 'make_request', return_value=mock_response):
            await transition_provider.health_check()
            assert transition_provider.status == ProviderStatus.HEALTHY

        # Become degraded
        async def degraded_check():
            return {"healthy": False, "error": "Service slow"}

        transition_provider._perform_health_check = degraded_check
        await transition_provider.health_check()

        assert transition_provider.status == ProviderStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_degraded_to_unhealthy_transition(self, transition_provider):
        """Test transition from degraded to unhealthy"""
        # Start degraded
        async def degraded_check():
            return {"healthy": False, "error": "Service issues"}

        transition_provider._perform_health_check = degraded_check
        await transition_provider.health_check()
        assert transition_provider.status == ProviderStatus.DEGRADED

        # Become unhealthy due to exception
        async def failing_check():
            raise Exception("Complete failure")

        transition_provider._perform_health_check = failing_check
        await transition_provider.health_check()

        assert transition_provider.status == ProviderStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_unhealthy_to_healthy_transition(self, transition_provider):
        """Test transition from unhealthy to healthy"""
        # Start unhealthy
        async def failing_check():
            raise Exception("Service down")

        transition_provider._perform_health_check = failing_check
        await transition_provider.health_check()
        assert transition_provider.status == ProviderStatus.UNHEALTHY

        # Become healthy
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(transition_provider, 'make_request', return_value=mock_response):
            await transition_provider.health_check()
            assert transition_provider.status == ProviderStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_multiple_failures_accumulation(self, transition_provider):
        """Test error count accumulation with multiple failures"""
        # Multiple failures
        async def failing_check():
            return {"healthy": False, "error": f"Failure {transition_provider._error_count + 1}"}

        for i in range(3):
            transition_provider._perform_health_check = failing_check
            await transition_provider.health_check()
            assert transition_provider._error_count == i + 1
            assert transition_provider.status == ProviderStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_recovery_reduces_error_count(self, transition_provider):
        """Test that successful health checks reduce error count"""
        # Build up errors
        async def failing_check():
            return {"healthy": False, "error": "Persistent issue"}

        for i in range(5):
            transition_provider._perform_health_check = failing_check
            await transition_provider.health_check()

        assert transition_provider._error_count == 5
        assert transition_provider.status == ProviderStatus.DEGRADED

        # Successful recovery
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(transition_provider, 'make_request', return_value=mock_response):
            await transition_provider.health_check()

        assert transition_provider._error_count == 4  # Reduced by 1
        assert transition_provider.status == ProviderStatus.DEGRADED  # Still degraded due to remaining errors

        # Multiple successes to fully recover
        for i in range(4):
            with patch.object(transition_provider, 'make_request', return_value=mock_response):
                await transition_provider.health_check()

        assert transition_provider._error_count == 0
        assert transition_provider.status == ProviderStatus.HEALTHY


if __name__ == "__main__":
    pytest.main([__file__])