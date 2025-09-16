"""
Comprehensive tests for provider methods with mocks and error scenarios.

This module tests all provider methods including create_completion, create_text_completion,
create_embeddings, and other methods with proper mocking and various error scenarios.
"""

import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Union
from unittest.mock import AsyncMock, patch, MagicMock, Mock
import pytest
import pytest_asyncio
import httpx

from src.core.provider_factory import BaseProvider, ProviderCapability
from src.core.unified_config import ProviderConfig, ProviderType
from src.core.exceptions import (
    APIConnectionError,
    AuthenticationError,
    InvalidRequestError,
    RateLimitError,
)
from src.models.model_info import ModelInfo


class MockProvider(BaseProvider):
    """Concrete implementation of BaseProvider for testing."""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Mock health check implementation."""
        return {"healthy": True, "details": {"status_code": 200}}

    async def create_completion(
        self, request: Dict[str, Any]
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """Mock create_completion implementation."""
        return await self._mock_create_completion(request)

    async def create_text_completion(
        self, request: Dict[str, Any]
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """Mock create_text_completion implementation."""
        return await self._mock_create_text_completion(request)

    async def create_embeddings(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock create_embeddings implementation."""
        return await self._mock_create_embeddings(request)

    async def _mock_create_completion(
        self, request: Dict[str, Any]
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """Mock implementation that makes HTTP request."""
        response = await self.make_request(
            "POST", f"{self.config.base_url}/chat/completions", json=request
        )
        return response.json()

    async def _mock_create_text_completion(
        self, request: Dict[str, Any]
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """Mock implementation that makes HTTP request."""
        response = await self.make_request(
            "POST", f"{self.config.base_url}/completions", json=request
        )
        return response.json()

    async def _mock_create_embeddings(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock implementation that makes HTTP request."""
        response = await self.make_request(
            "POST", f"{self.config.base_url}/embeddings", json=request
        )
        return response.json()


class TestProviderMethods:
    """Test suite for provider methods with comprehensive mocking and error scenarios."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock provider configuration."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["gpt-4", "gpt-3.5-turbo"],
            priority=1,
            enabled=True,
            timeout=30.0,
        )

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        client = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_provider(self, mock_config, mock_http_client):
        """Create a mock provider instance."""
        with patch(
            "src.core.provider_factory.get_advanced_http_client",
            return_value=mock_http_client,
        ):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = {
                    "http_client": {
                        "pool_limits": {
                            "max_keepalive_connections": 30,
                            "max_connections": 100,
                            "keepalive_timeout": 30.0,
                        },
                        "timeout": 30.0,
                    }
                }
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config)
                    return provider

    @pytest.mark.asyncio
    async def test_create_completion_success(
        self, mock_provider, mock_http_client
    ):
        """Test successful create_completion with proper response."""
        # Setup
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

        mock_http_client.request.return_value = mock_response

        # Execute
        result = await mock_provider.create_completion(request)

        # Verify
        assert result["id"] == "chatcmpl-123"
        assert result["model"] == "gpt-4"
        assert (
            result["choices"][0]["message"]["content"]
            == "Hello! How can I help you?"
        )
        assert result["usage"]["total_tokens"] == 30

        # Verify HTTP call
        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[0][0] == "POST"  # method
        assert "chat/completions" in call_args[0][1]  # url
        assert call_args[1]["json"] == request  # request body

    @pytest.mark.asyncio
    async def test_create_completion_streaming_success(
        self, mock_provider, mock_http_client
    ):
        """Test successful streaming create_completion."""
        # Setup
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        }

        # Mock streaming response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines.return_value = [
            'data: {"id": "chatcmpl-123", "choices": [{"delta": {"content": "Hello"}}]}\n\n',
            'data: {"id": "chatcmpl-123", "choices": [{"delta": {"content": " there"}}]}\n\n',
            "data: [DONE]\n\n",
        ]

        mock_http_client.request.return_value.__aenter__.return_value = (
            mock_response
        )
        mock_http_client.request.return_value.__aexit__.return_value = None

        # Execute
        stream_generator = await mock_provider.create_completion(request)

        # Collect streamed data
        chunks = []
        async for chunk in stream_generator:
            chunks.append(chunk)

        # Verify
        assert len(chunks) == 2  # Two data chunks before DONE
        assert "Hello" in chunks[0]
        assert "there" in chunks[1]

    @pytest.mark.asyncio
    async def test_create_completion_authentication_error(
        self, mock_provider, mock_http_client
    ):
        """Test create_completion with authentication error."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"error": {"message": "Invalid API key", "type": "authentication_error"}}'

        mock_http_client.request.return_value = mock_response

        # Execute & Verify
        with pytest.raises(AuthenticationError) as exc_info:
            await mock_provider.create_completion(request)

        assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_completion_rate_limit_error(
        self, mock_provider, mock_http_client
    ):
        """Test create_completion with rate limit error."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = '{"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}}'

        mock_http_client.request.return_value = mock_response

        # Execute & Verify
        with pytest.raises(RateLimitError) as exc_info:
            await mock_provider.create_completion(request)

        assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_completion_invalid_request_error(
        self, mock_provider, mock_http_client
    ):
        """Test create_completion with invalid request error."""
        request = {
            "model": "invalid-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"error": {"message": "Invalid model", "type": "invalid_request_error"}}'

        mock_http_client.request.return_value = mock_response

        # Execute & Verify
        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_completion(request)

        assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_completion_network_error(
        self, mock_provider, mock_http_client
    ):
        """Test create_completion with network connection error."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        # Mock network error
        mock_http_client.request.side_effect = httpx.ConnectError(
            "Connection failed"
        )

        # Execute & Verify
        with pytest.raises(APIConnectionError) as exc_info:
            await mock_provider.create_completion(request)

        assert "connection" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_completion_timeout_error(
        self, mock_provider, mock_http_client
    ):
        """Test create_completion with timeout error."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        # Mock timeout error
        mock_http_client.request.side_effect = httpx.TimeoutException(
            "Request timeout"
        )

        # Execute & Verify
        with pytest.raises(APIConnectionError) as exc_info:
            await mock_provider.create_completion(request)

        assert (
            "timeout" in str(exc_info.value).lower()
            or "connection" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_create_completion_malformed_response(
        self, mock_provider, mock_http_client
    ):
        """Test create_completion with malformed JSON response."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "", 0
        )

        mock_http_client.request.return_value = mock_response

        # Execute & Verify
        with pytest.raises(APIConnectionError):
            await mock_provider.create_completion(request)

    @pytest.mark.asyncio
    async def test_create_completion_missing_required_params(
        self, mock_provider
    ):
        """Test create_completion with missing required parameters."""
        # Missing messages
        request = {"model": "gpt-4"}

        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_completion(request)

        assert "messages" in str(exc_info.value)

        # Missing model
        request = {"messages": [{"role": "user", "content": "Hello"}]}

        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_completion(request)

        assert "model" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_completion_invalid_temperature(self, mock_provider):
        """Test create_completion with invalid temperature parameter."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 2.5,  # Invalid: should be 0-2
        }

        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_completion(request)

        assert "temperature" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_completion_invalid_max_tokens(self, mock_provider):
        """Test create_completion with invalid max_tokens parameter."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": "invalid",  # Should be integer
        }

        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_completion(request)

        assert "max_tokens" in str(exc_info.value)


class TestTextCompletionMethods:
    """Test suite for text completion methods."""

    @pytest.fixture
    def mock_config_text(self):
        """Create a mock provider configuration for text completion."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["gpt-3.5-turbo"],
            priority=1,
            enabled=True,
        )

    @pytest.fixture
    def mock_http_client_text(self):
        """Create a mock HTTP client for text completion."""
        client = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_provider_text(self, mock_config_text, mock_http_client_text):
        """Create a mock provider instance for text completion."""
        with patch(
            "src.core.provider_factory.get_advanced_http_client",
            return_value=mock_http_client_text,
        ):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = Mock(
                    get=lambda key, default=None: {
                        "http_client": {
                            "pool_limits": {
                                "max_keepalive_connections": 30,
                                "max_connections": 100,
                                "keepalive_timeout": 30.0,
                            },
                            "timeout": 30.0,
                        }
                    }.get(key, default)
                )
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config_text)
                    return provider

    @pytest.mark.asyncio
    async def test_create_text_completion_success(
        self, mock_provider_text, mock_http_client_text
    ):
        """Test successful create_text_completion."""
        request = {
            "model": "gpt-3.5-turbo",
            "prompt": "Complete this text:",
            "max_tokens": 50,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cmpl-123",
            "object": "text_completion",
            "created": int(time.time()),
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "text": "This is the completion of the text.",
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15,
            },
        }

        mock_http_client.request.return_value = mock_response

        # Execute
        result = await mock_provider.create_text_completion(request)

        # Verify
        assert result["id"] == "cmpl-123"
        assert (
            result["choices"][0]["text"]
            == "This is the completion of the text."
        )
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_create_text_completion_missing_prompt(
        self, mock_provider_text
    ):
        """Test create_text_completion with missing prompt."""
        request = {"model": "gpt-3.5-turbo"}

        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_text_completion(request)

        assert "prompt" in str(exc_info.value)


class TestEmbeddingsMethods:
    """Test suite for embeddings methods."""

    @pytest.fixture
    def mock_config_embeddings(self):
        """Create a mock provider configuration for embeddings."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["text-embedding-ada-002"],
            priority=1,
            enabled=True,
        )

    @pytest.fixture
    def mock_http_client_embeddings(self):
        """Create a mock HTTP client for embeddings."""
        client = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_provider_embeddings(
        self, mock_config_embeddings, mock_http_client_embeddings
    ):
        """Create a mock provider instance for embeddings."""
        with patch(
            "src.core.provider_factory.get_advanced_http_client",
            return_value=mock_http_client_embeddings,
        ):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = Mock(
                    get=lambda key, default=None: {
                        "http_client": {
                            "pool_limits": {
                                "max_keepalive_connections": 30,
                                "max_connections": 100,
                                "keepalive_timeout": 30.0,
                            },
                            "timeout": 30.0,
                        }
                    }.get(key, default)
                )
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config_embeddings)
                    return provider

    @pytest.mark.asyncio
    async def test_create_embeddings_success(
        self, mock_provider_embeddings, mock_http_client_embeddings
    ):
        """Test successful create_embeddings."""
        request = {
            "model": "text-embedding-ada-002",
            "input": ["Hello world", "How are you?"],
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3],
                    "index": 0,
                },
                {
                    "object": "embedding",
                    "embedding": [0.4, 0.5, 0.6],
                    "index": 1,
                },
            ],
            "model": "text-embedding-ada-002",
            "usage": {"prompt_tokens": 4, "total_tokens": 4},
        }

        mock_http_client.request.return_value = mock_response

        # Execute
        result = await mock_provider.create_embeddings(request)

        # Verify
        assert len(result["data"]) == 2
        assert result["data"][0]["embedding"] == [0.1, 0.2, 0.3]
        assert result["data"][1]["embedding"] == [0.4, 0.5, 0.6]
        assert result["usage"]["total_tokens"] == 4

    @pytest.mark.asyncio
    async def test_create_embeddings_missing_input(
        self, mock_provider_embeddings
    ):
        """Test create_embeddings with missing input."""
        request = {"model": "text-embedding-ada-002"}

        with pytest.raises(InvalidRequestError) as exc_info:
            await mock_provider.create_embeddings(request)

        assert "input" in str(exc_info.value)


class TestHealthCheckMethods:
    """Test suite for health check methods."""

    @pytest.fixture
    def mock_config_health(self):
        """Create a mock provider configuration for health checks."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["gpt-4"],
            priority=1,
            enabled=True,
        )

    @pytest.fixture
    def mock_http_client_health(self):
        """Create a mock HTTP client for health checks."""
        client = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_provider_health(
        self, mock_config_health, mock_http_client_health
    ):
        """Create a mock provider instance for health checks."""
        with patch(
            "src.core.provider_factory.get_advanced_http_client",
            return_value=mock_http_client_health,
        ):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = {
                    "http_client": {
                        "pool_limits": {
                            "max_keepalive_connections": 30,
                            "max_connections": 100,
                            "keepalive_timeout": 30.0,
                        },
                        "timeout": 30.0,
                    }
                }
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config_health)
                    return provider

    @pytest.mark.asyncio
    async def test_health_check_success(
        self, mock_provider_health, mock_http_client_health
    ):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_http_client.request.return_value = mock_response

        # Execute
        result = await mock_provider.health_check()

        # Verify
        assert result["healthy"] is True
        assert result["status"] == "healthy"
        assert "response_time" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(
        self, mock_provider_health, mock_http_client_health
    ):
        """Test failed health check."""
        mock_http_client.request.side_effect = httpx.ConnectError(
            "Connection failed"
        )

        # Execute
        result = await mock_provider.health_check()

        # Verify
        assert result["healthy"] is False
        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check_cached(
        self, mock_provider_health, mock_http_client_health
    ):
        """Test cached health check."""
        # First call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.request.return_value = mock_response

        result1 = await mock_provider.health_check()
        assert result1["cached"] is False

        # Second call (should be cached)
        result2 = await mock_provider.health_check()
        assert result2["cached"] is True

        # Should only make one HTTP call
        assert mock_http_client.request.call_count == 1


class TestModelDiscoveryMethods:
    """Test suite for model discovery methods."""

    @pytest.fixture
    def mock_config_discovery(self):
        """Create a mock provider configuration for model discovery."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["gpt-4"],
            priority=1,
            enabled=True,
        )

    @pytest.fixture
    def mock_http_client_discovery(self):
        """Create a mock HTTP client for model discovery."""
        client = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_provider_discovery(
        self, mock_config_discovery, mock_http_client_discovery
    ):
        """Create a mock provider instance for model discovery."""
        with patch(
            "src.core.provider_factory.get_advanced_http_client",
            return_value=mock_http_client_discovery,
        ):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = {
                    "http_client": {
                        "pool_limits": {
                            "max_keepalive_connections": 30,
                            "max_connections": 100,
                            "keepalive_timeout": 30.0,
                        },
                        "timeout": 30.0,
                    }
                }
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config_discovery)
                    return provider

    @pytest.mark.asyncio
    async def test_list_models_not_implemented(self, mock_provider_discovery):
        """Test list_models raises NotImplementedError by default."""
        with pytest.raises(NotImplementedError):
            await mock_provider.list_models()

    @pytest.mark.asyncio
    async def test_retrieve_model_not_implemented(
        self, mock_provider_discovery
    ):
        """Test retrieve_model raises NotImplementedError by default."""
        with pytest.raises(NotImplementedError):
            await mock_provider.retrieve_model("test-model")


class TestProviderCapabilities:
    """Test suite for provider capabilities."""

    @pytest.fixture
    def mock_config_capabilities(self):
        """Create a mock provider configuration for capabilities testing."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["gpt-4"],
            priority=1,
            enabled=True,
        )

    @pytest.fixture
    def mock_provider_capabilities(self, mock_config_capabilities):
        """Create a mock provider instance for capabilities testing."""
        with patch("src.core.provider_factory.get_advanced_http_client"):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = {
                    "http_client": {
                        "pool_limits": {
                            "max_keepalive_connections": 30,
                            "max_connections": 100,
                            "keepalive_timeout": 30.0,
                        },
                        "timeout": 30.0,
                    }
                }
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config_capabilities)
                    return provider

    def test_capabilities_property(self, mock_provider_capabilities):
        """Test capabilities property returns correct set."""
        capabilities = mock_provider.capabilities
        assert isinstance(capabilities, set)
        assert ProviderCapability.CHAT_COMPLETION in capabilities
        assert ProviderCapability.TEXT_COMPLETION in capabilities
        assert ProviderCapability.EMBEDDINGS in capabilities

    def test_provider_info(self, mock_provider_capabilities):
        """Test provider info property."""
        info = mock_provider.info
        assert info.name == "test_provider"
        assert info.models == ["gpt-4"]
        assert info.priority == 1
        assert info.enabled is True


class TestErrorScenarios:
    """Test suite for various error scenarios across all methods."""

    @pytest.fixture
    def mock_config_error(self):
        """Create a mock provider configuration for error scenarios."""
        return ProviderConfig(
            name="test_provider",
            type=ProviderType.OPENAI,
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["gpt-4"],
            priority=1,
            enabled=True,
        )

    @pytest.fixture
    def mock_http_client_error(self):
        """Create a mock HTTP client for error scenarios."""
        client = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_provider_error(self, mock_config_error, mock_http_client_error):
        """Create a mock provider instance for error scenarios."""
        with patch(
            "src.core.provider_factory.get_advanced_http_client",
            return_value=mock_http_client_error,
        ):
            with patch(
                "src.core.provider_factory.config_manager"
            ) as mock_config_manager:
                mock_config_manager.load_config.return_value = {
                    "http_client": {
                        "pool_limits": {
                            "max_keepalive_connections": 30,
                            "max_connections": 100,
                            "keepalive_timeout": 30.0,
                        },
                        "timeout": 30.0,
                    }
                }
                with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
                    provider = MockProvider(mock_config_error)
                    return provider

    @pytest.mark.asyncio
    async def test_server_error_500(
        self, mock_provider_error, mock_http_client_error
    ):
        """Test handling of 500 server errors."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_http_client.request.return_value = mock_response

        with pytest.raises(APIConnectionError):
            await mock_provider.create_completion(request)

    @pytest.mark.asyncio
    async def test_unexpected_http_status(
        self, mock_provider_error, mock_http_client_error
    ):
        """Test handling of unexpected HTTP status codes."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 418  # I'm a teapot
        mock_response.text = "I'm a teapot"

        mock_http_client.request.return_value = mock_response

        with pytest.raises(APIConnectionError):
            await mock_provider.create_completion(request)

    @pytest.mark.asyncio
    async def test_empty_response_body(
        self, mock_provider_error, mock_http_client_error
    ):
        """Test handling of empty response body."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError(
            "Empty response", "", 0
        )

        mock_http_client.request.return_value = mock_response

        with pytest.raises(APIConnectionError):
            await mock_provider.create_completion(request)

    @pytest.mark.asyncio
    async def test_partial_response_data(
        self, mock_provider_error, mock_http_client_error
    ):
        """Test handling of partial/incomplete response data."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            # Missing required fields like choices, usage
        }

        mock_http_client.request.return_value = mock_response

        # Should still work but with incomplete data
        result = await mock_provider.create_completion(request)
        assert result["id"] == "chatcmpl-123"
        assert "choices" not in result  # Missing field

    @pytest.mark.asyncio
    async def test_concurrent_requests_error_handling(
        self, mock_provider_error, mock_http_client_error
    ):
        """Test error handling with concurrent requests."""
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        # First request succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "id": "chatcmpl-123",
            "choices": [{"message": {"content": "Success"}}],
        }

        # Second request fails
        mock_http_client.request.side_effect = [
            mock_response_success,
            httpx.ConnectError("Connection failed"),
        ]

        # First request should succeed
        result1 = await mock_provider.create_completion(request)
        assert result1["id"] == "chatcmpl-123"

        # Second request should fail
        with pytest.raises(APIConnectionError):
            await mock_provider.create_completion(request)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
