"""
Modular application initializer for ProxyAPI.

This module provides a clean, testable initialization system
that leverages existing core components to replace the monolithic main.py structure.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from .config import settings
from .logging import setup_logging
from .exceptions import InitializationError


class ApplicationInitializer:
    """Handles all application initialization tasks using existing core components."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config.yaml"
        self.logger = None
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the application with existing core components.
        
        Returns:
            Dict containing initialized components for the application.
            
        Raises:
            InitializationError: If any initialization step fails.
        """
        try:
            # Step 1: Use existing settings (already validated)
            config = settings
            
            # Step 2: Setup logging using existing logging setup
            self.logger = setup_logging(config)
            self.logger.info("🚀 Starting application initialization...")
            
            # Step 3: Setup signal handlers for graceful shutdown
            await self._setup_signal_handlers()
            
            # Step 4: Initialize core services using existing components
            services = await self._initialize_services(config)
            
            self.logger.info("✅ Application initialization completed successfully")
            
            return {
                'config': config,
                'services': services,
                'logger': self.logger
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Application initialization failed: {e}")
            else:
                print(f"Application initialization failed: {e}", file=sys.stderr)
            raise InitializationError(f"Failed to initialize application: {e}") from e
    
    async def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        def signal_handler(signum, frame):
            if self.logger:
                self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to setup signal handlers: {e}")
    
    async def _initialize_services(self, config) -> Dict[str, Any]:
        """Initialize all core services using existing infrastructure."""
        services = {}

        # Log initialization progress
        self.logger.info("📋 Initializing core services...")

        # Core services are already initialized through the core module structure
        services['config'] = config
        services['logger'] = self.logger

        # Initialize parallel execution components
        await self._initialize_parallel_execution_components()

        self.logger.info("✅ Core services initialized")

        return services

    async def _initialize_parallel_execution_components(self):
        """Initialize the parallel execution system components."""
        try:
            self.logger.info("🔄 Initializing parallel execution system...")

            # Import parallel execution components
            from .provider_discovery import provider_discovery
            from .circuit_breaker_pool import circuit_breaker_pool
            from .load_balancer import load_balancer
            from .parallel_fallback import parallel_fallback_engine

            # Start provider discovery monitoring
            await provider_discovery.start_monitoring()
            self.logger.info("✅ Provider Discovery Service started")

            # Start circuit breaker adaptation
            await circuit_breaker_pool.start_adaptation_loop()
            self.logger.info("✅ Circuit Breaker Pool adaptation started")

            # Start load balancer monitoring
            await load_balancer.start_load_monitoring()
            self.logger.info("✅ Load Balancer monitoring started")

            self.logger.info("🚀 Parallel execution system initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize parallel execution system: {e}")
            # Don't fail the entire initialization, but log the error
            # The system can still operate with sequential fallback
    
    async def shutdown(self):
        """Perform graceful shutdown of all services."""
        if self.logger:
            self.logger.info("🛑 Starting graceful shutdown...")

        # Shutdown parallel execution components
        await self._shutdown_parallel_execution_components()

    async def _shutdown_parallel_execution_components(self):
        """Shutdown the parallel execution system components."""
        try:
            self.logger.info("🔄 Shutting down parallel execution system...")

            # Import and shutdown components
            from .provider_discovery import provider_discovery
            from .circuit_breaker_pool import circuit_breaker_pool
            from .load_balancer import load_balancer
            from .parallel_fallback import parallel_fallback_engine

            # Shutdown in reverse order
            await parallel_fallback_engine.shutdown()
            await load_balancer.shutdown()
            await circuit_breaker_pool.shutdown()
            await provider_discovery.stop_monitoring()

            self.logger.info("✅ Parallel execution system shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during parallel execution shutdown: {e}")


# Convenience function for direct usage
async def initialize_app(config_path: str = None) -> Dict[str, Any]:
    """Initialize the application with a single call."""
    initializer = ApplicationInitializer(config_path)
    return await initializer.initialize()