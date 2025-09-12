# Migration Guide: Monolithic to Modular Architecture

This guide provides step-by-step instructions for migrating the existing monolithic codebase to the new modular package structure.

## Overview

The migration splits the current codebase into 4 main packages:

- **proxy_core**: Core routing and resilience components
- **proxy_context**: Context management and caching
- **proxy_logging**: Structured logging and observability
- **proxy_api**: FastAPI and validation components

## Migration Steps

### 1. Package Structure

```
packages/
├── proxy_core/
│   ├── src/proxy_core/
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py (from src/core/circuit_breaker.py)
│   │   ├── rate_limiter.py (from src/core/rate_limiter.py)
│   │   ├── http_client.py (from src/core/http_client.py)
│   │   └── provider_factory.py (from src/core/provider_factory.py)
│   └── pyproject.toml
├── proxy_context/
│   ├── src/proxy_context/
│   │   ├── __init__.py
│   │   ├── context_condenser.py (from src/utils/context_condenser.py)
│   │   ├── smart_cache.py (from src/core/smart_cache.py)
│   │   ├── model_cache.py (from src/core/model_cache.py)
│   │   └── memory_manager.py (from src/core/memory_manager.py)
│   └── pyproject.toml
├── proxy_logging/
│   ├── src/proxy_logging/
│   │   ├── __init__.py
│   │   ├── structured_logger.py (from src/core/logging.py)
│   │   ├── metrics_collector.py (from src/core/metrics.py)
│   │   ├── opentelemetry_config.py (new)
│   │   └── prometheus_exporter.py (new)
│   └── pyproject.toml
└── proxy_api/
    ├── src/proxy_api/
    │   ├── __init__.py
    │   ├── app.py (from main.py/main_dynamic.py)
    │   ├── schemas.py (from src/models/)
    │   └── endpoints.py (from src/api/)
    └── pyproject.toml
```

### 2. File Mapping

#### proxy_core
- `src/core/circuit_breaker.py` → `packages/proxy_core/src/proxy_core/circuit_breaker.py`
- `src/core/rate_limiter.py` → `packages/proxy_core/src/proxy_core/rate_limiter.py`
- `src/core/http_client.py` → `packages/proxy_core/src/proxy_core/http_client.py`
- `src/core/provider_factory.py` → `packages/proxy_core/src/proxy_core/provider_factory.py`

#### proxy_context
- `src/utils/context_condenser.py` → `packages/proxy_context/src/proxy_context/context_condenser.py`
- `src/core/smart_cache.py` → `packages/proxy_context/src/proxy_context/smart_cache.py`
- `src/core/model_cache.py` → `packages/proxy_context/src/proxy_context/model_cache.py`
- `src/core/memory_manager.py` → `packages/proxy_context/src/proxy_context/memory_manager.py`

#### proxy_logging
- `src/core/logging.py` → `packages/proxy_logging/src/proxy_logging/structured_logger.py`
- `src/core/metrics.py` → `packages/proxy_logging/src/proxy_logging/metrics_collector.py`

#### proxy_api
- `src/api/endpoints.py` → `packages/proxy_api/src/proxy_api/endpoints.py`
- `src/api/model_endpoints.py` → `packages/proxy_api/src/proxy_api/model_endpoints.py`
- `src/models/` → `packages/proxy_api/src/proxy_api/schemas.py`

### 3. Import Changes

#### Before (monolithic):
```python
from src.core.circuit_breaker import CircuitBreaker
from src.core.smart_cache import SmartCache
from src.core.logging import setup_logging
```

#### After (modular):
```python
from proxy_core import CircuitBreaker
from proxy_context import SmartCache
from proxy_logging import StructuredLogger
```

### 4. Configuration Updates

#### Environment Variables
Update import paths in configuration files:

```yaml
# config.yaml
logging:
  module: "proxy_logging.structured_logger"
  class: "StructuredLogger"

cache:
  module: "proxy_context.smart_cache"
  class: "SmartCache"
```

### 5. Build and Install

```bash
# Install all packages in development mode
cd packages/proxy_core && pip install -e .
cd packages/proxy_context && pip install -e .
cd packages/proxy_logging && pip install -e .
cd packages/proxy_api && pip install -e .

# Or install all at once
pip install -e packages/proxy_core -e packages/proxy_context -e packages/proxy_logging -e packages/proxy_api
```

### 6. Testing Strategy

1. **Unit Tests**: Ensure each package has comprehensive unit tests
2. **Integration Tests**: Test package interactions
3. **Backward Compatibility**: Verify existing API contracts
4. **Performance Tests**: Ensure no performance regression

### 7. Deployment Changes

#### systemd Service Updates
Update the systemd service files to use the new package structure:

```ini
# llm-proxy.service
[Service]
ExecStart=/usr/bin/python -m proxy_api.main
```

### 8. Rollback Plan

If issues arise during migration:

1. Keep the original monolithic code in a separate branch
2. Use feature flags to switch between old and new implementations
3. Gradual rollout with canary deployments

### 9. Migration Timeline

| Phase | Duration | Tasks |
|-------|----------|--------|
| Phase 1 | 1-2 days | Create package structure and move files |
| Phase 2 | 2-3 days | Update imports and fix dependencies |
| Phase 3 | 1-2 days | Update tests and documentation |
| Phase 4 | 1 day | Deploy and monitor |

### 10. Checklist

- [ ] All files moved to appropriate packages
- [ ] Import statements updated
- [ ] Dependencies correctly specified in pyproject.toml files
- [ ] Tests updated and passing
- [ ] Documentation updated
- [ ] systemd services updated
- [ ] Performance benchmarks run
- [ ] Rollback plan tested

## Support

For questions or issues during migration, please:
1. Check the individual package README files
2. Review the updated documentation
3. Open an issue in the respective package repository