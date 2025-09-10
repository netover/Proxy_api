import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from src.utils.context_condenser import condense_context, AsyncLRUCache
from src.core.unified_config import CondensationSettings, ProviderConfig, ProviderType
from src.providers.base import Provider

@pytest.fixture
def mock_request():
    request = Mock()
    request.app.state.config = Mock()
    request.app.state.config.providers = []
    request.app.state.condensation_config = CondensationSettings()
    request.app.state.lru_cache = None
    request.app.state.config_mtime = 0
    return request

@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=Provider)
    provider.create_completion.return_value = {
        "choices": [{"message": {"content": "test summary"}}]
    }
    return provider

@pytest.mark.asyncio
async def test_cache_hit(mock_request, mock_provider):
    mock_request.app.state.lru_cache = AsyncLRUCache(maxsize=1)
    chunks = ["test chunk"]
    mock_request.app.state.lru_cache.set("hash", ("cached summary", time.time()))
    mock_request.app.state.condensation_config.cache_ttl = 3600
    summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "cached summary"

@pytest.mark.asyncio
async def test_cache_miss_and_store(mock_request, mock_provider):
    mock_request.app.state.lru_cache = AsyncLRUCache(maxsize=1)
    chunks = ["new chunk"]
    with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "test summary"
    cached = mock_request.app.state.lru_cache.get("hash")
    assert cached is not None

@pytest.mark.asyncio
async def test_adaptive_limit_enabled(mock_request, mock_provider):
    mock_request.app.state.condensation_config.adaptive_enabled = True
    mock_request.app.state.condensation_config.adaptive_factor = 0.5
    mock_request.app.state.condensation_config.max_tokens_default = 512
    chunks = ["long" * 1000]  # Large input
    with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
        summary = await condense_context(mock_request, chunks, max_tokens=1000)
    # Check that max_tokens was capped
    assert mock_provider.create_completion.call_args[0][0]["max_tokens"] <= 512

@pytest.mark.asyncio
async def test_adaptive_limit_disabled(mock_request, mock_provider):
    mock_request.app.state.condensation_config.adaptive_enabled = False
    chunks = ["long" * 1000]
    with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
        summary = await condense_context(mock_request, chunks, max_tokens=1000)
    assert mock_provider.create_completion.call_args[0][0]["max_tokens"] == 1000

@pytest.mark.asyncio
async def test_fallback_truncate(mock_request, mock_provider):
    mock_request.app.state.condensation_config.error_keywords = ["timeout"]
    mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
    chunks = ["full content" * 10]
    mock_provider.create_completion.side_effect = [Exception("timeout"), {"choices": [{"message": {"content": "truncated summary"}}]}]
    with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "truncated summary" == summary
    # Check truncate applied
    call_args = mock_provider.create_completion.call_args_list[1][0][0]
    assert len(call_args["messages"][1]["content"]) < len("full content" * 10 * 2)

@pytest.mark.asyncio
async def test_fallback_secondary_provider(mock_request, mock_provider1, mock_provider2):
    mock_request.app.state.config.providers = [Mock(priority=1), Mock(priority=2)]
    mock_request.app.state.condensation_config.error_keywords = ["failed"]
    mock_request.app.state.condensation_config.fallback_strategies = ["secondary_provider"]
    chunks = ["test"]
    mock_provider1.create_completion.side_effect = Exception("failed")
    mock_provider2.create_completion.return_value = {"choices": [{"message": {"content": "secondary summary"}}]}
    with patch('src.utils.context_condenser.get_provider', side_effect=[mock_provider1, mock_provider2]):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "secondary summary" == summary

@pytest.mark.asyncio
async def test_parallelism_success(mock_request, mock_provider1, mock_provider2):
    mock_request.app.state.condensation_config.parallel_providers = 2
    mock_request.app.state.config.providers = [Mock(priority=1, models=["model1"], timeout=10), Mock(priority=2, models=["model2"], timeout=10)]
    chunks = ["test"]
    mock_provider1.create_completion = AsyncMock(return_value={"choices": [{"message": {"content": "parallel summary"}}]})
    mock_provider2.create_completion = AsyncMock(return_value={"choices": [{"message": {"content": "other"}}]})
    with patch('src.utils.context_condenser.get_provider', side_effect=[mock_provider1, mock_provider2]):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "parallel summary" == summary  # First one succeeds

@pytest.mark.asyncio
async def test_dynamic_reload(mock_request):
    mock_request.app.state.condensation_config.dynamic_reload = True
    mock_request.app.state.condensation_config.parallel_providers = 1
    with patch('os.path.getmtime', return_value=100), patch.object(config_manager, '_last_modified', 50), patch('src.utils.context_condenser.config_manager.load_config', return_value=Mock(settings=Mock(condensation=Mock(parallel_providers=2)))):
        summary = await condense_context(mock_request, ["test"], max_tokens=512)
    # Check reload was triggered and config updated
    assert mock_request.app.state.condensation_config.parallel_providers == 2

@pytest.mark.asyncio
async def test_lru_eviction(mock_request):
    cache = AsyncLRUCache(maxsize=1)
    cache.set("key1", ("value1", time.time()))
    cache.set("key2", ("value2", time.time()))
    assert cache.get("key1") is None  # Evicted
    assert cache.get("key2") == ("value2", time.time())

@pytest.mark.asyncio
async def test_proactive_truncation(mock_request, mock_provider):
    """Test proactive truncation before provider call if content > threshold"""
    mock_request.app.state.condensation_config.truncation_threshold = 100
    long_chunks = ["short"] + ["long text " * 50]  # Total > 100
    with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
        summary = await condense_context(mock_request, long_chunks, max_tokens=512)
    # Verify truncation applied by checking content length in call
    call_content = mock_provider.create_completion.call_args[0][0]["messages"][1]["content"]
    assert len(call_content) <= 100  # Truncated
    assert summary == "test summary"

@pytest.mark.asyncio
async def test_background_non_blocking(mock_request):
    """Test proactive long context detection and background task addition (simulating route)"""
    from fastapi import BackgroundTasks
    mock_bg_tasks = Mock()
    mock_request.app.state.condensation_config.truncation_threshold = 100
    long_messages = [{"content": "long" * 50}] * 3  # Total > 100
    req = {"messages": long_messages}
    with patch('uuid.uuid4', return_value="test-request-id"), \
         patch('src.utils.context_condenser.condense_context', new_callable=AsyncMock(return_value="summary")), \
         patch.object(BackgroundTasks, 'add_task', return_value=None) as mock_add_task:
        # Simulate route call
        from main import background_condense
        background_condense("test-id", mock_request, ["long chunks"])
        mock_add_task.assert_called_once()
        # Check truncation would happen, but since background uses full, verify storage
        assert "test-request-id" in mock_request.app.state.summary_cache

@pytest.mark.asyncio
async def test_regex_error_detection(mock_request, mock_provider):
    """Test regex-based error detection and fallback"""
    mock_request.app.state.condensation_config.error_patterns = ["context.*exceeded", "token.*limit"]
    mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
    chunks = ["test"]
    error_msg = "The context length exceeded the maximum allowed tokens"
    mock_provider.create_completion.side_effect = Exception(error_msg)
    mock_provider.create_completion.side_effect = {"choices": [{"message": {"content": "fallback summary"}}]}  # Second call after fallback
    with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
        with pytest.raises(ValueError):  # Expect fallback but test detection
            await condense_context(mock_request, chunks, max_tokens=512)
    # Verify regex matched and fallback applied
    assert "fallback summary" in str(mock_provider.create_completion.call_args_list[-1])

@pytest.mark.asyncio
async def test_background_offload_simulation(mock_request, mock_provider):
    """Test background offload detection (simulate in test)"""
    from main import background_condense
    mock_request.app.state.summary_cache = {}
    mock_request.app.state.condensation_config.truncation_threshold = 10
    long_chunks = ["a" * 20]
    request_id = "test-bg-id"
    with patch('uuid.uuid4', return_value=request_id), \
         patch('src.utils.context_condenser.condense_context', new_callable=AsyncMock(return_value="bg summary")):
        background_condense(request_id, mock_request, long_chunks)
        cached = mock_request.app.state.summary_cache.get(request_id)
        assert cached == {"summary": "bg summary", "timestamp": ANY, "latency": ANY}

@pytest.mark.asyncio
async def test_multi_provider_retrial(mock_request, mock_provider1, mock_provider2):
    """Test multi-provider fallback on error"""
    mock_request.app.state.config.providers = [Mock(priority=1, models=["model"], name="prov1"), Mock(priority=2, models=["model"], name="prov2")]
    mock_request.app.state.condensation_config.error_patterns = ["rate limit"]
    mock_request.app.state.condensation_config.fallback_strategies = ["secondary_provider"]
    mock_request.app.state.condensation_config.parallel_providers = 1
    chunks = ["test"]
    mock_provider1.create_completion.side_effect = Exception("Rate limit exceeded")
    mock_provider2.create_completion.return_value = {"choices": [{"message": {"content": "retrial summary"}}]}
    with patch('src.utils.context_condenser.get_provider', side_effect=[mock_provider1, mock_provider2]):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "retrial summary"

@pytest.mark.asyncio
async def test_varied_provider_errors(mock_request, mock_provider):
    """Test handling of different provider-specific error messages with regex"""
    error_cases = [
        ("OpenAI context_length_exceeded", "context_length_exceeded"),
        ("Anthropic maximum context length reached", "maximum context length"),
        ("Perplexity token limit exceeded", "token limit exceeded")
    ]
    for error_msg, pattern in error_cases:
        mock_request.app.state.condensation_config.error_patterns = [pattern]
        mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
        mock_provider.create_completion.side_effect = [Exception(error_msg), {"choices": [{"message": {"content": f"handled {pattern}"}}]}]
        with patch('src.utils.context_condenser.get_provider', return_value=AsyncMock(return_value=mock_provider)):
            summary = await condense_context(mock_request, ["chunk"], max_tokens=512)
            assert f"handled {pattern}" in summary