import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from src.core.app_config import config


class TestAPI:
    """Test API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "uptime" in data

    def test_providers_endpoint(self, client):
        """Test providers endpoint"""
        response = client.get("/providers")
        assert response.status_code == 200
        data = response.json()
        # Should return empty list if no config loaded
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_chat_completions_endpoint_success(self, client, monkeypatch):
        """Test successful chat completions endpoint"""
        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.create_completion = AsyncMock(return_value={
            "id": "test_id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100}
        })

        # Mock get_provider function
        from src.providers.base import get_provider
        monkeypatch.setattr("src.providers.base.get_provider", lambda config: mock_provider)

        # Mock config with proper provider objects
        from src.core.app_config import ProviderConfig
        mock_provider_config = ProviderConfig(
            name="test_provider",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"]
        )

        mock_config = MagicMock()
        mock_config.providers = [mock_provider_config]
        monkeypatch.setattr("main.config", mock_config)

        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_id"
        assert data["model"] == "gpt-4"

    def test_chat_completions_endpoint_no_model(self, client):
        """Test chat completions endpoint without model"""
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "Model is required" in data["detail"]

    def test_chat_completions_endpoint_unsupported_model(self, client):
        """Test chat completions endpoint with unsupported model"""
        request_data = {
            "model": "unsupported-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "not supported" in data["detail"]

    @pytest.mark.asyncio
    async def test_completions_endpoint_success(self, client, monkeypatch):
        """Test successful completions endpoint"""
        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.create_text_completion = AsyncMock(return_value={
            "id": "test_id",
            "object": "text_completion",
            "created": 1234567890,
            "model": "text-davinci-003",
            "choices": [{"text": "Test completion"}],
            "usage": {"total_tokens": 50}
        })

        # Mock get_provider function
        monkeypatch.setattr("src.providers.base.get_provider", lambda config: mock_provider)

        # Mock config
        mock_config = MagicMock()
        mock_config.providers = [
            MagicMock(
                name="test_provider",
                enabled=True,
                models=["text-davinci-003"],
                priority=1
            )
        ]
        monkeypatch.setattr("main.config", mock_config)

        request_data = {
            "model": "text-davinci-003",
            "prompt": "Complete this text",
            "max_tokens": 100
        }

        response = client.post("/v1/completions", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_id"
        assert data["object"] == "text_completion"

    @pytest.mark.asyncio
    async def test_embeddings_endpoint_success(self, client, monkeypatch):
        """Test successful embeddings endpoint"""
        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.create_embeddings = AsyncMock(return_value={
            "object": "list",
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "text-embedding-ada-002",
            "usage": {"total_tokens": 10}
        })

        # Mock get_provider function
        monkeypatch.setattr("src.providers.base.get_provider", lambda config: mock_provider)

        # Mock config
        mock_config = MagicMock()
        mock_config.providers = [
            MagicMock(
                name="test_provider",
                enabled=True,
                models=["text-embedding-ada-002"],
                priority=1
            )
        ]
        monkeypatch.setattr("main.config", mock_config)

        request_data = {
            "model": "text-embedding-ada-002",
            "input": "Test input"
        }

        response = client.post("/v1/embeddings", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1


class TestErrorHandling:
    """Test error handling"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_global_exception_handler(self, client):
        """Test global exception handler"""
        # This would require mocking an internal exception
        # For now, just test that the endpoint exists and returns proper error format
        pass
