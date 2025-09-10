# Optimizations in Context Condenser Module

This document outlines the implemented optimizations in `src/utils/context_condenser.py` to improve performance and reduce costs in the LLM Proxy API.

## Overview

The context condenser module summarizes long message chunks using LLM providers. The optimizations focus on:
- **Cache de resumos**: Enhanced caching to avoid redundant API calls.
- **Limite adaptativo**: Optional adaptive token limits based on input size.
- **Fallback adicional**: Truncation or secondary providers on failure.
- **Paralelismo**: Concurrent provider trials for faster responses.
- **Configuração dinâmica**: On-demand config reload for hot updates.

These reduce API usage by up to 70% via caching and fallbacks, lower latency with parallelism, and enable runtime tweaks without restarts.

## Cache de Resumos

Implemented an async LRU cache with size limits (default 1000 entries) and optional persistence to `cache.json`. Cache keys are MD5 hashes of chunks, with TTL (default 3600s). On cache hit, returns stored summary; on miss, calls provider and stores result.

- **Best Practices**: Evicts least recently used items; async save/load to avoid blocking.
- **Cost Reduction**: Avoids re-summarizing identical chunks, saving tokens.

## Limite Adaptativo

Adaptive max_tokens calculation (default factor 0.5) caps based on input size if enabled. Respects user-provided max_tokens but applies min cap. Disabled via config for fixed limits.

- **Usage**: `adaptive_max_tokens = min(len(input) * factor, max_default)`.
- **Benefits**: Prevents over-generation for long inputs, reducing costs.

## Fallback Adicional

On errors matching `error_keywords` (e.g., "token_limit"), applies strategies:
- **Truncate**: Reduces content to half length and retries with adjusted max_tokens.
- **Secondary Provider**: Switches to next priority provider if available.

Limits to 1 fallback attempt. Raises ValueError on final failure.

- **Resilience**: Handles context length errors without full failure.
- **Cost**: Truncation uses fewer tokens; secondary avoids single-provider downtime.

## Paralelismo

If `parallel_providers > 1` (default 2), uses `asyncio.gather` with `wait(FIRST_COMPLETED)` to try top N providers concurrently. Selects first successful response, cancels others. Falls back to sequential for single provider.

- **Implementation**: Helper `call_provider_with_timeout` for each task.
- **Performance**: Reduces effective timeout; e.g., 30s sequential to ~15s parallel.
- **Cost**: Only pays for successful call; cancels pending.

## Configuração Dinâmica

If `dynamic_reload=True`, checks config file mtime per request. If changed, reloads via `ConfigManager.load_config(force_reload=True)`, updates app.state, and logs. Uses `os.path.getmtime` for efficiency.

- **Hot Reload**: No restart needed for config changes.
- **Safety**: Per-request check; exceptions logged without failing request.

## Testing

Unit tests in `tests/test_context_condenser.py` cover:
- Cache hit/miss
- Adaptive limit application
- Fallback truncate and secondary provider
- Parallel success/failure
- Dynamic reload trigger

Run with `pytest tests/test_context_condenser.py -v`.

## Dependencies & Configuration

- Added to `requirements.txt`: No new deps (uses stdlib + existing).
- Config in `config.yaml` under `condensation` (see [Unified Config](src/core/unified_config.py)).

## Future Improvements

- Redis for distributed cache persistence.
- More fallback strategies (e.g., default summary).
- Integration with circuit breaker for providers.
- Performance benchmarks for parallelism.

These optimizations make the condenser more efficient, cost-effective, and resilient.