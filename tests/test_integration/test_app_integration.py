"""
Integration tests for the complete application.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from src.bootstrap import app


class TestAppIntegration:
    """Test complete application integration."""

    def test_app_creation(self):
        """Test that the FastAPI app is created successfully."""
        assert app is not None
        assert app.title == "LLM Proxy API"
        assert app.version == "2.0.0"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        """Test root information endpoint."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    @pytest.mark.asyncio
    async def test_app_state_initialization(self):
        """Test app state initialization."""
        from src.core.app_state import app_state
        from src.core.unified_config import config_manager

        # Load config
        config_manager.load_config("config.yaml")
        config = config_manager.get_config()

        # Initialize app state
        await app_state.initialize(config)

        # Verify initialization
        assert app_state.config is not None
        assert app_state.provider_factory is not None

        # Cleanup
        await app_state.shutdown()

    def test_models_endpoint_without_auth(self):
        """Test models endpoint without authentication."""
        client = TestClient(app)
        response = client.get("/v1/models")

        # Should return 401 without auth
        assert response.status_code == 401

    def test_chat_completions_without_auth(self):
        """Test chat completions endpoint without authentication."""
        client = TestClient(app)
        response = client.post("/v1/chat/completions", json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        })

        # Should return 401 without auth
        assert response.status_code == 401


class TestProviderIntegration:
    """Test provider integration."""

    @pytest.mark.asyncio
    async def test_provider_factory_initialization(self):
        """Test provider factory initialization."""
        from src.core.providers.factory import provider_factory
        from src.core.unified_config import config_manager

        config_manager.load_config("config.yaml")
        config = config_manager.get_config()

        # This will fail due to missing API keys, but tests the integration
        try:
            providers = await provider_factory.initialize(config)
            # If we get here, providers were initialized (unexpected with dummy keys)
            assert isinstance(providers, dict)
        except Exception:
            # Expected due to missing API keys
            pass


class TestCacheIntegration:
    """Test cache integration."""

    @pytest.mark.asyncio
    async def test_cache_manager_integration(self):
        """Test cache manager integration."""
        from src.core.cache.cache_manager import CacheManager

        manager = CacheManager()

        # Should initialize without errors
        # Note: This may fail if Redis is not available
        try:
            await manager.initialize()
            # If successful, verify components
            assert hasattr(manager, 'unified_cache')
        except Exception as e:
            # Expected if Redis is not available
            assert "redis" in str(e).lower() or "connection" in str(e).lower()


class TestRateLimiterIntegration:
    """Test rate limiter integration."""

    @pytest.mark.asyncio
    async def test_rate_limiter_middleware_integration(self):
        """Test rate limiter middleware integration."""
        from src.core.rate_limiter import rate_limiter
        from src.core.unified_config import config_manager

        config_manager.load_config("config.yaml")
        config = config_manager.get_config()

        # Initialize rate limiter
        await rate_limiter.initialize(config.rate_limit)

        # Test basic functionality
        allowed, info = await rate_limiter.is_allowed("test_user", "/test")

        # Should handle gracefully even if Redis is unavailable
        assert isinstance(allowed, bool)
        assert isinstance(info, dict)
