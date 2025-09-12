"""
Advanced Retry Strategies for LLM Proxy API
Provides differentiated retry strategies based on error types and adaptive behavior
"""

import asyncio
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, Union, Callable, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from src.core.exceptions import (
    ProviderError, RateLimitError, APIConnectionError,
    AuthenticationError, ServiceUnavailableError
)
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class ErrorType(Enum):
    """Error types for retry strategy selection"""
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"
    AUTHENTICATION = "authentication"
    CLIENT_ERROR = "client_error"
    UNKNOWN = "unknown"


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    error_type: ErrorType
    error: Exception
    delay: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class RetryHistory:
    """Tracks retry attempts and success/failure patterns"""
    attempts: deque = field(default_factory=lambda: deque(maxlen=100))
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None

    def record_success(self):
        """Record a successful attempt"""
        self.success_count += 1
        self.consecutive_failures = 0
        self.last_success_time = time.time()

    def record_failure(self, error_type: ErrorType, error: Exception, delay: float):
        """Record a failed attempt"""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        attempt = RetryAttempt(
            attempt_number=len(self.attempts) + 1,
            error_type=error_type,
            error=error,
            delay=delay
        )
        self.attempts.append(attempt)

    def get_success_rate(self, window_size: int = 20) -> float:
        """Calculate success rate over recent attempts"""
        recent_attempts = list(self.attempts)[-window_size:]
        if not recent_attempts:
            return 1.0

        total = len(recent_attempts) + 1  # +1 for current success if any
        successes = sum(1 for _ in range(self.success_count) if _ >= len(recent_attempts) - window_size)
        return successes / total if total > 0 else 1.0

    def get_average_delay(self, error_type: Optional[ErrorType] = None) -> float:
        """Get average delay for specific error type or all errors"""
        delays = []
        for attempt in self.attempts:
            if error_type is None or attempt.error_type == error_type:
                delays.append(attempt.delay)

        return sum(delays) / len(delays) if delays else 0.0


@dataclass
class ProviderRetryConfig:
    """Detailed configuration for a specific provider"""
    max_attempts: Optional[int] = None
    base_delay: Optional[float] = None
    max_delay: Optional[float] = None
    backoff_factor: Optional[float] = None
    jitter: Optional[bool] = None
    jitter_factor: Optional[float] = None

    # Error-type specific configurations
    error_configs: Dict[ErrorType, Dict[str, Any]] = field(default_factory=dict)

    # Strategy-specific overrides
    strategy_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_error_config(self, error_type: ErrorType) -> Dict[str, Any]:
        """Get configuration for specific error type"""
        return self.error_configs.get(error_type, {})

    def get_strategy_override(self, strategy_name: str) -> Dict[str, Any]:
        """Get strategy-specific overrides"""
        return self.strategy_overrides.get(strategy_name, {})


@dataclass
class RetryConfig:
    """Configuration for retry strategies with enhanced provider support"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1

    # Provider-specific configurations
    provider_configs: Dict[str, ProviderRetryConfig] = field(default_factory=dict)

    def get_provider_config(self, provider_name: str) -> ProviderRetryConfig:
        """Get detailed configuration for specific provider"""
        return self.provider_configs.get(provider_name, ProviderRetryConfig())

    def get_effective_config(self, provider_name: str, error_type: Optional[ErrorType] = None,
                           strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """Get effective configuration combining global and provider-specific settings"""
        provider_config = self.get_provider_config(provider_name)

        # Start with global defaults
        effective = {
            'max_attempts': self.max_attempts,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
            'backoff_factor': self.backoff_factor,
            'jitter': self.jitter,
            'jitter_factor': self.jitter_factor
        }

        # Apply provider-level overrides
        if provider_config.max_attempts is not None:
            effective['max_attempts'] = provider_config.max_attempts
        if provider_config.base_delay is not None:
            effective['base_delay'] = provider_config.base_delay
        if provider_config.max_delay is not None:
            effective['max_delay'] = provider_config.max_delay
        if provider_config.backoff_factor is not None:
            effective['backoff_factor'] = provider_config.backoff_factor
        if provider_config.jitter is not None:
            effective['jitter'] = provider_config.jitter
        if provider_config.jitter_factor is not None:
            effective['jitter_factor'] = provider_config.jitter_factor

        # Apply error-type specific overrides
        if error_type:
            error_config = provider_config.get_error_config(error_type)
            effective.update(error_config)

        # Apply strategy-specific overrides
        if strategy_name:
            strategy_override = provider_config.get_strategy_override(strategy_name)
            effective.update(strategy_override)

        return effective


class RetryStrategy(ABC):
    """Base class for retry strategies with enhanced provider configuration"""

    def __init__(self, config: RetryConfig, provider_name: str = ""):
        self.config = config
        self.provider_name = provider_name
        self.history = RetryHistory()
        self._effective_config_cache = {}

    def get_effective_config(self, error_type: Optional[ErrorType] = None) -> Dict[str, Any]:
        """Get effective configuration for current provider and error type"""
        cache_key = (self.provider_name, error_type, self.__class__.__name__)

        if cache_key not in self._effective_config_cache:
            strategy_name = self.__class__.__name__.replace('Strategy', '').lower()
            self._effective_config_cache[cache_key] = self.config.get_effective_config(
                self.provider_name, error_type, strategy_name
            )

        return self._effective_config_cache[cache_key]

    @abstractmethod
    async def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if request should be retried"""
        pass

    @abstractmethod
    async def get_delay(self, error: Exception, attempt: int) -> float:
        """Calculate delay before next retry attempt"""
        pass

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error type for strategy selection"""
        if isinstance(error, RateLimitError):
            return ErrorType.RATE_LIMIT
        elif isinstance(error, asyncio.TimeoutError) or "timeout" in str(error).lower():
            return ErrorType.TIMEOUT
        elif isinstance(error, (ConnectionError, OSError)) or "connection" in str(error).lower():
            return ErrorType.CONNECTION
        elif isinstance(error, AuthenticationError):
            return ErrorType.AUTHENTICATION
        elif hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
            if 400 <= status_code < 500:
                return ErrorType.CLIENT_ERROR
            elif 500 <= status_code < 600:
                return ErrorType.SERVER_ERROR
        elif isinstance(error, ServiceUnavailableError):
            return ErrorType.SERVER_ERROR

        return ErrorType.UNKNOWN

    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        effective_config = self.get_effective_config()  # Get general config for max_attempts
        max_attempts = effective_config['max_attempts']

        for attempt in range(max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                self.history.record_success()
                return result

            except Exception as e:
                error_type = self.classify_error(e)
                last_exception = e

                # Don't retry on certain errors
                if not await self.should_retry(e, attempt):
                    logger.debug(
                        f"Not retrying {self.provider_name}",
                        extra={
                            'attempt': attempt,
                            'error_type': error_type.value,
                            'error': str(e)
                        }
                    )
                    break

                # Record failure
                delay = await self.get_delay(e, attempt)
                self.history.record_failure(error_type, e, delay)

                logger.warning(
                    f"Request failed, retrying {self.provider_name}",
                    extra={
                        'attempt': attempt,
                        'max_attempts': max_attempts,
                        'error_type': error_type.value,
                        'delay': round(delay, 2),
                        'error': str(e)
                    }
                )

                if attempt < max_attempts:
                    await asyncio.sleep(delay)

        # All retries exhausted
        raise last_exception


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff strategy optimized for rate limiting"""

    async def should_retry(self, error: Exception, attempt: int) -> bool:
        """Retry on rate limit and certain connection errors with provider-specific config"""
        error_type = self.classify_error(error)
        effective_config = self.get_effective_config(error_type)
        max_attempts = effective_config['max_attempts']

        # Always retry rate limits (up to configured max attempts)
        if error_type == ErrorType.RATE_LIMIT:
            return attempt < max_attempts

        # Retry connection errors but with potentially lower max attempts
        if error_type in [ErrorType.CONNECTION, ErrorType.TIMEOUT]:
            # Use provider-specific max attempts for these errors, defaulting to lower value
            connection_max = effective_config.get('connection_max_attempts', min(2, max_attempts))
            return attempt < connection_max

        # Don't retry client errors or auth errors
        if error_type in [ErrorType.AUTHENTICATION, ErrorType.CLIENT_ERROR]:
            return False

        # Retry server errors with adaptive behavior
        if error_type == ErrorType.SERVER_ERROR:
            # If we have many consecutive failures, reduce retry attempts
            if self.history.consecutive_failures > 3:
                return attempt < min(1, max_attempts)
            return attempt < max_attempts

        return False

    async def get_delay(self, error: Exception, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter and advanced features"""
        error_type = self.classify_error(error)
        effective_config = self.get_effective_config(error_type)

        # For rate limits, use longer base delay and check retry_after header
        if error_type == ErrorType.RATE_LIMIT:
            if hasattr(error, 'retry_after') and error.retry_after:
                base_delay = float(error.retry_after)
            elif hasattr(error, 'response') and hasattr(error.response, 'headers'):
                # Check common retry-after headers
                retry_after = error.response.headers.get('Retry-After') or error.response.headers.get('retry-after')
                if retry_after:
                    try:
                        base_delay = float(retry_after)
                    except ValueError:
                        base_delay = max(effective_config['base_delay'] * 2, 5.0)
                else:
                    base_delay = max(effective_config['base_delay'] * 2, 5.0)  # Start at 5 seconds for rate limits
            else:
                base_delay = max(effective_config['base_delay'] * 2, 5.0)
        else:
            base_delay = effective_config['base_delay']

        # Exponential backoff with capped exponent to prevent overflow
        exponent = min(attempt, 10)  # Cap exponent to prevent extremely long delays
        delay = base_delay * (effective_config['backoff_factor'] ** exponent)

        # Adaptive delay based on success rate
        success_rate = self.history.get_success_rate()
        if success_rate < 0.3:
            # Very low success rate, significantly increase delay
            delay *= 2.0
        elif success_rate < 0.5:
            # Lower success rate, increase delay
            delay *= 1.5
        elif success_rate > 0.8:
            # High success rate, can reduce delay slightly
            delay *= 0.8

        # Consider consecutive failures for rate limits
        if error_type == ErrorType.RATE_LIMIT and self.history.consecutive_failures > 2:
            delay *= 1.3

        # Add jitter to prevent thundering herd
        if effective_config['jitter']:
            jitter_range = delay * effective_config['jitter_factor']
            delay += random.uniform(-jitter_range, jitter_range)

        # Ensure minimum delay for rate limits
        if error_type == ErrorType.RATE_LIMIT:
            delay = max(delay, 1.0)

        # Cap at max delay
        return min(delay, effective_config['max_delay'])


class ImmediateRetryStrategy(RetryStrategy):
    """Immediate retry strategy for transient errors with smart detection"""

    def __init__(self, config: RetryConfig, provider_name: str = ""):
        super().__init__(config, provider_name)
        self.immediate_retry_count = 0
        self.max_immediate_retries = 2  # Allow up to 2 immediate retries
        self.transient_errors = {
            'connection reset', 'connection refused', 'connection aborted',
            'timeout', 'network is unreachable', 'temporary failure',
            'service temporarily unavailable', 'gateway timeout'
        }

    def _is_transient_error(self, error: Exception) -> bool:
        """Check if error is likely transient and suitable for immediate retry"""
        error_str = str(error).lower()
        return any(transient in error_str for transient in self.transient_errors)

    async def should_retry(self, error: Exception, attempt: int) -> bool:
        """Retry immediately on transient errors with smart detection"""
        error_type = self.classify_error(error)

        # Immediate retry for timeouts and connection errors
        if error_type in [ErrorType.TIMEOUT, ErrorType.CONNECTION]:
            if self.immediate_retry_count < self.max_immediate_retries:
                # Additional check for transient nature
                if self._is_transient_error(error):
                    self.immediate_retry_count += 1
                    return True

        # For server errors, check if they seem transient
        if error_type == ErrorType.SERVER_ERROR:
            if self._is_transient_error(error) and self.immediate_retry_count < self.max_immediate_retries:
                self.immediate_retry_count += 1
                return True
            # Otherwise use exponential backoff
            return attempt < self.config.max_attempts

        # Don't retry on client errors or auth errors
        if error_type in [ErrorType.AUTHENTICATION, ErrorType.CLIENT_ERROR]:
            return False

        # For unknown errors, check if they seem transient
        if error_type == ErrorType.UNKNOWN and self._is_transient_error(error):
            if self.immediate_retry_count < self.max_immediate_retries:
                self.immediate_retry_count += 1
                return True

        return False

    async def get_delay(self, error: Exception, attempt: int) -> float:
        """Minimal delay for immediate retries, exponential for others"""
        error_type = self.classify_error(error)
        effective_config = self.get_effective_config(error_type)

        # Use immediate retry delay if within limit and error is transient
        if (self.immediate_retry_count <= self.max_immediate_retries and
            (error_type in [ErrorType.TIMEOUT, ErrorType.CONNECTION] or
             (error_type in [ErrorType.SERVER_ERROR, ErrorType.UNKNOWN] and self._is_transient_error(error)))):
            # Progressive delay for immediate retries (0.05, 0.1, 0.2)
            immediate_delays = [0.05, 0.1, 0.2]
            delay_index = min(self.immediate_retry_count - 1, len(immediate_delays) - 1)
            return immediate_delays[delay_index]
        else:
            # Reset immediate retry count for non-immediate retries
            self.immediate_retry_count = 0

            # Exponential backoff for other errors
            delay = effective_config['base_delay'] * (effective_config['backoff_factor'] ** attempt)

            # Adaptive delay based on success rate
            success_rate = self.history.get_success_rate()
            if success_rate < 0.5:
                delay *= 1.2

            # Add jitter
            if effective_config['jitter']:
                jitter_range = delay * effective_config['jitter_factor']
                delay += random.uniform(-jitter_range, jitter_range)

            return min(delay, effective_config['max_delay'])


class AdaptiveRetryStrategy(RetryStrategy):
    """Adaptive retry strategy that learns from success/failure patterns with advanced metrics"""

    def __init__(self, config: RetryConfig, provider_name: str = ""):
        super().__init__(config, provider_name)
        self.adaptation_window = 15  # Increased window for better pattern recognition
        self.confidence_threshold = 0.7
        self.error_type_weights = {
            ErrorType.RATE_LIMIT: 1.2,
            ErrorType.CONNECTION: 0.8,
            ErrorType.TIMEOUT: 0.9,
            ErrorType.SERVER_ERROR: 1.0,
            ErrorType.UNKNOWN: 0.7
        }

    def _calculate_weighted_success_rate(self, error_type: ErrorType) -> float:
        """Calculate success rate weighted by error type frequency"""
        if not self.history.attempts:
            return 1.0

        # Count recent attempts by error type
        error_counts = {}
        success_count = 0
        total_count = 0

        for attempt in list(self.history.attempts)[-self.adaptation_window:]:
            total_count += 1
            if attempt.error_type == error_type:
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            else:
                success_count += 1  # Assume other attempts were successful

        if total_count == 0:
            return 1.0

        # Weight the success rate by error type frequency
        weight = self.error_type_weights.get(error_type, 1.0)
        error_frequency = error_counts.get(error_type, 0) / total_count
        base_success_rate = success_count / total_count

        return base_success_rate * (1 + weight * error_frequency)

    def _get_error_pattern_confidence(self, error_type: ErrorType) -> float:
        """Calculate confidence in error pattern based on historical data"""
        if len(self.history.attempts) < 5:
            return 0.5  # Low confidence with limited data

        recent_attempts = list(self.history.attempts)[-10:]
        error_count = sum(1 for attempt in recent_attempts if attempt.error_type == error_type)

        # Higher confidence if we have consistent patterns
        if error_count >= 3:
            return min(0.9, 0.5 + (error_count / 10))
        else:
            return 0.5

    async def should_retry(self, error: Exception, attempt: int) -> bool:
        """Adaptive retry decision based on historical patterns and confidence"""
        error_type = self.classify_error(error)

        # Never retry certain errors
        if error_type in [ErrorType.AUTHENTICATION, ErrorType.CLIENT_ERROR]:
            return False

        # Get weighted success rate and confidence
        weighted_success_rate = self._calculate_weighted_success_rate(error_type)
        confidence = self._get_error_pattern_confidence(error_type)

        # Adaptive thresholds based on confidence
        success_threshold = 0.4 if confidence > 0.7 else 0.6
        conservative_threshold = 0.6 if confidence > 0.7 else 0.7

        if error_type == ErrorType.RATE_LIMIT:
            # For rate limits, always retry but adapt attempt count
            max_attempts = self._adapt_max_attempts(weighted_success_rate, confidence)
            return attempt < max_attempts

        if error_type in [ErrorType.CONNECTION, ErrorType.TIMEOUT]:
            # For connection issues, retry if success rate is reasonable
            effective_config = self.get_effective_config(error_type)
            return (weighted_success_rate > success_threshold and
                    attempt < min(4, effective_config['max_attempts']))

        if error_type == ErrorType.SERVER_ERROR:
            # For server errors, be more conservative
            effective_config = self.get_effective_config(error_type)
            return (weighted_success_rate > conservative_threshold and
                    attempt < min(3, effective_config['max_attempts']))

        if error_type == ErrorType.UNKNOWN:
            # For unknown errors, use conservative approach
            effective_config = self.get_effective_config(error_type)
            return (weighted_success_rate > conservative_threshold and
                    attempt < min(2, effective_config['max_attempts']))

        return False

    async def get_delay(self, error: Exception, attempt: int) -> float:
        """Adaptive delay calculation with pattern-based adjustments"""
        error_type = self.classify_error(error)
        effective_config = self.get_effective_config(error_type)
        weighted_success_rate = self._calculate_weighted_success_rate(error_type)
        confidence = self._get_error_pattern_confidence(error_type)

        # Base delay calculation with error-type specific adjustments
        if error_type == ErrorType.RATE_LIMIT:
            base_delay = max(effective_config['base_delay'] * 2, 3.0)
        elif error_type in [ErrorType.CONNECTION, ErrorType.TIMEOUT]:
            base_delay = effective_config['base_delay'] * 0.5  # Shorter for connection issues
        elif error_type == ErrorType.SERVER_ERROR:
            base_delay = effective_config['base_delay'] * 1.2  # Slightly longer for server errors
        else:
            base_delay = effective_config['base_delay']

        # Exponential backoff with confidence-based adjustment
        exponent = min(attempt, 8)  # Cap exponent
        delay = base_delay * (effective_config['backoff_factor'] ** exponent)

        # Adapt delay based on weighted success rate and confidence
        if weighted_success_rate < 0.3:
            # Very low success rate - significantly increase delay
            delay *= 2.5
        elif weighted_success_rate < 0.5:
            # Low success rate - increase delay
            delay *= 1.8
        elif weighted_success_rate > 0.8 and confidence > 0.7:
            # High success rate with confidence - can reduce delay
            delay *= 0.6

        # Consider consecutive failures with confidence weighting
        if self.history.consecutive_failures > 2:
            failure_multiplier = 1.2 + (confidence * 0.3)
            delay *= failure_multiplier

        # Time-based adaptation (longer delays during peak hours if pattern suggests)
        current_hour = time.localtime().tm_hour
        if 9 <= current_hour <= 17 and weighted_success_rate < 0.5:  # Business hours
            delay *= 1.1  # Slight increase during peak hours

        # Add jitter with confidence-based adjustment
        if effective_config['jitter']:
            jitter_factor = effective_config['jitter_factor']
            if confidence > 0.8:
                jitter_factor *= 0.7  # Less jitter with high confidence
            jitter_range = delay * jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return min(delay, effective_config['max_delay'])

    def _adapt_max_attempts(self, success_rate: float, confidence: float) -> int:
        """Adapt maximum attempts based on success rate and confidence"""
        effective_config = self.get_effective_config()  # Get general config
        base_attempts = effective_config['max_attempts']

        if success_rate > 0.8 and confidence > 0.7:
            return min(base_attempts + 2, 6)
        elif success_rate > 0.6 and confidence > 0.6:
            return min(base_attempts + 1, 5)
        elif success_rate < 0.3 or confidence < 0.4:
            return max(base_attempts - 1, 1)
        else:
            return base_attempts


class RetryStrategyRegistry:
    """Registry for managing retry strategies"""

    def __init__(self):
        self.strategies: Dict[str, Type[RetryStrategy]] = {
            'exponential_backoff': ExponentialBackoffStrategy,
            'immediate_retry': ImmediateRetryStrategy,
            'adaptive': AdaptiveRetryStrategy,
        }
        self.default_strategy = 'adaptive'
        self.provider_strategies: Dict[str, str] = {}

    def register_strategy(self, name: str, strategy_class: Type[RetryStrategy]):
        """Register a new retry strategy"""
        self.strategies[name] = strategy_class

    def set_provider_strategy(self, provider_name: str, strategy_name: str):
        """Set specific strategy for a provider"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        self.provider_strategies[provider_name] = strategy_name

    def get_strategy(self, provider_name: str, config: RetryConfig) -> RetryStrategy:
        """Get appropriate strategy for provider"""
        strategy_name = self.provider_strategies.get(provider_name, self.default_strategy)
        strategy_class = self.strategies.get(strategy_name)

        if not strategy_class:
            logger.warning(f"Unknown strategy {strategy_name}, using default")
            strategy_class = self.strategies[self.default_strategy]

        return strategy_class(config, provider_name)


# Global registry instance
retry_strategy_registry = RetryStrategyRegistry()


def create_retry_strategy(provider_name: str, config: RetryConfig) -> RetryStrategy:
    """Factory function for creating retry strategies"""
    return retry_strategy_registry.get_strategy(provider_name, config)