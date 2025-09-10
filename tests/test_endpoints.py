import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.providers.base import ProviderError, InvalidRequestError, AuthenticationError, RateLimitError, ServiceUnavailableError
from src.providers.cohere import CohereProvider
from src.providers.azure_openai import AzureOpenAIProvider
from src.providers.blackbox import BlackboxProvider
from src.providers.perplexity import PerplexityProvider
from src.providers.grok import GrokProvider
from src.core.app_config import ProviderConfig
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app  # Assuming the FastAPI app is defined in main.py

client = TestClient(app)


@pytest.mark.asyncio
async def test_image_generations_success():
    """Test image generations endpoint success."""
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_blackbox = AsyncMock()
        mock_blackbox.create_image.return_value = {
            "id": "img_test_id",
            "object": "image",
            "created": 1234567890,
            "data": [{"url": "https://example.com/image.png"}]
        }
        mock_config = Mock()
        mock_config.name = "blackbox"
        mock_get_providers.return_value = [mock_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_blackbox

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "blackbox-alpha",
                    "prompt": "A test image",
                    "n": 1,
                    "size": "1024x1024"
                }
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.post("/v1/images/generations", json=data, headers=headers)
                assert response.status_code == 200
                json_response = response.json()
                assert "data" in json_response
                assert len(json_response["data"]) == 1
                mock_blackbox.create_image.assert_called_once()


@pytest.mark.asyncio
async def test_image_generations_invalid_request():
    """Test InvalidRequestError for image generations."""
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_blackbox = AsyncMock()
        mock_blackbox.create_image.side_effect = InvalidRequestError("Invalid image prompt")
        mock_config = Mock()
        mock_config.name = "blackbox"
        mock_get_providers.return_value = [mock_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_blackbox

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "blackbox-alpha",
                    "prompt": ""  # Invalid empty prompt
                }
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.post("/v1/images/generations", json=data, headers=headers)
                assert response.status_code == 400
                json_response = response.json()
                assert "error" in json_response
                assert json_response["error"]["type"] == "invalid_request_error"
                assert "Invalid image prompt" in json_response["error"]["message"]

@pytest.mark.asyncio
async def test_image_generations_auth_error():
    """Test AuthenticationError for image generations."""
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_blackbox = AsyncMock()
        mock_blackbox.create_image.side_effect = AuthenticationError("Blackbox invalid API key")
        mock_config = Mock()
        mock_config.name = "blackbox"
        mock_get_providers.return_value = [mock_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_blackbox

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "blackbox-alpha",
                    "prompt": "A test image",
                    "n": 1,
                    "size": "1024x1024"
                }
                headers = {"Authorization": "Bearer invalid_key"}
                response = await ac.post("/v1/images/generations", json=data, headers=headers)
                assert response.status_code == 401
                json_response = response.json()
                assert "error" in json_response
                assert json_response["error"]["type"] == "authentication_error"
                assert "Blackbox invalid API key" in json_response["error"]["message"]

@pytest.mark.asyncio
async def test_chat_completions_auth_error():
    """Test AuthenticationError for chat completions."""
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_openai = AsyncMock()
        mock_openai.create_completion.side_effect = AuthenticationError("Invalid API key")
        mock_config = Mock()
        mock_config.name = "openai"
        mock_get_providers.return_value = [mock_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_openai

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
                headers = {"Authorization": "Bearer invalid_key"}
                response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                assert response.status_code == 401
                json_response = response.json()
                assert "error" in json_response
                assert json_response["error"]["type"] == "authentication_error"
                assert "Invalid API key" in json_response["error"]["message"]


@pytest.mark.asyncio
async def test_chat_completions_rate_limit_error():
    """Test RateLimitError for chat completions."""
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_openai = AsyncMock()
        mock_openai.create_completion.side_effect = RateLimitError("Rate limit exceeded")
        mock_config = Mock()
        mock_config.name = "openai"
        mock_get_providers.return_value = [mock_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_openai

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                assert response.status_code == 429
                json_response = response.json()
                assert "error" in json_response
                assert json_response["error"]["type"] == "rate_limit_error"
                assert "Rate limit exceeded" in json_response["error"]["message"]


@pytest.mark.asyncio
async def test_chat_completions_service_unavailable():
    """Test ServiceUnavailableError for chat completions."""
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_openai = AsyncMock()
        mock_openai.create_completion.side_effect = ServiceUnavailableError("Service unavailable")
        mock_config = Mock()
        mock_config.name = "openai"
        mock_get_providers.return_value = [mock_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_openai

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                assert response.status_code == 503
                json_response = response.json()
                assert "error" in json_response
                assert json_response["error"]["type"] == "service_unavailable_error"
                assert "Service unavailable" in json_response["error"]["message"]


@pytest.mark.asyncio
async def test_chat_completions_cohere_routing():
    """Test chat completions with Cohere provider."""
    cohere_config = ProviderConfig(
        name="cohere",
        type="cohere",
        base_url="https://api.cohere.ai",
        api_key_env="COHERE_API_KEY",
        models=["command-xlarge-nightly"],
        enabled=True,
        priority=1
    )
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_cohere = AsyncMock(spec=CohereProvider)
        mock_cohere.create_completion.return_value = {
            "id": "cohere_id",
            "choices": [{"message": {"content": "Cohere response"}}],
            "model": "command-xlarge-nightly"
        }
        mock_get_providers.return_value = [cohere_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_cohere

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "command-xlarge-nightly",
                    "messages": [{"role": "user", "content": "Hello from Cohere"}]
                }
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                assert response.status_code == 200
                json_response = response.json()
                assert "choices" in json_response
                assert "Cohere response" in json_response["choices"][0]["message"]["content"]
                mock_cohere.create_completion.assert_called_once()
            
            @pytest.mark.asyncio
            async def test_chat_completions_cohere_error():
                """Test Cohere provider error in chat completions."""
                cohere_config = ProviderConfig(
                    name="cohere",
                    type="cohere",
                    base_url="https://api.cohere.ai",
                    api_key_env="COHERE_API_KEY",
                    models=["command-xlarge-nightly"],
                    enabled=True,
                    priority=1
                )
                with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
                    mock_cohere = AsyncMock(spec=CohereProvider)
                    mock_cohere.create_completion.side_effect = RateLimitError("Cohere rate limit exceeded")
                    mock_get_providers.return_value = [cohere_config]
            
                    with patch('src.api.endpoints.get_provider') as mock_get_provider:
                        mock_get_provider.return_value = mock_cohere
            
                        async with AsyncClient(app=app, base_url="http://test") as ac:
                            data = {
                                "model": "command-xlarge-nightly",
                                "messages": [{"role": "user", "content": "Hello from Cohere"}]
                            }
                            headers = {"Authorization": "Bearer test_key"}
                            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                            assert response.status_code == 429
                            json_response = response.json()
                            assert "error" in json_response
                            assert json_response["error"]["type"] == "rate_limit_error"
                            assert "Cohere rate limit exceeded" in json_response["error"]["message"]
            
            @pytest.mark.asyncio
            async def test_chat_completions_perplexity_success():
                """Test chat completions with Perplexity provider (no streaming)."""
                perplexity_config = ProviderConfig(
                    name="perplexity",
                    type="perplexity",
                    base_url="https://api.perplexity.ai",
                    api_key_env="PERPLEXITY_API_KEY",
                    models=["llama-3.1-sonar-small-128k-online"],
                    enabled=True,
                    priority=1
                )
                with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
                    mock_perplexity = AsyncMock(spec=PerplexityProvider)
                    mock_perplexity.create_completion.return_value = {
                        "id": "perplexity_id",
                        "choices": [{"message": {"content": "Perplexity response with sources"}}],
                        "model": "llama-3.1-sonar-small-128k-online",
                        "perplexity_sources": [{"title": "Test Source", "url": "https://example.com"}]
                    }
                    mock_get_providers.return_value = [perplexity_config]
            
                    with patch('src.api.endpoints.get_provider') as mock_get_provider:
                        mock_get_provider.return_value = mock_perplexity
            
                        async with AsyncClient(app=app, base_url="http://test") as ac:
                            data = {
                                "model": "llama-3.1-sonar-small-128k-online",
                                "messages": [{"role": "user", "content": "What is AI?"}]
                            }
                            headers = {"Authorization": "Bearer test_key"}
                            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                            assert response.status_code == 200
                            json_response = response.json()
                            assert "choices" in json_response
                            assert "Perplexity response" in json_response["choices"][0]["message"]["content"]
                            assert "perplexity_sources" in json_response
                            mock_perplexity.create_completion.assert_called_once()
            
            @pytest.mark.asyncio
            async def test_chat_completions_perplexity_error():
                """Test Perplexity provider error in chat completions."""
                perplexity_config = ProviderConfig(
                    name="perplexity",
                    type="perplexity",
                    base_url="https://api.perplexity.ai",
                    api_key_env="PERPLEXITY_API_KEY",
                    models=["llama-3.1-sonar-small-128k-online"],
                    enabled=True,
                    priority=1
                )
                with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
                    mock_perplexity = AsyncMock(spec=PerplexityProvider)
                    mock_perplexity.create_completion.side_effect = InvalidRequestError("Invalid query for Perplexity")
                    mock_get_providers.return_value = [perplexity_config]
            
                    with patch('src.api.endpoints.get_provider') as mock_get_provider:
                        mock_get_provider.return_value = mock_perplexity
            
                        async with AsyncClient(app=app, base_url="http://test") as ac:
                            data = {
                                "model": "llama-3.1-sonar-small-128k-online",
                                "messages": [{"role": "user", "content": ""}]  # Empty query
                            }
                            headers = {"Authorization": "Bearer test_key"}
                            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                            assert response.status_code == 400
                            json_response = response.json()
                            assert "error" in json_response
                            assert json_response["error"]["type"] == "invalid_request_error"
                            assert "Invalid query for Perplexity" in json_response["error"]["message"]
            
            @pytest.mark.asyncio
            async def test_chat_completions_grok_success():
                """Test chat completions with Grok provider (no streaming)."""
                grok_config = ProviderConfig(
                    name="grok",
                    type="grok",
                    base_url="https://api.x.ai/v1",
                    api_key_env="GROK_API_KEY",
                    models=["grok-beta"],
                    enabled=True,
                    priority=1
                )
                with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
                    mock_grok = AsyncMock(spec=GrokProvider)
                    mock_grok.create_completion.return_value = {
                        "id": "grok_id",
                        "choices": [{"message": {"content": "Grok response"}}],
                        "model": "grok-beta"
                    }
                    mock_get_providers.return_value = [grok_config]
            
                    with patch('src.api.endpoints.get_provider') as mock_get_provider:
                        mock_get_provider.return_value = mock_grok
            
                        async with AsyncClient(app=app, base_url="http://test") as ac:
                            data = {
                                "model": "grok-beta",
                                "messages": [{"role": "user", "content": "Hello from Grok"}]
                            }
                            headers = {"Authorization": "Bearer test_key"}
                            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                            assert response.status_code == 200
                            json_response = response.json()
                            assert "choices" in json_response
                            assert "Grok response" in json_response["choices"][0]["message"]["content"]
                            mock_grok.create_completion.assert_called_once()
            
            @pytest.mark.asyncio
            async def test_chat_completions_grok_error():
                """Test Grok provider error in chat completions."""
                grok_config = ProviderConfig(
                    name="grok",
                    type="grok",
                    base_url="https://api.x.ai/v1",
                    api_key_env="GROK_API_KEY",
                    models=["grok-beta"],
                    enabled=True,
                    priority=1
                )
                with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
                    mock_grok = AsyncMock(spec=GrokProvider)
                    mock_grok.create_completion.side_effect = AuthenticationError("Grok invalid API key")
                    mock_get_providers.return_value = [grok_config]
            
                    with patch('src.api.endpoints.get_provider') as mock_get_provider:
                        mock_get_provider.return_value = mock_grok
            
                        async with AsyncClient(app=app, base_url="http://test") as ac:
                            data = {
                                "model": "grok-beta",
                                "messages": [{"role": "user", "content": "Hello from Grok"}]
                            }
                            headers = {"Authorization": "Bearer test_key"}
                            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                            assert response.status_code == 401
                            json_response = response.json()
                            assert "error" in json_response
                            assert json_response["error"]["type"] == "authentication_error"
                            assert "Grok invalid API key" in json_response["error"]["message"]

@pytest.mark.asyncio
async def test_chat_completions_azure_streaming():
    """Test streaming chat completions with Azure OpenAI provider."""
    azure_config = ProviderConfig(
        name="azure_openai",
        type="azure_openai",
        base_url="https://example.openai.azure.com/openai",
        api_key_env="AZURE_OPENAI_API_KEY",
        deployment_id="gpt-4-deployment",
        api_version="2023-12-01-preview",
        models=["gpt-4-deployment"],
        enabled=True,
        priority=1
    )
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_azure = AsyncMock(spec=AzureOpenAIProvider)
        mock_azure.stream_generator.return_value = [
            '{"id": "chunk1", "choices": [{"delta": {"content": "Azure "}}]}',
            '{"id": "chunk2", "choices": [{"delta": {"content": "response"}}]}',
            '{"finish_reason": "stop"}'
        ]
        mock_get_providers.return_value = [azure_config]

        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_azure

            async with AsyncClient(app=app, base_url="http://test") as ac:
                data = {
                    "model": "gpt-4-deployment",
                    "messages": [{"role": "user", "content": "Hello from Azure"}],
                    "stream": True
                }
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
                # Verify SSE format
                content = b""
                async for chunk in response.aiter_bytes():
                    content += chunk
                lines = content.decode('utf-8').split('\n')
                assert any('data: ' in line for line in lines)
                assert any('"Azure response"' in line for line in lines)
                # Accumulate content and check full response and [DONE]
                full_content = ""
                has_done = False
                for line in lines:
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        try:
                            data = line[6:]
                            json_chunk = json.loads(data)
                            if 'choices' in json_chunk and json_chunk['choices'][0].get('delta', {}).get('content'):
                                full_content += json_chunk['choices'][0]['delta']['content']
                        except json.JSONDecodeError:
                            pass
                    elif line == 'data: [DONE]':
                        has_done = True
                assert full_content == "Azure response"
                assert has_done

def test_chat_completions_streaming():
    """Test streaming chat completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "stream": True
    }
    headers = {"Authorization": "Bearer test_key"}  # Use a test API key

    response = client.post("/v1/chat/completions", json=data, headers=headers, stream=True)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Verify SSE format in response
    lines = [line.decode('utf-8') for line in response.iter_lines() if line]
    assert len(lines) > 0
    assert any(line.startswith("data: ") for line in lines)
    # Check for end of stream
    assert any('data: [DONE]' in line for line in lines)

def test_chat_completions_non_streaming():
    """Test non-streaming chat completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "stream": False
    }
    headers = {"Authorization": "Bearer test_key"}

    response = client.post("/v1/chat/completions", json=data, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    json_response = response.json()
    assert "choices" in json_response

def test_text_completions_streaming():
    """Test streaming text completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo-instruct",
        "prompt": "Hello, world!",
        "stream": True
    }
    headers = {"Authorization": "Bearer test_key"}

    response = client.post("/v1/completions", json=data, headers=headers, stream=True)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Verify SSE format in response
    lines = [line.decode('utf-8') for line in response.iter_lines() if line]
    assert len(lines) > 0
    assert any(line.startswith("data: ") for line in lines)
    # Check for end of stream
    assert any('data: [DONE]' in line for line in lines)

def test_text_completions_non_streaming():
    """Test non-streaming text completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo-instruct",
        "prompt": "Hello, world!",
        "stream": False
    }
    headers = {"Authorization": "Bearer test_key"}

    response = client.post("/v1/completions", json=data, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    json_response = response.json()
    assert "choices" in json_response

def test_invalid_api_key():
    """Test endpoint with invalid API key."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }
    headers = {"Authorization": "Bearer invalid_key"}

    response = client.post("/v1/chat/completions", json=data, headers=headers, stream=True)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_embeddings_success():
    """Test embeddings endpoint success."""
    with patch('src.api.endpoints.app_state.provider_factory.get_providers_for_model') as mock_get_providers:
        mock_provider = AsyncMock()
        mock_provider.create_embeddings.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3], "object": "embedding", "index": 0}],
            "model": "text-embedding-ada-002",
            "usage": {"prompt_tokens": 1, "total_tokens": 1}
        }
        mock_get_providers.return_value = [mock_provider]

        async with AsyncClient(app=app, base_url="http://test") as ac:
            data = {
                "model": "text-embedding-ada-002",
                "input": "test input"
            }
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.post("/v1/embeddings", json=data, headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "data" in json_response
            assert len(json_response["data"]) == 1
            assert "embedding" in json_response["data"][0]


@pytest.mark.asyncio
async def test_list_models_success():
    """Test list models endpoint success."""
    with patch('src.api.endpoints.app_state.provider_factory.get_all_provider_info') as mock_get_info:
        mock_provider1 = Mock()
        mock_provider1.name = "openai"
        mock_provider1.type.value = "openai"
        mock_provider1.status.value = "healthy"
        mock_provider1.models = ["gpt-3.5-turbo"]
        mock_get_info.return_value = [mock_provider1]

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/v1/models")
            assert response.status_code == 200
            json_response = response.json()
            assert "data" in json_response
            assert len(json_response["data"]) == 1
            assert json_response["data"][0]["id"] == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_list_providers_success():
    """Test list providers endpoint success."""
    with patch('src.api.endpoints.app_state.provider_factory.get_all_provider_info') as mock_get_info:
        mock_provider = Mock()
        mock_provider.name = "openai"
        mock_provider.type.value = "openai"
        mock_provider.status.value = "healthy"
        mock_provider.models = ["gpt-3.5-turbo"]
        mock_provider.priority = 1
        mock_provider.last_health_check = 1234567890
        mock_provider.error_count = 0
        mock_provider.last_error = None
        mock_get_info.return_value = [mock_provider]

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/providers", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "providers" in json_response
            assert len(json_response["providers"]) == 1
            assert json_response["providers"][0]["name"] == "openai"


@pytest.mark.asyncio
async def test_get_metrics_success():
    """Test get metrics endpoint success."""
    with patch('src.api.endpoints.metrics_collector.get_all_stats') as mock_get_stats, \
         patch('src.api.endpoints.app_state.provider_factory.get_all_provider_info') as mock_get_info:
        mock_stats = {"openai": {"total_requests": 10, "success_rate": 0.9}}
        mock_get_stats.return_value = mock_stats
        mock_provider = Mock()
        mock_provider.name = "openai"
        mock_provider.status.value = "healthy"
        mock_provider.models = ["gpt-3.5-turbo"]
        mock_provider.priority = 1
        mock_provider.last_health_check = 1234567890
        mock_provider.error_count = 0
        mock_get_info.return_value = [mock_provider]

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/metrics", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "providers" in json_response
            assert "openai" in json_response["providers"]
            assert json_response["providers"]["openai"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_success():
    """Test health check endpoint success."""
    with patch('src.api.endpoints.app_state.provider_factory.get_all_provider_info') as mock_get_info:
        mock_provider1 = Mock()
        mock_provider1.status.value = "healthy"
        mock_provider2 = Mock()
        mock_provider2.status.value = "degraded"
        mock_get_info.return_value = [mock_provider1, mock_provider2]

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            json_response = response.json()
            assert "status" in json_response
            assert "providers" in json_response
            assert json_response["providers"]["healthy"] == 1


@pytest.mark.asyncio
async def test_invalid_model_error():
    """Test invalid model error case."""
    with patch('src.api.endpoints.app_state.provider_factory.get_providers_for_model') as mock_get_providers:
        mock_get_providers.return_value = []  # No providers for model

        async with AsyncClient(app=app, base_url="http://test") as ac:
            data = {
                "model": "invalid-model",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
            assert response.status_code == 400
            json_response = response.json()
            assert "error" in json_response
            assert json_response["error"]["message"] == "Model 'invalid-model' is not supported by any available provider"


@pytest.mark.asyncio
async def test_provider_unavailable_error():
    """Test provider unavailable error case."""
    with patch('src.api.endpoints.app_state.provider_factory.get_providers_for_model') as mock_get_providers:
        mock_provider = AsyncMock()
        mock_provider.create_completion.side_effect = Exception("Provider error")
        mock_get_providers.return_value = [mock_provider]

        async with AsyncClient(app=app, base_url="http://test") as ac:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.post("/v1/chat/completions", json=data, headers=headers)
            assert response.status_code == 503
            json_response = response.json()
            assert "error" in json_response
            assert json_response["error"]["message"] == "All providers are currently unavailable"


@pytest.mark.asyncio
async def test_rate_limit_exceeded():
    """Test rate limit exceeded error case."""
    with patch('src.core.rate_limiter.rate_limiter.limit') as mock_limit:
        mock_limit.side_effect = lambda func: lambda *args, **kwargs: func(*args, **kwargs)  # Mock to not limit for test
        # For actual rate limit test, would need to trigger the limit, but for simplicity, test with auth fail as proxy
        # Alternatively, mock to raise on second call
        def limited_func(func):
            calls = [0]
            def wrapper(*args, **kwargs):
                calls[0] += 1
                if calls[0] > 1:  # Simulate exceed on second
                    raise Exception("Rate limit exceeded")
                return func(*args, **kwargs)
            return wrapper
        mock_limit.return_value = limited_func

        async with AsyncClient(app=app, base_url="http://test") as ac:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            headers = {"Authorization": "Bearer test_key"}
            # First request succeeds
            response1 = await ac.post("/v1/chat/completions", json=data, headers=headers)
            assert response1.status_code == 200  # Assuming mock success
            # Second would fail, but since mock raises Exception, need to catch in test or adjust
            # For now, note as basic; full rate limit test requires slowapi mock

@pytest.mark.asyncio
async def test_rate_limit_exceeded_full():
    """Test full rate limit exceeded with slowapi mock."""
    from slowapi.errors import RateLimitExceeded
    with patch('src.core.rate_limiter.rate_limiter.limit') as mock_limit:
        calls = [0]
        def limited_wrapper(func):
            async def wrapper(*args, **kwargs):
                nonlocal calls
                calls[0] += 1
                if calls[0] > 1:
                    raise RateLimitExceeded("Rate limit exceeded")
                return await func(*args, **kwargs)
            return wrapper
        mock_limit.side_effect = limited_wrapper

        async with AsyncClient(app=app, base_url="http://test") as ac:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            headers = {"Authorization": "Bearer test_key"}
            # First request should succeed (assuming underlying success)
            with patch('src.api.endpoints.get_providers_for_model') as mock_providers:
                mock_provider = AsyncMock()
                mock_provider.create_completion.return_value = {"choices": [{"message": {"content": "Success"}}]}
                mock_config = Mock()
                mock_config.name = "openai"
                mock_providers.return_value = [mock_config]
                with patch('src.api.endpoints.get_provider') as mock_get:
                    mock_get.return_value = mock_provider
                    response1 = await ac.post("/v1/chat/completions", json=data, headers=headers)
                    assert response1.status_code == 200

            # Second request should fail with 429
            response2 = await ac.post("/v1/chat/completions", json=data, headers=headers)
            assert response2.status_code == 429
            json_response = response2.json()
            assert "error" in json_response
            assert json_response["error"]["type"] == "rate_limit_error"
            assert "Rate limit exceeded" in json_response["error"]["message"]
@pytest.mark.asyncio
async def test_text_completions_context_condensation():
    """Test automatic context condensation on text completions endpoint."""
    from src.core.app_config import ProviderConfig
    import json
    config = ProviderConfig(
        name="openai",
        type="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        models=["gpt-3.5-turbo-instruct"],
        enabled=True,
        priority=1
    )
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_get_providers.return_value = [config]
        
        mock_provider = AsyncMock()
        success_response = {
            "id": "textcmpl_test",
            "choices": [{"text": "Response after condensation"}],
            "model": "gpt-3.5-turbo-instruct"
        }
        mock_provider.create_text_completion.side_effect = [
            ValueError("context_length_exceeded"),
            success_response
        ]
        
        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            with patch('main.condense_context') as mock_condense:
                mock_condense.return_value = "Condensed prompt summary"
                
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    # Long prompt to trigger context error
                    long_prompt = "a" * 10000
                    data = {
                        "model": "gpt-3.5-turbo-instruct",
                        "prompt": long_prompt,
                        "stream": False  # Non-streaming to trigger condensation
                    }
                    headers = {"Authorization": "Bearer test_key"}
                    response = await ac.post("/v1/completions", json=data, headers=headers)
                    assert response.status_code == 200
                    json_response = response.json()
                    assert "choices" in json_response
                    assert "Response after condensation" in json_response["choices"][0]["text"]
                    # Verify retry happened
                    assert mock_provider.create_text_completion.call_count == 2
                    mock_condense.assert_called_once()
@pytest.mark.asyncio
async def test_chat_completions_context_condensation():
    """Test automatic context condensation on context length exceeded error."""
    from src.core.app_config import ProviderConfig
    import json
    config = ProviderConfig(
        name="openai",
        type="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        models=["gpt-3.5-turbo"],
        enabled=True,
        priority=1
    )
    with patch('src.api.endpoints.get_providers_for_model') as mock_get_providers:
        mock_get_providers.return_value = [config]
        
        mock_provider = AsyncMock()
        success_response = {
            "id": "chatcmpl_test",
            "choices": [{"message": {"content": "Response after condensation"}}],
            "model": "gpt-3.5-turbo"
        }
        mock_provider.create_completion.side_effect = [
            ValueError("context_length_exceeded"),
            success_response
        ]
        
        with patch('src.api.endpoints.get_provider') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            with patch('main.condense_context') as mock_condense:
                mock_condense.return_value = "Condensed summary of long context"
                
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    # Long message to trigger context error
                    long_content = "a" * 10000
                    data = {
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": long_content}],
                        "stream": False  # Non-streaming to trigger condensation
                    }
                    headers = {"Authorization": "Bearer test_key"}
                    response = await ac.post("/v1/chat/completions", json=data, headers=headers)
                    assert response.status_code == 200
                    json_response = response.json()
                    assert "choices" in json_response
                    assert "Condensed summary" in json_response["choices"][0]["message"]["content"]
                    # Verify retry happened
                    assert mock_provider.create_completion.call_count == 2
                    mock_condense.assert_called_once()