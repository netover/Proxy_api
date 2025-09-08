"""
Circuit breaker implementation for LLM Proxy API
Prevents cascading failures when providers become unresponsive
"""

import time
import asyncio
from enum import Enum
from typing import Dict, Any, Callable, Awaitable
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Tripped, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: tuple = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker initialized for {name}")
    
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self.state == CircuitState.CLOSED
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == CircuitState.OPEN
    
    def is_half_open(self) -> bool:
        """Check if circuit is half-open"""
        return self.state == CircuitState.HALF_OPEN
    
    async def can_execute(self) -> bool:
        """Check if request can be executed"""
        async with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if (time.time() - self.last_failure_time) >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN state")
                    return True
                return False
            
            # HALF_OPEN state
            return True
    
    async def on_success(self):
        """Handle successful request"""
        async with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker {self.name} moved to CLOSED state after success")
    
    async def on_failure(self, exception: Exception):
        """Handle failed request"""
        async with self.lock:
            self.last_failure_time = time.time()
            
            # If we're in HALF_OPEN state, any failure should trip the circuit
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.failure_count = 1  # Reset to 1 as we're starting a new failure cycle
                logger.error(f"Circuit breaker {self.name} TRIPPED from HALF_OPEN - moved to OPEN state")
            else:
                # In CLOSED state, increment failure count
                self.failure_count += 1
                logger.warning(f"Circuit breaker {self.name} failure #{self.failure_count}: {exception}")
                
                # Check if we should trip the circuit
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.error(f"Circuit breaker {self.name} TRIPPED - moved to OPEN state")

    
    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not await self.can_execute():
            raise CircuitBreakerOpenException(f"Circuit breaker {self.name} is open")
        
        try:
            result = await func(*args, **kwargs)
            await self.on_success()
            return result
        except self.expected_exception as e:
            await self.on_failure(e)
            raise

class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open"""
    pass

# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: tuple = (Exception,)
) -> CircuitBreaker:
    """Get or create circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
    return _circuit_breakers[name]

def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all circuit breakers"""
    return _circuit_breakers.copy()
