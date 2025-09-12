"""
Chaos Engineering Framework for LLM Proxy API.
Provides fault injection, network simulation, and resilience testing capabilities.
"""

import asyncio
import json
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from .logging import ContextualLogger
from .telemetry import TracedSpan, traced

logger = ContextualLogger(__name__)


class FaultType(Enum):
    """Types of faults that can be injected."""
    DELAY = "delay"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    NETWORK_FAILURE = "network_failure"
    MEMORY_PRESSURE = "memory_pressure"


class Severity(Enum):
    """Severity levels for fault injection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FaultConfig:
    """Configuration for a specific fault injection."""
    fault_type: FaultType
    severity: Severity
    probability: float  # 0.0 to 1.0
    duration_ms: int
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChaosMonkey:
    """Centralized chaos engineering controller."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.active_faults: List[FaultConfig] = []
        self.injection_history: List[Dict[str, Any]] = []
        self.logger = logger
        
    def configure(self, chaos_config: Dict[str, Any]) -> None:
        """Configure chaos engineering from settings."""
        self.enabled = chaos_config.get("enabled", False)
        if self.enabled:
            faults_config = chaos_config.get("faults", [])
            for fault_data in faults_config:
                fault = FaultConfig(
                    fault_type=FaultType(fault_data["type"]),
                    severity=Severity(fault_data["severity"]),
                    probability=fault_data["probability"],
                    duration_ms=fault_data["duration_ms"],
                    error_code=fault_data.get("error_code"),
                    error_message=fault_data.get("error_message"),
                    metadata=fault_data.get("metadata", {})
                )
                self.active_faults.append(fault)
            self.logger.info(f"Chaos engineering configured with {len(self.active_faults)} faults")
    
    def should_inject_fault(self, fault_config: FaultConfig) -> bool:
        """Determine if a fault should be injected based on probability."""
        return random.random() < fault_config.probability
    
    @traced("chaos.inject_fault", attributes={"operation": "fault_injection"})
    async def inject_fault(self, fault_config: FaultConfig, operation: str = None) -> Optional[Exception]:
        """Inject a specific fault based on configuration."""
        if not self.enabled:
            return None
            
        fault_start = time.time()
        
        try:
            with TracedSpan("chaos.fault_execution", attributes={
                "fault.type": fault_config.fault_type.value,
                "fault.severity": fault_config.severity.value,
                "fault.duration": fault_config.duration_ms,
                "operation": operation or "general"
            }) as span:
                
                self.logger.info(
                    f"Injecting {fault_config.fault_type.value} fault "
                    f"(severity: {fault_config.severity.value}, "
                    f"duration: {fault_config.duration_ms}ms)"
                )
                
                if fault_config.fault_type == FaultType.DELAY:
                    await asyncio.sleep(fault_config.duration_ms / 1000.0)
                    span.set_attribute("fault.delay_applied", True)
                    
                elif fault_config.fault_type == FaultType.ERROR:
                    error = httpx.HTTPStatusError(
                        fault_config.error_message or "Simulated error",
                        request=None,
                        response=httpx.Response(
                            status_code=fault_config.error_code or 500,
                            content=json.dumps({"error": "Chaos injection error"})
                        )
                    )
                    span.set_attribute("fault.error_thrown", True)
                    span.set_attribute("fault.error_code", fault_config.error_code or 500)
                    raise error
                    
                elif fault_config.fault_type == FaultType.TIMEOUT:
                    await asyncio.sleep(fault_config.duration_ms / 1000.0)
                    raise asyncio.TimeoutError("Simulated timeout")
                    
                elif fault_config.fault_type == FaultType.RATE_LIMIT:
                    error = httpx.HTTPStatusError(
                        "Rate limit exceeded",
                        request=None,
                        response=httpx.Response(
                            status_code=429,
                            content=json.dumps({"error": "Rate limit exceeded"})
                        )
                    )
                    span.set_attribute("fault.rate_limit_thrown", True)
                    raise error
                    
                elif fault_config.fault_type == FaultType.NETWORK_FAILURE:
                    raise ConnectionError("Network connection failed")
                    
                elif fault_config.fault_type == FaultType.MEMORY_PRESSURE:
                    # Simulate memory pressure without actually consuming memory
                    await asyncio.sleep(min(fault_config.duration_ms / 1000.0, 0.1))
                    span.set_attribute("fault.memory_pressure_simulated", True)
                
                return None
                
        except Exception as e:
            fault_duration = time.time() - fault_start
            self.injection_history.append({
                "timestamp": time.time(),
                "fault_type": fault_config.fault_type.value,
                "severity": fault_config.severity.value,
                "duration_ms": fault_duration * 1000,
                "success": True,
                "error": str(e) if isinstance(e, Exception) else None,
                "operation": operation
            })
            return e
    
    @asynccontextmanager
    async def chaos_context(self, operation: str = None):
        """Context manager for applying chaos engineering within operations."""
        if not self.enabled:
            yield
            return
            
        try:
            # Check for applicable faults
            applicable_faults = [
                fault for fault in self.active_faults
                if self.should_inject_fault(fault)
            ]
            
            if applicable_faults:
                # Inject the first applicable fault
                fault = applicable_faults[0]
                error = await self.inject_fault(fault, operation)
                if error:
                    raise error
                    
            yield
            
        except Exception as e:
            # Log chaos injection results
            self.logger.info(f"Chaos injection completed: {e}")
            raise
            
    def get_injection_stats(self) -> Dict[str, Any]:
        """Get statistics about fault injection."""
        total_injections = len(self.injection_history)
        if total_injections == 0:
            return {"total_injections": 0, "active_faults": len(self.active_faults)}
            
        fault_types = {}
        severities = {}
        
        for injection in self.injection_history:
            fault_type = injection["fault_type"]
            severity = injection["severity"]
            
            fault_types[fault_type] = fault_types.get(fault_type, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
            
        return {
            "total_injections": total_injections,
            "active_faults": len(self.active_faults),
            "fault_types": fault_types,
            "severities": severities,
            "recent_injections": self.injection_history[-10:]  # Last 10 injections
        }
    
    def reset(self) -> None:
        """Reset chaos engineering state."""
        self.active_faults.clear()
        self.injection_history.clear()
        self.logger.info("Chaos engineering reset")


# Network simulation utilities
class NetworkSimulator:
    """Simulates various network conditions."""
    
    @staticmethod
    @traced("network.simulate_delay", attributes={"operation": "network_simulation"})
    async def simulate_delay(delay_ms: int) -> None:
        """Simulate network delay."""
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)
    
    @staticmethod
    @traced("network.simulate_jitter", attributes={"operation": "network_simulation"})
    async def simulate_jitter(base_delay_ms: int, jitter_percent: float = 0.2) -> None:
        """Simulate network jitter."""
        jitter = base_delay_ms * jitter_percent
        jittered_delay = base_delay_ms + random.uniform(-jitter, jitter)
        if jittered_delay > 0:
            await asyncio.sleep(jittered_delay / 1000.0)
    
    @staticmethod
    def get_network_profiles() -> Dict[str, Dict[str, Any]]:
        """Get predefined network profiles."""
        return {
            "fast": {
                "min_delay": 10,
                "max_delay": 50,
                "jitter": 0.1,
                "packet_loss": 0.001
            },
            "medium": {
                "min_delay": 100,
                "max_delay": 300,
                "jitter": 0.2,
                "packet_loss": 0.01
            },
            "slow": {
                "min_delay": 500,
                "max_delay": 2000,
                "jitter": 0.3,
                "packet_loss": 0.05
            },
            "unreliable": {
                "min_delay": 1000,
                "max_delay": 5000,
                "jitter": 0.5,
                "packet_loss": 0.1
            }
        }


# Global chaos monkey instance
chaos_monkey = ChaosMonkey()
network_simulator = NetworkSimulator()


@traced("chaos.test_scenario", attributes={"operation": "chaos_testing"})
async def run_chaos_scenario(
    scenario_config: Dict[str, Any],
    target_function: Callable[..., Awaitable[Any]],
    *args, **kwargs
) -> Dict[str, Any]:
    """Run a specific chaos testing scenario."""
    start_time = time.time()
    
    try:
        # Configure chaos monkey for this scenario
        chaos_monkey.configure(scenario_config)
        
        # Execute target function under chaos conditions
        result = await target_function(*args, **kwargs)
        
        return {
            "success": True,
            "result": result,
            "duration_ms": (time.time() - start_time) * 1000,
            "chaos_injections": chaos_monkey.get_injection_stats()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "duration_ms": (time.time() - start_time) * 1000,
            "chaos_injections": chaos_monkey.get_injection_stats()
        }