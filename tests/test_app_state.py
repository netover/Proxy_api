import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.core.app_state import AppState, app_state


class TestAppState:
    """Test AppState class"""

    def test_init(self):
        """Test AppState initialization"""
        state = AppState()
        assert state.config_manager is None
        assert state.provider_factory is None
        assert state.initialized is False

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful AppState initialization"""
        state = AppState()

        with patch(
            "src.core.app_state.ConfigManager"
        ) as mock_config_manager_class, patch(
            "src.core.app_state.ProviderFactory"
        ) as mock_provider_factory_class, patch(
            "src.core.app_state.rate_limiter"
        ) as mock_rate_limiter:

            mock_config_manager = Mock()
            mock_provider_factory = Mock()
            mock_config = Mock()
            mock_config.providers = [Mock(), Mock()]  # 2 providers
            mock_config.settings.rate_limit_rpm = 100

            mock_config_manager_class.return_value = mock_config_manager
            mock_provider_factory_class.return_value = mock_provider_factory
            mock_config_manager.load_config.return_value = mock_config
            mock_provider_factory.initialize_providers = AsyncMock()

            await state.initialize()

            assert state.config_manager == mock_config_manager
            assert state.provider_factory == mock_provider_factory
            assert state.initialized is True

            mock_config_manager.load_config.assert_called_once()
            mock_provider_factory.initialize_providers.assert_called_once_with(
                mock_config.providers
            )
            mock_rate_limiter.configure_limits.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test initialization when already initialized"""
        state = AppState()
        state.initialized = True

        await state.initialize()

        # Should not do anything
        assert state.initialized is True

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test AppState initialization failure"""
        state = AppState()

        with patch(
            "src.core.app_state.ConfigManager"
        ) as mock_config_manager_class:
            mock_config_manager_class.side_effect = Exception("Config error")

            with pytest.raises(Exception) as exc_info:
                await state.initialize()

            assert "Config error" in str(exc_info.value)
            assert state.initialized is False

    @pytest.mark.asyncio
    async def test_initialize_with_config_path(self):
        """Test initialization with custom config path"""
        state = AppState()
        config_path = Path("/custom/config.yaml")

        with patch(
            "src.core.app_state.ConfigManager"
        ) as mock_config_manager_class, patch(
            "src.core.app_state.ProviderFactory"
        ) as mock_provider_factory_class, patch(
            "src.core.app_state.rate_limiter"
        ) as mock_rate_limiter:

            mock_config_manager = Mock()
            mock_provider_factory = Mock()
            mock_config = Mock()
            mock_config.providers = []
            mock_config.settings.rate_limit_rpm = 50

            mock_config_manager_class.return_value = mock_config_manager
            mock_provider_factory_class.return_value = mock_provider_factory
            mock_config_manager.load_config.return_value = mock_config
            mock_provider_factory.initialize_providers = AsyncMock()

            await state.initialize(config_path)

            mock_config_manager_class.assert_called_once_with(config_path)

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful AppState shutdown"""
        state = AppState()
        state.initialized = True
        state.provider_factory = Mock()
        state.provider_factory.shutdown = AsyncMock()

        await state.shutdown()

        assert state.initialized is False
        state.provider_factory.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized"""
        state = AppState()
        state.initialized = False

        await state.shutdown()

        # Should not do anything
        assert state.initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_without_provider_factory(self):
        """Test shutdown without provider factory"""
        state = AppState()
        state.initialized = True
        state.provider_factory = None

        await state.shutdown()

        assert state.initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_failure(self):
        """Test AppState shutdown failure"""
        state = AppState()
        state.initialized = True
        state.provider_factory = Mock()
        state.provider_factory.shutdown = AsyncMock(
            side_effect=Exception("Shutdown error")
        )

        await state.shutdown()

        # Should still set initialized to False despite error
        assert state.initialized is False


class TestGlobalAppState:
    """Test global app_state instance"""

    def test_global_instance(self):
        """Test that global app_state is an AppState instance"""
        assert isinstance(app_state, AppState)
        assert app_state.initialized is False

    @pytest.mark.asyncio
    async def test_global_instance_initialization(self):
        """Test global instance can be initialized"""
        # Reset state
        app_state.initialized = False
        app_state.config_manager = None
        app_state.provider_factory = None

        with patch(
            "src.core.app_state.ConfigManager"
        ) as mock_config_manager_class, patch(
            "src.core.app_state.ProviderFactory"
        ) as mock_provider_factory_class, patch(
            "src.core.app_state.rate_limiter"
        ) as mock_rate_limiter:

            mock_config_manager = Mock()
            mock_provider_factory = Mock()
            mock_config = Mock()
            mock_config.providers = []
            mock_config.settings.rate_limit_rpm = 60

            mock_config_manager_class.return_value = mock_config_manager
            mock_provider_factory_class.return_value = mock_provider_factory
            mock_config_manager.load_config.return_value = mock_config
            mock_provider_factory.initialize_providers = AsyncMock()

            await app_state.initialize()

            assert app_state.initialized is True
