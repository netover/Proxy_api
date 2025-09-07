import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock
from src.core.app_config import ProviderConfig
from src.providers.base import Provider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider


class TestProviderBase:
    """Test base Provider class functionality through concrete implementations"""

    @pytest.fixture
    def openai_provider_config(self):
        
        return ProviderConfig(
            name="test_openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_OPENAI_API_KEY",
            models=["gpt-4"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )

    def test_openai_provider_initialization(self, openai_provider_config):
        """Test OpenAI provider initialization"""
        provider = OpenAIProvider(openai_provider_config)
        assert provider.config == openai_provider_config
        assert provider.api_key == ""  # No env var set

    @pytest.mark.asyncio
    async def test_make_request_with_retry_success(self, openai_provider_config):
        """Test successful request with retry"""
        provider = OpenAIProvider(openai_provider_config)

        # Mock the client
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        provider.client.request = AsyncMock(return_value=mock_response)

        response = await provider.make_request_with_retry(
            "GET",
            "https://api.example.com/test"
        )

        assert response == mock_response
        provider.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_with_retry_failure(self, openai_provider_config):
        """Test request failure after retries"""
        provider = OpenAIProvider(openai_provider_config)

        # Mock the client to always fail with httpx exception
        provider.client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        with pytest.raises(httpx.ConnectError):
            await provider.make_request_with_retry(
                "GET",
                "https://api.example.com/test"
            )

        # Should be called retry_attempts + 1 times (initial + retries)
        assert provider.client.request.call_count == openai_provider_config.retry_attempts + 1
    
class TestOpenAIProvider:
    """Test OpenAI provider implementation"""

    @pytest.fixture
    def openai_config(self):
        """Create OpenAI provider configuration"""
        return ProviderConfig(
            name="openai_test",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )

    def test_openai_provider_initialization(self, openai_config):
        """Test OpenAI provider initialization"""
        provider = OpenAIProvider(openai_config)
        assert provider.config == openai_config
        assert provider.config.type == "openai"

    @pytest.mark.asyncio
    async def test_create_completion(self, openai_config):
        """Test creating a chat completion"""
        provider = OpenAIProvider(openai_config)

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)

        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        result = await provider.create_completion(request)

        assert result["id"] == "test_id"
        assert result["model"] == "gpt-4"
        provider.make_request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_text_completion(self, openai_config):
        """Test creating a text completion"""
        provider = OpenAIProvider(openai_config)

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "text_completion",
            "created": 1234567890,
            "model": "text-davinci-003",
            "choices": [{"text": "Test completion"}],
            "usage": {"total_tokens": 50}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)

        request = {
            "model": "text-davinci-003",
            "prompt": "Complete this text",
            "max_tokens": 100
        }

        result = await provider.create_text_completion(request)

        assert result["id"] == "test_id"
        assert result["object"] == "text_completion"
        provider.make_request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_embeddings(self, openai_config):
        """Test creating embeddings"""
        provider = OpenAIProvider(openai_config)

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "text-embedding-ada-002",
            "usage": {"total_tokens": 10}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)

        request = {
            "model": "text-embedding-ada-002",
            "input": "Test input"
        }

        result = await provider.create_embeddings(request)

        assert result["object"] == "list"
        assert len(result["data"]) == 1
        provider.make_request_with_retry.assert_called_once()


class TestAnthropicProvider:
    """Test Anthropic provider implementation"""

    @pytest.fixture
    def anthropic_config(self):
        """Create Anthropic provider configuration"""
        return ProviderConfig(
            name="anthropic_test",
            type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_API_KEY",
            models=["claude-3-sonnet-20240229"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )

    def test_anthropic_provider_initialization(self, anthropic_config):
        """Test Anthropic provider initialization"""
        provider = AnthropicProvider(anthropic_config)
        assert provider.config == anthropic_config
        assert provider.config.type == "anthropic"

    @pytest.mark.asyncio
    async def test_create_completion(self, anthropic_config):
        """Test creating a chat completion with Anthropic"""
        provider = AnthropicProvider(anthropic_config)

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "model": "claude-3-sonnet-20240229",
            "content": [{"text": "Test response"}],
            "usage": {"input_tokens": 10, "output_tokens": 20}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)

        request = {
            "model": "claude-3-sonnet-20240229",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }

        result = await provider.create_completion(request)

        assert result["id"] == "test_id"
        assert result["model"] == "claude-3-sonnet-20240229"
        provider.make_request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_text_completion(self, anthropic_config):
        """Test creating a text completion with Anthropic"""
        provider = AnthropicProvider(anthropic_config)

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "model": "claude-3-sonnet-20240229",
            "content": [{"text": "Test completion"}],
            "usage": {"input_tokens": 5, "output_tokens": 15}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)

        request = {
            "model": "claude-3-sonnet-20240229",
            "prompt": "Complete this text",
            "max_tokens": 100
        }

        result = await provider.create_text_completion(request)

        assert result["object"] == "text_completion"
        assert result["choices"][0]["text"] == "Test completion"
        provider.make_request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_embeddings_not_implemented(self, anthropic_config):
        """Test that embeddings raises NotImplementedError for Anthropic"""
        provider = AnthropicProvider(anthropic_config)

        request = {
            "model": "claude-3-sonnet-20240229",
            "input": "Test input"
        }

        with pytest.raises(NotImplementedError):
            await provider.create_embeddings(request)
