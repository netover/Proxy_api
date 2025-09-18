import pytest
import asyncio
import time
import os
import hashlib
from unittest.mock import Mock, AsyncMock, patch
from src.utils.context import condense_context
from src.utils.cache import AsyncLRUCache
from src.core.config.models import (
    CondensationSettings,
)
from src.core.providers.base import BaseProvider


@pytest.fixture
def mock_request():
    request = Mock()
    request.app.state.config = Mock()
    request.app.state.config.providers = [
        Mock(
            enabled=True,
            priority=1,
            models=["model"],
            timeout=10,
            name="test_provider",
        )
    ]
    request.app.state.condensation_config = CondensationSettings()
    request.app.state.lru_cache = None
    request.app.state.config_mtime = 0
    return request


@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=BaseProvider)
    provider.create_completion.return_value = {
        "choices": [{"message": {"content": "test summary"}}]
    }
    return provider


@pytest.fixture
def mock_provider1():
    provider = AsyncMock(spec=BaseProvider)
    provider.create_completion.return_value = {
        "choices": [{"message": {"content": "provider1 summary"}}]
    }
    return provider


@pytest.fixture
def mock_provider2():
    provider = AsyncMock(spec=BaseProvider)
    provider.create_completion.return_value = {
        "choices": [{"message": {"content": "provider2 summary"}}]
    }
    return provider


@pytest.mark.asyncio
async def test_cache_hit(mock_request, mock_provider):
    mock_request.app.state.lru_cache = AsyncLRUCache(maxsize=1)
    chunks = ["test chunk"]
    hash_key = hashlib.md5("".join(chunks).encode()).hexdigest()
    mock_request.app.state.lru_cache.set(hash_key, ("cached summary", time.time()))
    mock_request.app.state.condensation_config.cache_ttl = 3600
    with patch(
        "src.core.providers.factory.create_provider",
        return_value=mock_provider,
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "cached summary"


@pytest.mark.asyncio
async def test_cache_miss_and_store(mock_request, mock_provider):
    mock_request.app.state.lru_cache = AsyncLRUCache(maxsize=1)
    chunks = ["new chunk"]
    with patch(
        "src.core.providers.factory.create_provider",
        return_value=mock_provider,
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "test summary"
    cached = mock_request.app.state.lru_cache.get(
        hashlib.md5("".join(chunks).encode()).hexdigest()
    )
    assert cached is not None


@pytest.mark.asyncio
async def test_adaptive_limit_enabled(mock_request, mock_provider):
    mock_request.app.state.condensation_config.adaptive_enabled = True
    mock_request.app.state.condensation_config.adaptive_factor = 0.5
    mock_request.app.state.condensation_config.max_tokens_default = 512
    chunks = ["long" * 1000]  # Large input
    with patch(
        "src.core.providers.factory.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=1000)
    # Check that max_tokens was capped
    assert mock_provider.create_completion.call_args[0][0]["max_tokens"] <= 512


@pytest.mark.asyncio
async def test_adaptive_limit_disabled(mock_request, mock_provider):
    mock_request.app.state.condensation_config.adaptive_enabled = False
    chunks = ["long" * 1000]
    with patch(
        "src.core.providers.factory.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=1000)
    assert mock_provider.create_completion.call_args[0][0]["max_tokens"] == 1000


@pytest.mark.asyncio
async def test_fallback_truncate(mock_request, mock_provider):
    mock_request.app.state.condensation_config.error_keywords = ["timeout"]
    mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
    chunks = ["full content" * 10]
    mock_provider.create_completion.side_effect = [
        Exception("timeout"),
        {"choices": [{"message": {"content": "truncated summary"}}]},
    ]
    with patch(
        "src.core.providers.factory.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "truncated summary" == summary
    # Check truncate applied
    call_args = mock_provider.create_completion.call_args_list[1][0][0]
    assert len(call_args["messages"][1]["content"]) < len("full content" * 10 * 2)


@pytest.mark.asyncio
async def test_fallback_secondary_provider(
    mock_request, mock_provider1, mock_provider2
):
    mock_request.app.state.config.providers = [
        Mock(priority=1),
        Mock(priority=2),
    ]
    mock_request.app.state.condensation_config.error_keywords = ["failed"]
    mock_request.app.state.condensation_config.fallback_strategies = [
        "secondary_provider"
    ]
    chunks = ["test"]
    mock_provider1.create_completion.side_effect = Exception("failed")
    mock_provider2.create_completion.return_value = {
        "choices": [{"message": {"content": "secondary summary"}}]
    }
    with patch(
        "src.core.providers.factory.get_provider",
        side_effect=[mock_provider1, mock_provider2],
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "secondary summary" == summary


@pytest.mark.asyncio
async def test_parallelism_success(mock_request, mock_provider1, mock_provider2):
    mock_request.app.state.condensation_config.parallel_providers = 2
    mock_request.app.state.config.providers = [
        Mock(priority=1, models=["model1"], timeout=10),
        Mock(priority=2, models=["model2"], timeout=10),
    ]
    chunks = ["test"]
    mock_provider1.create_completion = AsyncMock(
        return_value={"choices": [{"message": {"content": "parallel summary"}}]}
    )
    mock_provider2.create_completion = AsyncMock(
        return_value={"choices": [{"message": {"content": "other"}}]}
    )
    with patch(
        "src.core.providers.factory.get_provider",
        side_effect=[mock_provider1, mock_provider2],
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "parallel summary" == summary  # First one succeeds


@pytest.mark.asyncio
async def test_dynamic_reload(mock_request):
    mock_request.app.state.condensation_config.dynamic_reload = True
    mock_request.app.state.condensation_config.parallel_providers = 1
    with patch("os.path.getmtime", return_value=100), patch(
        "src.core.config.manager._last_modified", 50
    ), patch(
        "src.core.config.manager.load_config",
        return_value=Mock(settings=Mock(condensation=Mock(parallel_providers=2))),
    ):
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
    with patch(
        "src.core.providers.factory.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        summary = await condense_context(mock_request, long_chunks, max_tokens=512)
    # Verify truncation applied by checking content length in call
    call_content = mock_provider.create_completion.call_args[0][0]["messages"][1][
        "content"
    ]
    assert len(call_content) <= 100  # Truncated
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_background_non_blocking(mock_request):
    """Test proactive long context detection and background task addition (simulating route)"""
    from fastapi import BackgroundTasks

    Mock()
    mock_request.app.state.condensation_config.truncation_threshold = 100
    long_messages = [{"content": "long" * 50}] * 3  # Total > 100
    req = {"messages": long_messages}
    with patch("uuid.uuid4", return_value="test-request-id"), patch(
        "src.utils.context.condense_context",
        new_callable=AsyncMock(return_value="summary"),
    ), patch.object(BackgroundTasks, "add_task", return_value=None) as mock_add_task:
        # Simulate route call
        from src.main import background_condense

        background_condense("test-id", mock_request, ["long chunks"])
        mock_add_task.assert_called_once()
        # Check truncation would happen, but since background uses full, verify storage
        assert "test-request-id" in mock_request.app.state.summary_cache


@pytest.mark.asyncio
async def test_regex_error_detection(mock_request, mock_provider):
    """Test regex-based error detection and fallback"""
    mock_request.app.state.condensation_config.error_patterns = [
        "context.*exceeded",
        "token.*limit",
    ]
    mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
    chunks = ["test"]
    error_msg = "The context length exceeded the maximum allowed tokens"
    mock_provider.create_completion.side_effect = Exception(error_msg)
    mock_provider.create_completion.side_effect = {
        "choices": [{"message": {"content": "fallback summary"}}]
    }  # Second call after fallback
    with patch(
        "src.core.providers.factory.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        with pytest.raises(ValueError):  # Expect fallback but test detection
            await condense_context(mock_request, chunks, max_tokens=512)
    # Verify regex matched and fallback applied
    assert "fallback summary" in str(mock_provider.create_completion.call_args_list[-1])


@pytest.mark.asyncio
async def test_background_offload_simulation(mock_request, mock_provider):
    """Test background offload detection (simulate in test)"""
    from src.main import background_condense

    mock_request.app.state.summary_cache = {}
    mock_request.app.state.condensation_config.truncation_threshold = 10
    long_chunks = ["a" * 20]
    request_id = "test-bg-id"
    with patch("uuid.uuid4", return_value=request_id), patch(
        "src.utils.context.condense_context",
        new_callable=AsyncMock(return_value="bg summary"),
    ):
        background_condense(request_id, mock_request, long_chunks)
        cached = mock_request.app.state.summary_cache.get(request_id)
        assert cached == {
            "summary": "bg summary",
            "timestamp": ANY,
            "latency": ANY,
        }


@pytest.mark.asyncio
async def test_multi_provider_retrial(mock_request, mock_provider1, mock_provider2):
    """Test multi-provider fallback on error"""
    mock_request.app.state.config.providers = [
        Mock(priority=1, models=["model"], name="prov1"),
        Mock(priority=2, models=["model"], name="prov2"),
    ]
    mock_request.app.state.condensation_config.error_patterns = ["rate limit"]
    mock_request.app.state.condensation_config.fallback_strategies = [
        "secondary_provider"
    ]
    mock_request.app.state.condensation_config.parallel_providers = 1
    chunks = ["test"]
    mock_provider1.create_completion.side_effect = Exception("Rate limit exceeded")
    mock_provider2.create_completion.return_value = {
        "choices": [{"message": {"content": "retrial summary"}}]
    }
    with patch(
        "src.core.providers.factory.get_provider",
        side_effect=[mock_provider1, mock_provider2],
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "retrial summary"


@pytest.mark.asyncio
async def test_varied_provider_errors(mock_request, mock_provider):
    """Test handling of different provider-specific error messages with regex"""
    error_cases = [
        ("OpenAI context_length_exceeded", "context_length_exceeded"),
        ("Anthropic maximum context length reached", "maximum context length"),
        ("Perplexity token limit exceeded", "token limit exceeded"),
    ]
    for error_msg, pattern in error_cases:
        mock_request.app.state.condensation_config.error_patterns = [pattern]
        mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
        mock_provider.create_completion.side_effect = [
            Exception(error_msg),
            {"choices": [{"message": {"content": f"handled {pattern}"}}]},
        ]
        with patch(
            "src.core.providers.factory.get_provider",
            return_value=AsyncMock(return_value=mock_provider),
        ):
            summary = await condense_context(mock_request, ["chunk"], max_tokens=512)
            assert f"handled {pattern}" in summary


@pytest.mark.asyncio
async def test_timeout_error_fallback(mock_request, mock_provider):
    """Test fallback on timeout error"""
    mock_request.app.state.condensation_config.error_patterns = ["timeout"]
    mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
    chunks = ["test chunk"]
    mock_provider.create_completion.side_effect = asyncio.TimeoutError(
        "Request timed out"
    )
    mock_provider.create_completion.side_effect = {
        "choices": [{"message": {"content": "fallback summary"}}]
    }  # Second call after fallback
    with patch(
        "src.core.providers.factory.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "fallback summary" == summary


@pytest.mark.asyncio
async def test_rate_limit_error_fallback(mock_request, mock_provider):
    """Test fallback on rate limit error"""
    mock_request.app.state.condensation_config.error_patterns = ["rate limit"]
    mock_request.app.state.condensation_config.fallback_strategies = [
        "secondary_provider"
    ]
    mock_request.app.state.config.providers = [
        Mock(priority=1, models=["model"], name="prov1"),
        Mock(priority=2, models=["model"], name="prov2"),
    ]
    chunks = ["test"]
    mock_provider.create_completion.side_effect = RateLimitError("Rate limit exceeded")
    mock_provider2 = AsyncMock(
        return_value={"choices": [{"message": {"content": "rate limit fallback"}}]}
    )
    with patch(
        "src.core.providers.factory.get_provider",
        side_effect=[mock_provider, mock_provider2],
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "rate limit fallback" == summary


@pytest.mark.asyncio
async def test_provider_failure_fallback_sequential(mock_request):
    """Test sequential fallback on provider failure"""
    mock_request.app.state.condensation_config.parallel_providers = 1
    mock_request.app.state.condensation_config.fallback_strategies = [
        "secondary_provider"
    ]
    mock_request.app.state.config.providers = [
        Mock(priority=1, models=["model"], name="prov1"),
        Mock(priority=2, models=["model"], name="prov2"),
    ]
    chunks = ["test"]
    prov1 = AsyncMock()
    prov1.create_completion.side_effect = Exception("Provider failed")
    prov2 = AsyncMock(
        return_value={"choices": [{"message": {"content": "sequential fallback"}}]}
    )
    with patch("src.core.providers.factory.get_provider", side_effect=[prov1, prov2]):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "sequential fallback" == summary


@pytest.mark.asyncio
async def test_provider_failure_fallback_parallel(mock_request):
    """Test parallel fallback on all providers failing except one"""
    mock_request.app.state.condensation_config.parallel_providers = 2
    mock_request.app.state.config.providers = [
        Mock(priority=1, models=["model"], name="prov1"),
        Mock(priority=2, models=["model"], name="prov2"),
    ]
    chunks = ["test"]
    prov1_success = AsyncMock(
        return_value={"choices": [{"message": {"content": "parallel success"}}]}
    )
    prov2_fail = AsyncMock(side_effect=Exception("Failed"))
    with patch(
        "src.core.providers.factory.get_provider",
        side_effect=[prov1_success, prov2_fail],
    ):
        summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert "parallel success" == summary


@pytest.mark.asyncio
async def test_background_offload_integration(mock_request):
    """Test background offload integration and cache storage"""
    from src.main import background_condense

    mock_request.app.state.summary_cache = {}
    request_id = "test-bg"
    chunks = ["long context"]
    with patch(
        "src.utils.context.condense_context",
        new_callable=AsyncMock(return_value="bg summary"),
    ):
        await background_condense(request_id, mock_request, chunks)
    cached = mock_request.app.state.summary_cache.get(request_id)
    assert cached["summary"] == "bg summary"
    assert "latency" in cached


@pytest.mark.asyncio
async def test_metric_recording_cache_hit(mock_request):
    """Test metric recording for cache hit"""
    from src.core.metrics.collector import metrics_collector

    original_hits = metrics_collector.summarization_metrics.cache_hits
    mock_request.app.state.lru_cache = AsyncLRUCache(maxsize=1)
    mock_request.app.state.lru_cache.set("hash", ("cached", time.time()))
    mock_request.app.state.condensation_config.cache_ttl = 3600
    chunks = ["test"]
    await condense_context(mock_request, chunks, max_tokens=512)
    assert metrics_collector.summarization_metrics.cache_hits == original_hits + 1


@pytest.mark.asyncio
async def test_metric_recording_cache_miss(mock_request, mock_provider):
    """Test metric recording for cache miss with latency"""
    from src.core.metrics.collector import metrics_collector

    original_misses = metrics_collector.summarization_metrics.cache_misses
    original_latency = metrics_collector.summarization_metrics.total_latency
    mock_request.app.state.lru_cache = AsyncLRUCache(maxsize=1)
    chunks = ["new chunk"]
    with patch(
        "src.utils.context_condenser.get_provider",
        return_value=AsyncMock(return_value=mock_provider),
    ):
        await condense_context(mock_request, chunks, max_tokens=512)
    assert metrics_collector.summarization_metrics.cache_misses == original_misses + 1
    assert metrics_collector.summarization_metrics.total_latency > original_latency


@pytest.mark.asyncio
async def test_exact_threshold_truncation(mock_request, mock_provider):
    """Test truncation when content exactly matches threshold"""
    mock_request.app.state.condensation_config.truncation_threshold = 50
    chunks = ["a" * 25, "b" * 25]  # Total 50 chars
    with patch(
        "src.core.providers.factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    # Should not truncate since == threshold
    call_content = mock_provider.create_completion.call_args[0][0]["messages"][1][
        "content"
    ]
    assert len(call_content) == 53  # 50 + separators
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_multiple_truncation_levels(mock_request, mock_provider):
    """Test proactive truncation followed by fallback truncation"""
    mock_request.app.state.condensation_config.truncation_threshold = 100
    mock_request.app.state.condensation_config.error_keywords = ["context.*exceeded"]
    mock_request.app.state.condensation_config.fallback_strategies = ["truncate"]
    long_content = "x" * 200  # > threshold
    chunks = [long_content]
    # First call fails with error, second succeeds after truncation
    mock_provider.create_completion.side_effect = [
        Exception("context length exceeded"),
        {"choices": [{"message": {"content": "fallback summary"}}]},
    ]
    with patch(
        "src.core.providers.factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "fallback summary"
    # Check that content was truncated twice: proactive then fallback
    calls = mock_provider.create_completion.call_args_list
    first_call_content = calls[0][0][0]["messages"][1]["content"]
    second_call_content = calls[1][0][0]["messages"][1]["content"]
    assert len(first_call_content) <= 50  # Proactive truncation to half of threshold
    assert (
        len(second_call_content) <= len(first_call_content) // 2
    )  # Fallback truncation


@pytest.mark.asyncio
async def test_truncation_with_unicode(mock_request, mock_provider):
    """Test truncation preserves unicode characters correctly"""
    mock_request.app.state.condensation_config.truncation_threshold = 50
    unicode_chunks = [
        "Hello 🌟 world 🌍",
        "café résumé naïve",
        "αβγδε 中文 🚀",
    ]
    with patch(
        "src.core.providers.factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(
                mock_request, unicode_chunks, max_tokens=512
            )
    call_content = mock_provider.create_completion.call_args[0][0]["messages"][1][
        "content"
    ]
    # Should handle unicode properly, truncated if needed
    assert isinstance(call_content, str)
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_empty_chunks_list(mock_request, mock_provider):
    """Test handling of empty chunks list"""
    chunks = []
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    # Should handle empty input gracefully
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_very_large_single_chunk(mock_request, mock_provider):
    """Test handling of extremely large single chunk"""
    mock_request.app.state.condensation_config.truncation_threshold = 1000
    large_chunk = "word " * 10000  # Very large content
    chunks = [large_chunk]
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    call_content = mock_provider.create_completion.call_args[0][0]["messages"][1][
        "content"
    ]
    # Should be truncated to threshold
    assert len(call_content) <= 1000
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_unicode_special_characters(mock_request, mock_provider):
    """Test handling of various unicode and special characters"""
    chunks = [
        "Normal text",
        "🚀 🌟 🔥 💯",  # Emojis
        "café naïve résumé",  # Accented chars
        "αβγδεζηθικλμνξοπρστυφχψω",  # Greek
        "中文 español русский",  # Different scripts
        "a\tb\nc\rd",  # Control chars
        "a\x00b\x01c",  # Null bytes
    ]
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "test summary"
    # Verify content is properly joined and handled
    call_content = mock_provider.create_completion.call_args[0][0]["messages"][1][
        "content"
    ]
    assert "Normal text" in call_content
    assert "🚀" in call_content


@pytest.mark.asyncio
async def test_invalid_max_tokens(mock_request, mock_provider):
    """Test handling of invalid max_tokens values"""
    chunks = ["test"]
    # Test zero
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=0)
    assert summary == "test summary"
    # Test negative
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=-10)
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_no_enabled_providers(mock_request):
    """Test error when no providers are enabled"""
    mock_request.app.state.config.providers = [Mock(enabled=False)]
    chunks = ["test"]
    with pytest.raises(ValueError, match="No enabled providers"):
        await condense_context(mock_request, chunks, max_tokens=512)


@pytest.mark.asyncio
async def test_all_providers_fail_parallel(mock_request):
    """Test error when all parallel providers fail"""
    mock_request.app.state.condensation_config.parallel_providers = 2
    mock_request.app.state.config.providers = [
        Mock(
            enabled=True,
            priority=1,
            models=["model"],
            timeout=10,
            name="prov1",
        ),
        Mock(
            enabled=True,
            priority=2,
            models=["model"],
            timeout=10,
            name="prov2",
        ),
    ]
    chunks = ["test"]
    failing_provider = AsyncMock()
    failing_provider.create_completion.side_effect = Exception("Failed")
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=failing_provider,
    ):
        with pytest.raises(ValueError, match="All parallel providers failed"):
            await condense_context(mock_request, chunks, max_tokens=512)


@pytest.mark.asyncio
async def test_cache_persistence_file_error(mock_request, mock_provider, tmp_path):
    """Test cache persistence file write error"""
    persist_file = tmp_path / "test_cache.json"
    # Make file read-only to simulate write error
    persist_file.write_text("{}")
    persist_file.chmod(0o444)  # Read-only
    cache = AsyncLRUCache(maxsize=1, persist_file=str(persist_file))
    mock_request.app.state.lru_cache = cache
    chunks = ["test"]
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=mock_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    # Should still work despite save error
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_corrupted_cache_file(mock_request, mock_provider, tmp_path):
    """Test handling of corrupted cache file"""
    persist_file = tmp_path / "corrupted_cache.json"
    persist_file.write_text("{invalid json")
    cache = AsyncLRUCache(maxsize=1, persist_file=str(persist_file))
    mock_request.app.state.lru_cache = cache
    # Should load and rename corrupted file
    await cache.load()
    assert not persist_file.exists()
    corrupted_file = tmp_path / "corrupted_cache.json.corrupted"
    assert corrupted_file.exists()


@pytest.mark.asyncio
async def test_provider_factory_error(mock_request):
    """Test error in provider factory"""
    chunks = ["test"]
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        side_effect=Exception("Factory error"),
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            with pytest.raises(Exception, match="Factory error"):
                await condense_context(mock_request, chunks, max_tokens=512)


@pytest.mark.asyncio
async def test_config_reload_failure(mock_request, mock_provider):
    """Test config reload failure handling"""
    mock_request.app.state.condensation_config.dynamic_reload = True
    mock_request.app.state.config_mtime = 100
    chunks = ["test"]
    with patch("os.path.getmtime", return_value=200):
        with patch(
            "src.core.unified_config.config_manager.load_config",
            side_effect=Exception("Config load failed"),
        ):
            with patch(
                "src.utils.context_condenser.provider_factory.create_provider",
                return_value=mock_provider,
            ):
                with patch(
                    "src.utils.context_condenser.sorted",
                    return_value=[
                        Mock(
                            enabled=True,
                            priority=1,
                            models=["model"],
                            timeout=10,
                            name="test",
                        )
                    ],
                ):
                    summary = await condense_context(
                        mock_request, chunks, max_tokens=512
                    )
    # Should continue with old config
    assert summary == "test summary"


@pytest.mark.asyncio
async def test_invalid_provider_response(mock_request):
    """Test handling of invalid response from provider"""
    chunks = ["test"]
    invalid_provider = AsyncMock()
    invalid_provider.create_completion.return_value = {"invalid": "response"}
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        return_value=invalid_provider,
    ):
        with patch(
            "src.utils.context_condenser.sorted",
            return_value=[
                Mock(
                    enabled=True,
                    priority=1,
                    models=["model"],
                    timeout=10,
                    name="test",
                )
            ],
        ):
            with pytest.raises(KeyError):  # Missing 'choices'
                await condense_context(mock_request, chunks, max_tokens=512)


@pytest.mark.asyncio
async def test_parallel_timeout(mock_request):
    """Test timeout handling in parallel mode"""
    mock_request.app.state.condensation_config.parallel_providers = 2
    mock_request.app.state.config.providers = [
        Mock(
            enabled=True,
            priority=1,
            models=["model"],
            timeout=0.001,
            name="prov1",
        ),  # Very short timeout
        Mock(
            enabled=True,
            priority=2,
            models=["model"],
            timeout=10,
            name="prov2",
        ),
    ]
    chunks = ["test"]
    slow_provider = AsyncMock()
    slow_provider.create_completion = AsyncMock(side_effect=asyncio.TimeoutError)
    fast_provider = AsyncMock()
    fast_provider.create_completion.return_value = {
        "choices": [{"message": {"content": "fast summary"}}]
    }
    with patch(
        "src.utils.context_condenser.provider_factory.create_provider",
        side_effect=[slow_provider, fast_provider],
    ):
        with patch(
            "asyncio.wait",
            side_effect=lambda tasks, **kwargs: asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            ),
        ):
            summary = await condense_context(mock_request, chunks, max_tokens=512)
    assert summary == "fast summary"


@pytest.mark.asyncio
async def test_background_task_cancellation(mock_request, mock_provider):
    """Test background task cancellation on shutdown"""
    cache = AsyncLRUCache(maxsize=1, persist_file="test.json")
    mock_request.app.state.lru_cache = cache
    # Add a background task
    task = asyncio.create_task(asyncio.sleep(10))
    cache._background_tasks.add(task)
    await cache.shutdown()
    assert task.cancelled()
    # Cleanup
    if os.path.exists("test.json"):
        os.remove("test.json")
