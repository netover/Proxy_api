import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock
from src.core.app_config import ProviderConfig
from src.providers.base import Provider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider
from src.providers.cohere import CohereProvider
from src.providers.azure_openai import AzureOpenAIProvider
from src.providers.blackbox import BlackboxProvider
from src.providers.base import InvalidRequestError, AuthenticationError, RateLimitError


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


class TestBlackboxProvider:
    """Test Blackbox provider implementation"""
 
    @pytest.fixture
    def blackbox_config(self):
        """Create Blackbox provider configuration"""
        return ProviderConfig(
            name="blackbox_test",
            type="blackbox",
            base_url="https://api.blackbox.ai/v1",
            api_key_env="BLACKBOX_API_KEY",
            models=["blackbox-alpha"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )
 
    def test_blackbox_provider_initialization(self, blackbox_config):
        """Test Blackbox provider initialization"""
        provider = BlackboxProvider(blackbox_config)
        assert provider.config == blackbox_config
        assert provider.config.type == "blackbox"
 
    @pytest.mark.asyncio
    async def test_create_completion(self, blackbox_config):
        """Test creating a chat completion with Blackbox"""
        provider = BlackboxProvider(blackbox_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "blackbox-alpha",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "blackbox-alpha",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }
 
        result = await provider.create_completion(request)
 
        assert result["id"] == "test_id"
        assert result["model"] == "blackbox-alpha"
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_image(self, blackbox_config):
        """Test creating an image with Blackbox"""
        provider = BlackboxProvider(blackbox_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "img_test_id",
            "object": "image",
            "created": 1234567890,
            "data": [{"url": "https://example.com/image.png"}]
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "blackbox-alpha",
            "prompt": "A test image",
            "n": 1,
            "size": "1024x1024"
        }
 
        result = await provider.create_image(request)
 
        assert result["id"] == "img_test_id"
        assert "data" in result
        assert len(result["data"]) == 1
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_completion_invalid_request(self, blackbox_config):
        """Test InvalidRequestError in Blackbox completion"""
        provider = BlackboxProvider(blackbox_config)
        provider.make_request_with_retry = AsyncMock(side_effect=httpx.HTTPStatusError("400 Bad Request", response=MagicMock(status_code=400)))
 
        request = {"model": "blackbox-alpha", "messages": []}  # Invalid: no messages
 
        with pytest.raises(InvalidRequestError):
            await provider.create_completion(request)
 
    @pytest.mark.asyncio
    async def test_create_image_auth_error(self, blackbox_config):
        """Test AuthenticationError in Blackbox image"""
        provider = BlackboxProvider(blackbox_config)
        provider.make_request_with_retry = AsyncMock(side_effect=httpx.HTTPStatusError("401 Unauthorized", response=MagicMock(status_code=401)))
 
        request = {"model": "blackbox-alpha", "prompt": "Test"}
 
        with pytest.raises(AuthenticationError):
            await provider.create_image(request)
 
 
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

class TestCohereProvider:
    """Test Cohere provider implementation"""
 
    @pytest.fixture
    def cohere_config(self):
        """Create Cohere provider configuration"""
        return ProviderConfig(
            name="cohere_test",
            type="cohere",
            base_url="https://api.cohere.ai",
            api_key_env="COHERE_API_KEY",
            models=["command-xlarge-nightly"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )
 
    def test_cohere_provider_initialization(self, cohere_config):
        """Test Cohere provider initialization"""
        provider = CohereProvider(cohere_config)
        assert provider.config == cohere_config
        assert provider.config.type == "cohere"
 
    @pytest.mark.asyncio
    async def test_create_completion(self, cohere_config):
        """Test creating a chat completion with Cohere"""
        provider = CohereProvider(cohere_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "generations": [{"text": "Test response"}],
            "meta": {"api_version": "2023-08-10"}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "command-xlarge-nightly",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }
 
        result = await provider.create_completion(request)
 
        assert result["choices"][0]["message"]["content"] == "Test response"
        assert result["model"] == "command-xlarge-nightly"
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_text_completion(self, cohere_config):
        """Test creating a text completion with Cohere"""
        provider = CohereProvider(cohere_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "generations": [{"text": "Test completion"}],
            "meta": {"prompt_tokens": 10}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "command-xlarge-nightly",
            "prompt": "Complete this text",
            "max_tokens": 100
        }
 
        result = await provider.create_text_completion(request)
 
        assert result["choices"][0]["text"] == "Test completion"
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_embeddings_not_implemented(self, cohere_config):
        """Test that embeddings raises NotImplementedError for Cohere"""
        provider = CohereProvider(cohere_config)
 
        request = {
            "model": "command-xlarge-nightly",
            "input": "Test input"
        }
 
        with pytest.raises(NotImplementedError):
            await provider.create_embeddings(request)
 
    @pytest.mark.asyncio
    async def test_create_completion_rate_limit(self, cohere_config):
        """Test RateLimitError in Cohere completion"""
        provider = CohereProvider(cohere_config)
        provider.make_request_with_retry = AsyncMock(side_effect=httpx.HTTPStatusError("429 Too Many Requests", response=MagicMock(status_code=429)))
 
        request = {"model": "command-xlarge-nightly", "messages": [{"role": "user", "content": "Hello"}]}
 
        with pytest.raises(RateLimitError):
            await provider.create_completion(request)
 
 
class TestAzureOpenAIProvider:
    """Test Azure OpenAI provider implementation"""
 
    @pytest.fixture
    def azure_config(self):
        """Create Azure OpenAI provider configuration"""
        return ProviderConfig(
            name="azure_openai_test",
            type="azure_openai",
            base_url="https://example.openai.azure.com/openai",
            api_key_env="AZURE_OPENAI_API_KEY",
            deployment_id="gpt-4-deployment",
            api_version="2023-12-01-preview",
            models=["gpt-4-deployment"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )
 
    def test_azure_openai_provider_initialization(self, azure_config):
        """Test Azure OpenAI provider initialization"""
        provider = AzureOpenAIProvider(azure_config)
        assert provider.config == azure_config
        assert provider.config.type == "azure_openai"
        assert provider.deployment_id == "gpt-4-deployment"
        assert provider.api_version == "2023-12-01-preview"
 
    @pytest.mark.asyncio
    async def test_create_completion(self, azure_config):
        """Test creating a chat completion with Azure OpenAI"""
        provider = AzureOpenAIProvider(azure_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4-deployment",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "gpt-4-deployment",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }
 
        result = await provider.create_completion(request)
 
        assert result["id"] == "test_id"
        assert result["model"] == "gpt-4-deployment"
        # Verify endpoint called with deployment and api_version
        assert "/deployments/gpt-4-deployment/chat/completions?api-version=2023-12-01-preview" in str(provider.make_request_with_retry.call_args)
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_completion_streaming(self, azure_config):
        """Test streaming chat completion with Azure OpenAI"""
        provider = AzureOpenAIProvider(azure_config)
 
        # Mock streaming response chunks
        async def mock_stream():
            yield {"id": "chunk1", "choices": [{"delta": {"content": "T"}}]}
            yield {"id": "chunk2", "choices": [{"delta": {"content": "est"}}]}
            yield {"finish_reason": "stop"}
 
        mock_response = MagicMock()
        mock_response.aiter_bytes = AsyncMock(return_value=mock_stream())
        provider.client.stream = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "gpt-4-deployment",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        }
 
        chunks = []
        async for chunk in provider.stream_generator(request):
            chunks.append(chunk)
 
        assert len(chunks) >= 2
        assert any("Test" in chunk for chunk in chunks)
 
    @pytest.mark.asyncio
    async def test_create_text_completion(self, azure_config):
        """Test creating a text completion with Azure OpenAI"""
        provider = AzureOpenAIProvider(azure_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test_id",
            "object": "text_completion",
            "created": 1234567890,
            "model": "text-davinci-deployment",
            "choices": [{"text": "Test completion"}],
            "usage": {"total_tokens": 50}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "text-davinci-deployment",
            "prompt": "Complete this text",
            "max_tokens": 100
        }
 
        result = await provider.create_text_completion(request)
 
        assert result["id"] == "test_id"
        assert result["choices"][0]["text"] == "Test completion"
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_embeddings(self, azure_config):
        """Test creating embeddings with Azure OpenAI"""
        provider = AzureOpenAIProvider(azure_config)
 
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [{"embedding": [0.1, 0.2, 0.3], "index": 0}],
            "model": "text-embedding-deployment",
            "usage": {"total_tokens": 10}
        }
        provider.make_request_with_retry = AsyncMock(return_value=mock_response)
 
        request = {
            "model": "text-embedding-deployment",
            "input": "Test input"
        }
 
        result = await provider.create_embeddings(request)
 
        assert result["object"] == "list"
        assert len(result["data"]) == 1
        provider.make_request_with_retry.assert_called_once()
 
    @pytest.mark.asyncio
    async def test_create_completion_api_connection_error(self, azure_config):
        """Test APIConnectionError in Azure completion"""
        provider = AzureOpenAIProvider(azure_config)
        provider.make_request_with_retry = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
 
        request = {"model": "gpt-4-deployment", "messages": [{"role": "user", "content": "Hello"}]}
 
        with pytest.raises(httpx.ConnectError):  # Or custom APIConnectionError if defined
            await provider.create_completion(request)
 
 
@pytest.mark.parametrize("api_key_env, expected_providers", [
    ("TEST_EMPTY_KEY", 0),  # Empty API key
    ("TEST_VALID_KEY", 1),  # Valid API key
])
def test_provider_loader_empty_api_key(api_key_env, expected_providers, monkeypatch):
    """Test provider_loader with mocked empty api_key"""
    monkeypatch.setenv(api_key_env, "" if expected_providers == 0 else "test_key")
    
    config = ProviderConfig(
        name="test_provider",
        type="openai",
        api_key_env=api_key_env,
        base_url="https://api.example.com/v1",
        models=["test-model"],
        enabled=True,
        priority=1
    )
    
    factories = get_provider_factories([config])
    # Count how many factories were successfully loaded (not skipped)
    loaded_count = len(factories)
    
    assert loaded_count == expected_providers

@pytest.mark.parametrize("enabled", [True, False])
def test_provider_loader_disabled_provider(enabled, monkeypatch):
    """Test provider_loader with disabled providers"""
    monkeypatch.setenv("TEST_KEY", "test_key")
    
    config = ProviderConfig(
        name="test_disabled",
        type="openai",
        api_key_env="TEST_KEY",
        base_url="https://api.example.com/v1",
        models=["test-model"],
        enabled=enabled,
        priority=1
    )
    
    factories = get_provider_factories([config])
    # Count how many factories were successfully loaded (not skipped)
    loaded_count = len(factories)
    
    if enabled:
        assert loaded_count == 1
    else:
        assert loaded_count == 0  # Skips disabled
