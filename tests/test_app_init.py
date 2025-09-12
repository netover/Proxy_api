import pytest
import asyncio
import signal
from unittest.mock import Mock, patch, AsyncMock
from src.core.app_init import ApplicationInitializer, initialize_app


class TestApplicationInitializer:
    """Test ApplicationInitializer class"""

    def test_init_default_config_path(self):
        """Test ApplicationInitializer initialization with default config path"""
        initializer = ApplicationInitializer()
        assert initializer.config_path == "config.yaml"
        assert initializer.logger is None
        assert isinstance(initializer._shutdown_event, asyncio.Event)

    def test_init_custom_config_path(self):
        """Test ApplicationInitializer initialization with custom config path"""
        custom_path = "/custom/config.yaml"
        initializer = ApplicationInitializer(custom_path)
        assert initializer.config_path == custom_path

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful application initialization"""
        with patch('src.core.app_init.settings') as mock_settings, \
             patch('src.core.app_init.setup_logging') as mock_setup_logging, \
             patch('src.core.app_init.ApplicationInitializer._setup_signal_handlers') as mock_setup_signals, \
             patch('src.core.app_init.ApplicationInitializer._initialize_services') as mock_init_services:

            # Mock components
            mock_config = Mock()
            mock_settings.__class__ = Mock()  # Make it behave like an object
            mock_settings.__class__.__name__ = 'Settings'
            mock_logger = Mock()
            mock_services = {"test_service": "mock"}

            mock_settings.return_value = mock_config
            mock_setup_logging.return_value = mock_logger
            mock_init_services.return_value = mock_services

            initializer = ApplicationInitializer()
            result = await initializer.initialize()

            # Verify calls
            mock_setup_logging.assert_called_once_with(mock_config)
            mock_setup_signals.assert_called_once()
            mock_init_services.assert_called_once_with(mock_config)

            # Verify result
            assert result["config"] == mock_config
            assert result["services"] == mock_services
            assert result["logger"] == mock_logger
            assert initializer.logger == mock_logger

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test application initialization failure"""
        with patch('src.core.app_init.settings', side_effect=Exception("Config error")):
            initializer = ApplicationInitializer()

            with pytest.raises(Exception) as exc_info:
                await initializer.initialize()

            assert "Failed to initialize application" in str(exc_info.value)
            assert "Config error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initialize_with_logger_on_failure(self):
        """Test initialization failure when logger is already set"""
        with patch('src.core.app_init.settings') as mock_settings, \
             patch('src.core.app_init.setup_logging') as mock_setup_logging:

            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            # First part succeeds (logger setup)
            with patch('src.core.app_init.ApplicationInitializer._setup_signal_handlers') as mock_setup_signals:
                mock_setup_signals.side_effect = Exception("Signal setup failed")

                initializer = ApplicationInitializer()

                with pytest.raises(Exception) as exc_info:
                    await initializer.initialize()

                # Logger error should be called
                mock_logger.error.assert_called_once()

    def test_setup_signal_handlers_success(self):
        """Test successful signal handlers setup"""
        with patch('signal.signal') as mock_signal:
            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            asyncio.run(initializer._setup_signal_handlers())

            # Should setup SIGINT and SIGTERM
            assert mock_signal.call_count == 2
            mock_signal.assert_any_call(signal.SIGINT, initializer._signal_handler)
            mock_signal.assert_any_call(signal.SIGTERM, initializer._signal_handler)

    def test_setup_signal_handlers_failure(self):
        """Test signal handlers setup failure"""
        with patch('signal.signal', side_effect=OSError("Signal setup failed")):
            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            asyncio.run(initializer._setup_signal_handlers())

            # Should log warning but not fail
            initializer.logger.warning.assert_called_once_with("Failed to setup signal handlers: Signal setup failed")

    def test_signal_handler(self):
        """Test signal handler functionality"""
        initializer = ApplicationInitializer()
        initializer.logger = Mock()

        # Initially, shutdown event should not be set
        assert not initializer._shutdown_event.is_set()

        # Simulate signal handler call
        initializer._signal_handler(signal.SIGINT, None)

        # Shutdown event should be set
        assert initializer._shutdown_event.is_set()
        initializer.logger.info.assert_called_once_with("Received signal 2, initiating graceful shutdown...")

    @pytest.mark.asyncio
    async def test_initialize_services(self):
        """Test _initialize_services method"""
        with patch('src.core.app_init.ApplicationInitializer._initialize_parallel_execution_components') as mock_init_parallel:
            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            config = Mock()
            result = await initializer._initialize_services(config)

            expected_services = {
                'config': config,
                'logger': initializer.logger
            }

            assert result == expected_services
            mock_init_parallel.assert_called_once()
            initializer.logger.info.assert_any_call("📋 Initializing core services...")
            initializer.logger.info.assert_any_call("✅ Core services initialized")

    @pytest.mark.asyncio
    async def test_initialize_parallel_execution_components_success(self):
        """Test successful parallel execution components initialization"""
        with patch('src.core.app_init.circuit_breaker_pool') as mock_circuit_breaker, \
             patch('src.core.app_init.load_balancer') as mock_load_balancer, \
             patch('src.core.app_init.provider_discovery') as mock_provider_discovery:

            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            await initializer._initialize_parallel_execution_components()

            # Verify all components are started
            mock_provider_discovery.start_monitoring.assert_called_once()
            mock_circuit_breaker.start_adaptation_loop.assert_called_once()
            mock_load_balancer.start_load_monitoring.assert_called_once()

            # Verify logging
            initializer.logger.info.assert_any_call("🔄 Initializing parallel execution system...")
            initializer.logger.info.assert_any_call("✅ Provider Discovery Service started")
            initializer.logger.info.assert_any_call("✅ Circuit Breaker Pool adaptation started")
            initializer.logger.info.assert_any_call("✅ Load Balancer monitoring started")
            initializer.logger.info.assert_any_call("🚀 Parallel execution system initialized successfully")

    @pytest.mark.asyncio
    async def test_initialize_parallel_execution_components_failure(self):
        """Test parallel execution components initialization failure"""
        with patch('src.core.app_init.circuit_breaker_pool') as mock_circuit_breaker:
            mock_circuit_breaker.start_adaptation_loop.side_effect = Exception("Circuit breaker failed")

            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            # Should not raise exception, just log error
            await initializer._initialize_parallel_execution_components()

            initializer.logger.error.assert_called_once_with("Failed to initialize parallel execution system: Circuit breaker failed")

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful application shutdown"""
        with patch('src.core.app_init.ApplicationInitializer._shutdown_parallel_execution_components') as mock_shutdown_parallel:
            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            await initializer.shutdown()

            initializer.logger.info.assert_called_once_with("🛑 Starting graceful shutdown...")
            mock_shutdown_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_without_logger(self):
        """Test shutdown when logger is not set"""
        with patch('src.core.app_init.ApplicationInitializer._shutdown_parallel_execution_components') as mock_shutdown_parallel:
            initializer = ApplicationInitializer()
            initializer.logger = None

            # Should not fail
            await initializer.shutdown()

            mock_shutdown_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_parallel_execution_components_success(self):
        """Test successful parallel execution components shutdown"""
        with patch('src.core.app_init.circuit_breaker_pool') as mock_circuit_breaker, \
             patch('src.core.app_init.load_balancer') as mock_load_balancer, \
             patch('src.core.app_init.parallel_fallback_engine') as mock_parallel_fallback, \
             patch('src.core.app_init.provider_discovery') as mock_provider_discovery:

            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            await initializer._shutdown_parallel_execution_components()

            # Verify shutdown order
            mock_parallel_fallback.shutdown.assert_called_once()
            mock_load_balancer.shutdown.assert_called_once()
            mock_circuit_breaker.shutdown.assert_called_once()
            mock_provider_discovery.stop_monitoring.assert_called_once()

            initializer.logger.info.assert_any_call("🔄 Shutting down parallel execution system...")
            initializer.logger.info.assert_any_call("✅ Parallel execution system shutdown complete")

    @pytest.mark.asyncio
    async def test_shutdown_parallel_execution_components_failure(self):
        """Test parallel execution components shutdown failure"""
        with patch('src.core.app_init.circuit_breaker_pool') as mock_circuit_breaker:
            mock_circuit_breaker.shutdown.side_effect = Exception("Shutdown failed")

            initializer = ApplicationInitializer()
            initializer.logger = Mock()

            await initializer._shutdown_parallel_execution_components()

            initializer.logger.error.assert_called_once_with("Error during parallel execution shutdown: Shutdown failed")


class TestInitializeAppFunction:
    """Test initialize_app convenience function"""

    @pytest.mark.asyncio
    async def test_initialize_app_default_config(self):
        """Test initialize_app with default config path"""
        with patch('src.core.app_init.ApplicationInitializer') as mock_initializer_class:
            mock_initializer = Mock()
            mock_result = {"test": "result"}
            mock_initializer.initialize.return_value = mock_result
            mock_initializer_class.return_value = mock_initializer

            result = await initialize_app()

            mock_initializer_class.assert_called_once_with(None)
            mock_initializer.initialize.assert_called_once()
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_initialize_app_custom_config(self):
        """Test initialize_app with custom config path"""
        custom_path = "/custom/config.yaml"

        with patch('src.core.app_init.ApplicationInitializer') as mock_initializer_class:
            mock_initializer = Mock()
            mock_result = {"test": "result"}
            mock_initializer.initialize.return_value = mock_result
            mock_initializer_class.return_value = mock_initializer

            result = await initialize_app(custom_path)

            mock_initializer_class.assert_called_once_with(custom_path)
            mock_initializer.initialize.assert_called_once()
            assert result == mock_result


class TestApplicationInitializerIntegration:
    """Integration tests for ApplicationInitializer"""

    @pytest.mark.asyncio
    async def test_full_initialization_flow(self):
        """Test the complete initialization and shutdown flow"""
        with patch('src.core.app_init.settings') as mock_settings, \
             patch('src.core.app_init.setup_logging') as mock_setup_logging, \
             patch('signal.signal') as mock_signal, \
             patch('src.core.app_init.circuit_breaker_pool') as mock_circuit_breaker, \
             patch('src.core.app_init.load_balancer') as mock_load_balancer, \
             patch('src.core.app_init.provider_discovery') as mock_provider_discovery:

            # Setup mocks
            mock_config = Mock()
            mock_logger = Mock()
            mock_settings.return_value = mock_config
            mock_setup_logging.return_value = mock_logger

            initializer = ApplicationInitializer()

            # Initialize
            result = await initializer.initialize()

            assert "config" in result
            assert "services" in result
            assert "logger" in result
            assert result["logger"] == mock_logger

            # Shutdown
            await initializer.shutdown()

            # Verify shutdown was called
            mock_provider_discovery.stop_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_with_missing_components(self):
        """Test initialization when some components are missing"""
        with patch('src.core.app_init.settings') as mock_settings, \
             patch('src.core.app_init.setup_logging') as mock_setup_logging, \
             patch('src.core.app_init.ApplicationInitializer._setup_signal_handlers') as mock_setup_signals, \
             patch('src.core.app_init.ApplicationInitializer._initialize_services') as mock_init_services, \
             patch('src.core.app_init.circuit_breaker_pool', side_effect=ImportError("Module not found")):

            mock_config = Mock()
            mock_logger = Mock()
            mock_services = {"config": mock_config, "logger": mock_logger}

            mock_settings.return_value = mock_config
            mock_setup_logging.return_value = mock_logger
            mock_init_services.return_value = mock_services

            initializer = ApplicationInitializer()

            # Should still succeed even if parallel components fail
            result = await initializer.initialize()

            assert result["config"] == mock_config
            assert result["logger"] == mock_logger

    def test_signal_handler_edge_cases(self):
        """Test signal handler with edge cases"""
        initializer = ApplicationInitializer()
        initializer.logger = None  # No logger set

        # Should not fail even without logger
        initializer._signal_handler(signal.SIGTERM, None)
        assert initializer._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_multiple_initializations(self):
        """Test multiple initialization calls"""
        with patch('src.core.app_init.settings') as mock_settings, \
             patch('src.core.app_init.setup_logging') as mock_setup_logging, \
             patch('src.core.app_init.ApplicationInitializer._setup_signal_handlers') as mock_setup_signals, \
             patch('src.core.app_init.ApplicationInitializer._initialize_services') as mock_init_services:

            mock_config = Mock()
            mock_logger = Mock()
            mock_services = {"test": "service"}

            mock_settings.return_value = mock_config
            mock_setup_logging.return_value = mock_logger
            mock_init_services.return_value = mock_services

            initializer = ApplicationInitializer()

            # First initialization
            result1 = await initializer.initialize()
            assert result1["logger"] == mock_logger

            # Second initialization should work (though logger is already set)
            result2 = await initializer.initialize()
            assert result2["logger"] == mock_logger