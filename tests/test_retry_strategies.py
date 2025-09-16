"""
Test suite for advanced retry strategies
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
import time

from src.core.retry_strategies import (
    RetryConfig,
    ProviderRetryConfig,
    ErrorType,
    ExponentialBackoffStrategy,
    ImmediateRetryStrategy,
    AdaptiveRetryStrategy,
)
from src.core.exceptions import (
    RateLimitError,
    APIConnectionError,
    ServiceUnavailableError,
)


class TestRetryStrategies:
    """Test cases for retry strategies"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            backoff_factor=2.0,
            jitter=True,
            jitter_factor=0.1,
        )

    @pytest.mark.asyncio
    async def test_exponential_backoff_rate_limit(self):
        """Test exponential backoff for rate limit errors"""
        strategy = ExponentialBackoffStrategy(self.config, "test_provider")

        # Mock rate limit error
        error = RateLimitError("Rate limit exceeded")

        # Should retry rate limit
        assert await strategy.should_retry(error, 0) == True
        assert await strategy.should_retry(error, 2) == True

        # Check delay calculation
        delay = await strategy.get_delay(error, 0)
        assert delay >= 3.0  # Minimum for rate limits (base_delay * 2)

    @pytest.mark.asyncio
    async def test_immediate_retry_transient_errors(self):
        """Test immediate retry for transient errors"""
        strategy = ImmediateRetryStrategy(self.config, "test_provider")

        # Mock connection error
        error = APIConnectionError("Connection reset")

        # Should retry immediately for transient errors
        assert await strategy.should_retry(error, 0) == True

        # Check immediate delay
        delay = await strategy.get_delay(error, 0)
        assert delay <= 0.2  # Very short delay for immediate retry

    @pytest.mark.asyncio
    async def test_adaptive_strategy_learning(self):
        """Test adaptive strategy learns from history"""
        strategy = AdaptiveRetryStrategy(self.config, "test_provider")

        # Simulate some failures
        error = ServiceUnavailableError("Service temporarily unavailable")
        for i in range(3):
            strategy.history.record_failure(ErrorType.SERVER_ERROR, error, 1.0)

        # Should be more conservative after failures
        should_retry = await strategy.should_retry(error, 1)
        assert should_retry == False  # Should not retry after many failures

    @pytest.mark.asyncio
    async def test_provider_specific_configuration(self):
        """Test per-provider configuration"""
        # Create provider-specific config
        provider_config = ProviderRetryConfig(
            max_attempts=5,
            base_delay=2.0,
            error_configs={
                ErrorType.RATE_LIMIT: {"max_attempts": 10, "base_delay": 5.0}
            },
        )

        config = RetryConfig(provider_configs={"openai": provider_config})
        strategy = ExponentialBackoffStrategy(config, "openai")

        # Test effective configuration
        effective = strategy.get_effective_config(ErrorType.RATE_LIMIT)
        assert effective["max_attempts"] == 10
        assert effective["base_delay"] == 5.0

    @pytest.mark.asyncio
    async def test_retry_execution_success(self):
        """Test successful retry execution"""
        strategy = ExponentialBackoffStrategy(self.config, "test_provider")

        # Mock successful function
        mock_func = AsyncMock(return_value="success")

        result = await strategy.execute_with_retry(mock_func, "arg1", "arg2")
        assert result == "success"
        assert strategy.history.success_count == 1

    @pytest.mark.asyncio
    async def test_retry_execution_failure(self):
        """Test retry execution with failures"""
        strategy = ExponentialBackoffStrategy(self.config, "test_provider")

        # Mock function that always fails
        mock_func = AsyncMock(
            side_effect=APIConnectionError("Connection failed")
        )

        with pytest.raises(APIConnectionError):
            await strategy.execute_with_retry(mock_func)

        assert (
            strategy.history.failure_count == 2
        )  # Connection errors only retry up to 2 times

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_errors(self):
        """Test that auth errors don't retry"""
        strategy = ExponentialBackoffStrategy(self.config, "test_provider")

        from src.core.exceptions import AuthenticationError

        error = AuthenticationError("Invalid API key")

        # Should not retry auth errors
        assert await strategy.should_retry(error, 0) == False


if __name__ == "__main__":
    pytest.main([__file__])
