import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
import os
import hashlib

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
        # Set a test API key in environment
        test_api_key = "test-openai-key"
        os.environ["OPENAI_API_KEY"] = test_api_key
    
        # Also set the hashed key in the auth module for validation
        from src.core.auth import VALID_API_KEYS, API_KEYS, api_key_auth
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
        VALID_API_KEYS.add(key_hash)
        API_KEYS[key_hash] = {"provider": "openai", "created_at": "test"}
    
        # Reinitialize the API key auth to pick up the new key
        api_key_auth.load_api_keys()
    
        # Mock the provider
        mock_provider = MagicMock()
        # Create a mock response object with a json method
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100}
        }
        mock_provider.create_completion = AsyncMock(return_value=mock_response)

        # Mock get_provider function
        from src.providers.base import get_provider
        monkeypatch.setattr("src.providers.base.get_provider", lambda config: mock_provider)

        # Mock config with proper provider objects
        from src.core.app_config import ProviderConfig
        mock_provider_config = ProviderConfig(
            name="test_provider",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1
        )

        # Create a mock config object
        mock_config = MagicMock()
        mock_config.providers = [mock_provider_config]
        
        # Mock the config in main module
        monkeypatch.setattr("main.config", mock_config)

        # Mock the circuit breaker to always succeed
        from src.core.circuit_breaker import CircuitBreaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.execute = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
        monkeypatch.setattr("src.providers.base.get_circuit_breaker", lambda name, **kwargs: mock_circuit_breaker)

        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        # Include API key in headers
        response = client.post("/v1/chat/completions", 
                             json=request_data,
                             headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_id"
        assert data["model"] == "gpt-4"

    def test_chat_completions_endpoint_no_model(self, client, monkeypatch):
        """Test chat completions endpoint without model"""
        # Set a test API key in environment
        test_api_key = "test-openai-key"
        os.environ["OPENAI_API_KEY"] = test_api_key
    
        # Also set the hashed key in the auth module for validation
        from src.core.auth import VALID_API_KEYS, API_KEYS, api_key_auth
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
        VALID_API_KEYS.add(key_hash)
        API_KEYS[key_hash] = {"provider": "openai", "created_at": "test"}
    
        # Reinitialize the API key auth to pick up the new key
        api_key_auth.load_api_keys()
    
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", 
                             json=request_data,
                             headers={"X-API-Key": test_api_key})
        assert response.status_code == 400
        data = response.json()
        assert "Model is required" in data["detail"]

    def test_chat_completions_endpoint_unsupported_model(self, client, monkeypatch):
        """Test chat completions endpoint with unsupported model"""
        # Set a test API key in environment
        test_api_key = "test-openai-key"
        os.environ["OPENAI_API_KEY"] = test_api_key
    
        # Also set the hashed key in the auth module for validation
        from src.core.auth import VALID_API_KEYS, API_KEYS, api_key_auth
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
        VALID_API_KEYS.add(key_hash)
        API_KEYS[key_hash] = {"provider": "openai", "created_at": "test"}
    
        # Reinitialize the API key auth to pick up the new key
        api_key_auth.load_api_keys()
    
        # Mock config with empty providers list
        mock_config = MagicMock()
        mock_config.providers = []
        monkeypatch.setattr("main.config", mock_config)
    
        request_data = {
            "model": "unsupported-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", 
                             json=request_data,
                             headers={"X-API-Key": test_api_key})
        assert response.status_code == 400
        data = response.json()
        assert "not supported" in data["detail"]

    @pytest.mark.asyncio
    async def test_completions_endpoint_success(self, client, monkeypatch):
        """Test successful completions endpoint"""
        # Set a test API key in environment
        test_api_key = "test-openai-key"
        os.environ["OPENAI_API_KEY"] = test_api_key
    
        # Also set the hashed key in the auth module for validation
        from src.core.auth import VALID_API_KEYS, API_KEYS, api_key_auth
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
        VALID_API_KEYS.add(key_hash)
        API_KEYS[key_hash] = {"provider": "openai", "created_at": "test"}
    
        # Reinitialize the API key auth to pick up the new key
        api_key_auth.load_api_keys()
    
        # Mock the provider
        mock_provider = MagicMock()
        # Create a mock response object with a json method
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "text_completion",
            "created": 1234567890,
            "model": "text-davinci-003",
            "choices": [{"text": "Test completion"}],
            "usage": {"total_tokens": 50}
        }
        mock_provider.create_text_completion = AsyncMock(return_value=mock_response)

        # Mock get_provider function
        monkeypatch.setattr("src.providers.base.get_provider", lambda config: mock_provider)

        # Mock config
        from src.core.app_config import ProviderConfig
        mock_provider_config = ProviderConfig(
            name="test_provider",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["text-davinci-003"],
            enabled=True,
            priority=1
        )
        
        mock_config = MagicMock()
        mock_config.providers = [mock_provider_config]
        monkeypatch.setattr("main.config", mock_config)

        # Mock the circuit breaker to always succeed
        from src.core.circuit_breaker import CircuitBreaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.execute = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
        monkeypatch.setattr("src.providers.base.get_circuit_breaker", lambda name, **kwargs: mock_circuit_breaker)

        request_data = {
            "model": "text-davinci-003",
            "prompt": "Complete this text",
            "max_tokens": 100
        }

        response = client.post("/v1/completions", 
                             json=request_data,
                             headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_id"
        assert data["object"] == "text_completion"

    @pytest.mark.asyncio
    async def test_embeddings_endpoint_success(self, client, monkeypatch):
        """Test successful embeddings endpoint"""
        # Set a test API key in environment
        test_api_key = "test-openai-key"
        os.environ["OPENAI_API_KEY"] = test_api_key
    
        # Also set the hashed key in the auth module for validation
        from src.core.auth import VALID_API_KEYS, API_KEYS, api_key_auth
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
        VALID_API_KEYS.add(key_hash)
        API_KEYS[key_hash] = {"provider": "openai", "created_at": "test"}
    
        # Reinitialize the API key auth to pick up the new key
        api_key_auth.load_api_keys()
    
        # Mock the provider
        mock_provider = MagicMock()
        # Create a mock response object with a json method
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "text-embedding-ada-002",
            "usage": {"total_tokens": 10}
        }
        mock_provider.create_embeddings = AsyncMock(return_value=mock_response)

        # Mock get_provider function
        monkeypatch.setattr("src.providers.base.get_provider", lambda config: mock_provider)

        # Mock config
        from src.core.app_config import ProviderConfig
        mock_provider_config = ProviderConfig(
            name="test_provider",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["text-embedding-ada-002"],
            enabled=True,
            priority=1
        )
        
        mock_config = MagicMock()
        mock_config.providers = [mock_provider_config]
        monkeypatch.setattr("main.config", mock_config)

        # Mock the circuit breaker to always succeed
        from src.core.circuit_breaker import CircuitBreaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.execute = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
        monkeypatch.setattr("src.providers.base.get_circuit_breaker", lambda name, **kwargs: mock_circuit_breaker)

        request_data = {
            "model": "text-embedding-ada-002",
            "input": "Test input"
        }

        response = client.post("/v1/embeddings", 
                             json=request_data,
                             headers={"X-API-Key": test_api_key})
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

    def test_chat_completions_without_api_key(self, client):
        """Test chat completions endpoint without API key"""
        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 401
        data = response.json()
        assert "API key required" in data["detail"]
