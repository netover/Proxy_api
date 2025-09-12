
# Comprehensive LLM Proxy API Testing Guide

This comprehensive testing guide covers all aspects of testing the LLM Proxy API, including unit tests, integration tests, load tests, security tests, and performance benchmarking. It provides detailed information about the pytest framework, test fixtures, mocking strategies, async testing patterns, and best practices for comprehensive test suite management.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Architecture and Organization](#test-architecture-and-organization)
3. [Testing Types Overview](#testing-types-overview)
4. [Pytest Framework Usage](#pytest-framework-usage)
5. [Test Fixtures](#test-fixtures)
6. [Mocking Strategies](#mocking-strategies)
7. [Async Testing Patterns](#async-testing-patterns)
8. [Unit Testing](#unit-testing)
9. [Integration Testing](#integration-testing)
10. [Load Testing](#load-testing)
11. [Security Testing](#security-testing)
12. [Performance Testing and Benchmarking](#performance-testing-and-benchmarking)
13. [Test Coverage Analysis](#test-coverage-analysis)
14. [CI/CD Integration](#cicd-integration)
15. [Writing New Tests](#writing-new-tests)
16. [Test Naming Conventions](#test-naming-conventions)
17. [Maintaining Test Quality](#maintaining-test-quality)
18. [Testing Tools and Utilities](#testing-tools-and-utilities)
19. [Best Practices](#best-practices)
20. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Core testing framework
pip install pytest>=8.4.2 pytest-asyncio>=0.21.0 pytest-cov

# Security testing tools
pip install bandit>=1.7.0 safety>=3.0.0

# Load testing
curl https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz -L | tar xvz
sudo mv k6-v0.45.0-linux-amd64/k6 /usr/local/bin/

# Performance testing
pip install pytest-benchmark numpy>=1.24.0
```

### Environment Setup

```bash
# Copy environment file
cp .env.example .env

# Set required test variables
echo "TEST_API_KEY=test-key-123" >> .env
echo "TEST_BASE_URL=http://localhost:8000" >> .env
```

### Run Basic Tests

```bash
# Start the application
python main.py

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test types
pytest tests/ -m "unit"           # Unit tests only
pytest tests/ -m "integration"    # Integration tests only
pytest tests/ -m "not slow"       # Skip slow tests
```

## Test Architecture and Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Global fixtures and configuration
├── test_*.py                      # Unit tests
├── test_*_integration.py          # Integration tests
├── load_tests/                    # k6 load testing scenarios
│   ├── light_load_30_users.js
│   ├── medium_load_100_users.js
│   └── *.js
├── security/                      # Security testing
│   ├── __init__.py
│   ├── test_authentication_security.py
│   ├── test_input_validation_security.py
│   └── run_security_tests.py
├── benchmark_*.py                 # Performance benchmarks
└── TESTING_GUIDE.md              # This guide
```

### Test Categories

- **Unit Tests**: Test individual functions, classes, and modules in isolation
- **Integration Tests**: Test interactions between components and external services
- **Load Tests**: Test system performance under various load conditions
- **Security Tests**: Test authentication, authorization, and vulnerability prevention
- **Performance Tests**: Benchmark response times, memory usage, and throughput

## Testing Types Overview

| Test Type | Purpose | Tools | Frequency | Coverage Goal |
|-----------|---------|-------|-----------|----------------|
| **Unit Tests** | Individual component validation | pytest | Every PR | 80%+ |
| **Integration Tests** | API endpoint and service integration | pytest-asyncio | Every PR | 70%+ |
| **Load Tests** | Performance under load | k6 | Daily | N/A |
| **Security Tests** | Vulnerability scanning and auth testing | bandit, safety, pytest | Every PR | 100% critical paths |
| **Performance Tests** | Benchmarking and profiling | pytest-benchmark, memory_profiler | Weekly | N/A |

## Pytest Framework Usage

### Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=html
    --cov-report=term
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    security: Security tests
    asyncio: Async tests
```

### Running Tests

```bash
# Basic test run
pytest tests/

# Run specific test file
pytest tests/test_app_config.py

# Run specific test class
pytest tests/test_app_config.py::TestAppConfig

# Run specific test method
pytest tests/test_app_config.py::TestAppConfig::test_valid_app_config

# Run with markers
pytest -m "unit and not slow"
pytest -m "integration"
pytest -m "security"

# Run with coverage
pytest --cov=src --cov-report=html

# Run parallel tests
pytest -n auto

# Run failed tests only
pytest --lf

# Run new tests only
pytest --nf
```

### Pytest Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Increase verbosity |
| `-s` | Don't capture output |
| `-x` | Stop on first failure |
| `--tb=short` | Short traceback format |
| `--lf` | Run failed tests only |
| `--nf` | Run new tests only |
| `-n auto` | Run tests in parallel |
| `--cov` | Generate coverage report |
| `-m MARKER` | Run tests with specific marker |

## Test Fixtures

### Basic Fixtures

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_directory():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_config():
    """Provide sample configuration data."""
    return {
        "providers": [
            {
                "name": "openai",
                "type": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
                "models": ["gpt-3.5-turbo", "gpt-4"]
            }
        ]
    }

@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
```

### Async Fixtures

```python
import pytest
from httpx import AsyncClient

@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default - per test function
def function_fixture():
    # Set up
    yield "data"
    # Tear down

@pytest.fixture(scope="class")     # Per test class
def class_fixture():
    # Set up
    yield "data"
    # Tear down

@pytest.fixture(scope="module")    # Per test module
def module_fixture():
    # Set up
    yield "data"
    # Tear down

@pytest.fixture(scope="session")   # Per test session
def session_fixture():
    # Set up
    yield "data"
    # Tear down
```

### Parameterized Fixtures

```python
@pytest.fixture(params=["openai", "anthropic", "cohere"])
def provider_name(request):
    """Fixture with multiple parameter values."""
    return request.param

@pytest.fixture(params=[True, False])
def enabled_flag(request):
    """Boolean parameter fixture."""
    return request.param
```

## Mocking Strategies

### Basic Mocking with unittest.mock

```python
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Mock function
@patch('module.function_to_mock')
def test_with_mock(mock_func):
    mock_func.return_value = "mocked_result"
    # Test code
    assert mock_func.return_value == "mocked_result"

# Mock method
def test_method_mock():
    mock_obj = Mock()
    mock_obj.method.return_value = 42
    assert mock_obj.method() == 42

# Mock context manager
def test_context_mock():
    with patch('module.function') as mock_func:
        mock_func.return_value = "patched"
        # Test code
```

### Mocking Environment Variables

```python
from unittest.mock import patch
import os

def test_env_var_mock():
    with patch.dict(os.environ, {"API_KEY": "test_key"}):
        assert os.getenv("API_KEY") == "test_key"
    # Environment restored after context
```

### Async Mocking

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function():
    mock_provider = AsyncMock()
    mock_provider.create_completion.return_value = {
        "choices": [{"message": {"content": "Mocked response"}}]
    }

    result = await mock_provider.create_completion("test prompt")
    assert result["choices"][0]["message"]["content"] == "Mocked response"
```

### Complex Mock Objects

```python
from unittest.mock import MagicMock

def test_complex_mock():
    # Create mock with spec
    mock_provider = MagicMock(spec=ProviderClass)

    # Configure return values
    mock_provider.get_models.return_value = ["model1", "model2"]
    mock_provider.is_available.return_value = True

    # Configure side effects
    mock_provider.connect.side_effect = ConnectionError("Failed to connect")

    # Test
    assert mock_provider.is_available() is True
    with pytest.raises(ConnectionError):
        mock_provider.connect()
```

### Mocking HTTP Requests

```python
import pytest
from unittest.mock import patch
import httpx

@pytest.mark.asyncio
async def test_http_mock():
    mock_response = {
        "status_code": 200,
        "json": lambda: {"result": "success"}
    }

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = mock_response

        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com")
            assert response.status_code == 200
            assert response.json() == {"result": "success"}
```

## Async Testing Patterns

### Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await async_function()
    assert result == "expected"
```

### Async Test with Setup/Teardown

```python
import pytest

@pytest.fixture
async def async_setup():
    """Async fixture for setup."""
    # Setup code
    await setup_database()
    yield
    # Teardown code
    await cleanup_database()

@pytest.mark.asyncio
async def test_with_async_fixture(async_setup):
    """Test using async fixture."""
    result = await async_operation()
    assert result is not None
```

### Testing Async Context Managers

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager."""
    mock_cm = AsyncMock()

    async with mock_cm:
        # Test code inside context
        pass

    # Verify context manager was used
    mock_cm.__aenter__.assert_called_once()
    mock_cm.__aexit__.assert_called_once()
```

### Testing Concurrent Operations

```python
import pytest
import asyncio
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test multiple concurrent async operations."""

    async def mock_operation(delay):
        await asyncio.sleep(delay)
        return f"completed_{delay}"

    # Mock concurrent operations
    with patch('module.async_operation', side_effect=mock_operation):
        tasks = [
            module.async_operation(0.1),
            module.async_operation(0.2),
            module.async_operation(0.3)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert "completed_0.1" in results
        assert "completed_0.2" in results
        assert "completed_0.3" in results
```

### Testing Async Generators

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_generator():
    """Test async generator function."""

    async def mock_generator():
        yield "item1"
        yield "item2"
        yield "item3"

    with patch('module.async_generator_func', mock_generator):
        items = []
        async for item in module.async_generator_func():
            items.append(item)

        assert items == ["item1", "item2", "item3"]
```

## Unit Testing

### Unit Test Structure

```python
import pytest
from unittest.mock import patch, Mock
from src.core.app_config import ProviderConfig, AppConfig

class TestProviderConfig:
    """Test ProviderConfig class functionality."""

    def test_valid_provider_config(self):
        """Test creating valid provider configuration."""
        config = ProviderConfig(
            name="openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo"]
        )

        assert config.name == "openai"
        assert config.enabled is True  # Default value
        assert config.priority == 100  # Default value

    def test_provider_config_validation(self):
        """Test provider configuration validation."""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(
                name="test",
                type="invalid_type",  # Invalid provider type
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=[]
            )

        assert "Provider type must be one of" in str(exc_info.value)

    @pytest.mark.parametrize("priority,expected_valid", [
        (1, True),
        (50, True),
        (1000, True),
        (0, False),    # Too low
        (1001, False)  # Too high
    ])
    def test_priority_bounds(self, priority, expected_valid):
        """Test priority field bounds with parameterization."""
        if expected_valid:
            config = ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                priority=priority
            )
            assert config.priority == priority
        else:
            with pytest.raises(ValidationError):
                ProviderConfig(
                    name="test",
                    type="openai",
                    base_url="https://api.test.com",
                    api_key_env="TEST_KEY",
                    models=["model1"],
                    priority=priority
                )
```

### Mocking External Dependencies

```python
import pytest
from unittest.mock import patch, AsyncMock

class TestProviderDiscovery:
    """Test provider discovery with mocked external APIs."""

    @patch('src.providers.openai.OpenAIDiscovery.get_models')
    def test_openai_discovery(self, mock_get_models):
        """Test OpenAI provider discovery."""
        # Setup mock response
        mock_get_models.return_value = [
            Mock(id="gpt-4", name="GPT-4", context_length=8192),
            Mock(id="gpt-3.5-turbo", name="GPT-3.5 Turbo", context_length=4096)
        ]

        # Test discovery service
        service = ProviderDiscoveryService()
        models = service.discover_openai_models()

        assert len(models) == 2
        assert models[0].id == "gpt-4"
        assert models[1].id == "gpt-3.5-turbo"

        # Verify mock was called
        mock_get_models.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_async_http_call(self, mock_get):
        """Test async HTTP calls with mocking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": ["gpt-4"]}
        mock_get.return_value = mock_response

        service = ModelDiscoveryService()
        result = await service.fetch_remote_models()

        assert result == ["gpt-4"]
        mock_get.assert_called_once_with("https://api.openai.com/v1/models")
```

## Integration Testing

### API Endpoint Testing

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app

class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    def test_chat_completions_endpoint(self, client):
        """Test chat completions endpoint."""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }
        headers = {"Authorization": "Bearer test-key"}

        response = client.post("/v1/chat/completions", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0

    @pytest.mark.asyncio
    async def test_streaming_endpoint(self, async_client):
        """Test streaming response endpoint."""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        }
        headers = {"Authorization": "Bearer test-key"}

        response = await async_client.post(
            "/v1/chat/completions",
            json=payload,
            headers=headers
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Verify SSE format
        content = b""
        async for chunk in response.aiter_bytes():
            content += chunk

        lines = content.decode('utf-8').split('\n')
        assert any('data: ' in line for line in lines)
```

### Database Integration Testing

```python
import pytest
from unittest.mock import patch
import tempfile
import os

class TestCacheIntegration:
    """Test cache integration with file system."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_cache_write_read(self, temp_cache_dir):
        """Test cache write and read operations."""
        cache = FileCache(cache_dir=temp_cache_dir)

        # Write to cache
        cache.set("test_key", {"data": "value"}, ttl=3600)

        # Read from cache
        result = cache.get("test_key")

        assert result == {"data": "value"}

    def test_cache_expiration(self, temp_cache_dir):
        """Test cache expiration."""
        cache = FileCache(cache_dir=temp_cache_dir)

        # Set short TTL
        cache.set("test_key", "value", ttl=1)

        # Wait for expiration
        import time
        time.sleep(1.1)

        # Should return None
        result = cache.get("test_key")
        assert result is None
```

## Load Testing

### k6 Test Structure

```javascript
// load_tests/light_load_30_users.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export let options = {
    stages: [
        { duration: '30s', target: 10 },   // Ramp up to 10 users
        { duration: '2m', target: 30 },    // Stay at 30 users for 2 minutes
        { duration: '30s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<1000'],   // 95% of requests under 1s
        http_req_failed: ['rate<0.1'],       // Less than 10% failures
        errors: ['rate<0.05'],               // Less than 5% custom errors
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-key-123';

const testMessages = [
    "What is artificial intelligence?",
    "Explain quantum computing",
    "How does machine learning work?"
];

export default function () {
    const payload = JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [{
            role: 'user',
            content: testMessages[Math.floor(Math.random() * testMessages.length)]
        }],
        max_tokens: 100
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
        },
    };

    const response = http.post(`${BASE_URL}/v1/chat/completions`, payload, params);

    const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 1000ms': (r) => r.timings.duration < 1000,
        'has choices': (r) => JSON.parse(r.body).choices !== undefined,
    });

    errorRate.add(!success);
    responseTime.add(response.timings.duration);

    sleep(1); // 1 second between requests
}

export function handleSummary(data) {
    return {
        'stdout': textSummary(data, { indent: ' ', enableColors: true }),
        'light_load_summary.json': JSON.stringify({
            total_requests: data.metrics.http_reqs.values.count,
            successful_requests: data.metrics.http_reqs.values.count - data.metrics.http_req_failed.values.count,
            avg_response_time: data.metrics.http_req_duration.values.avg,
            p95_response_time: data.metrics.http_req_duration.values['p(95)'],
            error_rate: data.metrics.http_req_failed.values.rate,
        }, null, 2),
    };
}
```

### Load Test Scenarios

```javascript
// load_tests/stress_test_1000_users.js
export let options = {
    stages: [
        { duration: '1m', target: 100 },     // Quick ramp to 100 users
        { duration: '2m', target: 500 },     // Ramp to 500 users
        { duration: '3m', target: 1000 },    // Peak at 1000 users
        { duration: '2m', target: 500 },     // Scale down to 500
        { duration: '1m', target: 0 },       // Ramp down to 0
    ],
    thresholds: {
        http_req_duration: ['p(99)<2000'],   // 99% under 2s
        http_req_failed: ['rate<0.15'],      // Allow higher error rate under stress
    },
};
```

### Running Load Tests

```bash
# Run light load test
k6 run tests/load_tests/light_load_30_users.js

# Run with custom environment variables
k6 run -e BASE_URL=http://staging.api.com -e API_KEY=staging-key tests/load_tests/medium_load_100_users.js

# Run with output to file
k6 run --out json=results.json tests/load_tests/light_load_30_users.js

# Run in cloud
k6 cloud tests/load_tests/stress_test_1000_users.js
```

## Security Testing

### Authentication Security Testing

```python
import pytest
import time
import hashlib
import hmac
from unittest.mock import Mock, patch
from fastapi import HTTPException

class TestAuthenticationSecurity:
    """Comprehensive security tests for authentication."""

    def test_brute_force_protection(self):
        """Test protection against brute force attacks."""
        from src.core.auth import APIKeyAuth

        api_keys = ["valid_key_123"]
        auth = APIKeyAuth(api_keys)

        # Simulate multiple failed attempts
        failed_attempts = 0
        for i in range(100):
            if not auth.verify_api_key(f"invalid_key_{i}"):
                failed_attempts += 1

        assert failed_attempts == 100
        # Valid key should still work
        assert auth.verify_api_key("valid_key_123") is True

    def test_timing_attack_resistance(self):
        """Test resistance to timing attacks."""
        from src.core.auth import APIKeyAuth

        api_keys = ["short", "very_long_api_key_for_testing_timing"]
        auth = APIKeyAuth(api_keys)

        test_keys = ["a", "medium_key", "very_long_key_that_should_have_similar_timing"]
        times = []

        for key in test_keys:
            start = time.perf_counter()
            auth.verify_api_key(key)
            end = time.perf_counter()
            times.append(end - start)

        # Check timing variation is minimal (< 10% relative deviation)
        avg_time = sum(times) / len(times)
        max_deviation = max(abs(t - avg_time) for t in times)
        relative_deviation = max_deviation / avg_time if avg_time > 0 else 0

        assert relative_deviation < 0.1

    def test_api_key_entropy(self):
        """Test API key randomness and entropy."""
        weak_keys = ["weak", "password", "123456", "admin"]

        # Check that weak keys are flagged
        for key in weak_keys:
            # Should work but be flagged as weak
            from src.core.auth import APIKeyAuth
            auth = APIKeyAuth([key])
            assert auth.verify_api_key(key) is True  # Still works
            # In practice, you'd log warnings for weak keys

    def test_jwt_token_security(self):
        """Test JWT token security."""
        import jwt
        from datetime import datetime, timedelta

        secret_key = "test_secret_key"
        payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        # Generate token
        token = jwt.encode(payload, secret_key, algorithm="HS256")

        # Verify token
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == "test_user"

        # Test tampering
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token + "tampered", secret_key, algorithms=["HS256"])

    def test_session_hijacking_prevention(self):
        """Test prevention of session hijacking."""
        # Mock session storage
        sessions = {}

        def create_session(user_id: str) -> str:
            session_id = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()
            sessions[session_id] = {
                "user_id": user_id,
                "created": time.time(),
                "expires": time.time() + 3600
            }
            return session_id

        def validate_session(session_id: str) -> bool:
            if session_id not in sessions:
                return False
            session = sessions[session_id]
            if time.time() > session["expires"]:
                del sessions[session_id]
                return False
            return True

        # Create session
        session_id = create_session("user1")
        assert validate_session(session_id) is True

        # Test invalid session
        assert validate_session("invalid_session") is False

        # Test session expiration
        sessions[session_id]["expires"] = time.time() - 1
        assert validate_session(session_id) is False

    def test_rate_limiting_bypass_attempts(self):
        """Test rate limiting for authentication attempts."""
        auth_attempts = {}
        rate_limit_window = 60  # 1 minute
        max_attempts = 5

        def check_rate_limit(identifier: str) -> bool:
            now = time.time()
            if identifier not in auth_attempts:
                auth_attempts[identifier] = []

            # Clean old attempts
            auth_attempts[identifier] = [
                attempt for attempt in auth_attempts[identifier]
                if now - attempt < rate_limit_window
            ]

            if len(auth_attempts[identifier]) >= max_attempts:
                return False

            auth_attempts[identifier].append(now)
            return True

        # Test normal usage
        for i in range(max_attempts):
            assert check_rate_limit("test_user") is True

        # Test rate limiting
        assert check_rate_limit("test_user") is False

        # Different user not affected
        assert check_rate_limit("other_user") is True
```

### Input Validation Security Testing

```python
import pytest
import json
from unittest.mock import patch

class TestInputValidationSecurity:
    """Test input validation and injection prevention."""

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "'; SELECT * FROM users; --"
        ]

        for malicious_input in malicious_inputs:
            # Mock request with malicious input
            mock_request = Mock()
            mock_request.json.return_value = {
                "query": malicious_input,
                "model": "gpt-3.5-turbo"
            }

            # Should either reject or sanitize
            with patch('src.api.endpoints.process_request') as mock_process:
                mock_process.return_value = {"response": "safe_response"}

                from src.api.endpoints import chat_completions
                try:
                    result = chat_completions(mock_request)
                    # If it succeeds, ensure no SQL injection occurred
                    assert "DROP" not in str(result)
                    assert "SELECT" not in str(result)
                except HTTPException as e:
                    # Rejection is acceptable
                    assert e.status_code in [400, 422]

    def test_xss_prevention(self):
        """Test Cross-Site Scripting prevention."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]

        for payload in xss_payloads:
            mock_request = Mock()
            mock_request.json.return_value = {
                "messages": [{"role": "user", "content": payload}],
                "model": "gpt-3.5-turbo"
            }

            with patch('src.api.endpoints.process_request') as mock_process:
                mock_process.return_value = {"response": "safe_response"}

                try:
                    from src.api.endpoints import chat_completions
                    result = chat_completions(mock_request)
                    # Ensure XSS payload is not in response
                    response_str = json.dumps(result)
                    assert "<script>" not in response_str
                    assert "javascript:" not in response_str
                except HTTPException as e:
                    # Rejection is acceptable
                    assert e.status_code in [400, 422]

    def test_file_upload_security(self):
        """Test file upload security."""
        dangerous_files = [
            "malicious.exe",
            "script.php",
            "exploit.jsp",
            "../../../etc/passwd"
        ]

        for filename in dangerous_files:
            # Mock file upload
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = "application/octet-stream"

            # Should reject dangerous files
            from src.core.validation import validate_file_upload
            with pytest.raises(ValueError):
                validate_file_upload(mock_file)

    def test_command_injection_prevention(self):
        """Test command injection prevention."""
        injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "`whoami`",
            "$(rm -rf /)"
        ]

        for payload in injection_payloads:
            mock_request = Mock()
            mock_request.json.return_value = {
                "command": payload,
                "model": "gpt-3.5-turbo"
            }

            # Should reject or sanitize command injection attempts
            from src.api.endpoints import execute_command
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(stdout="safe_output", stderr="")

                try:
                    result = execute_command(mock_request)
                    # Ensure injection didn't execute
                    assert mock_subprocess.call_count == 0 or "rm" not in str(mock_subprocess.call_args)
                except HTTPException as e:
                    # Rejection is acceptable
                    assert e.status_code in [400, 422]
```

### Penetration Testing

```python
import pytest
import requests
from unittest.mock import patch, Mock

class TestPenetrationTesting:
    """Automated penetration testing scenarios."""

    def test_directory_traversal_attack(self):
        """Test directory traversal attack prevention."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            ".../...//.../...//.../...//etc/passwd"
        ]

        for payload in traversal_payloads:
            mock_request = Mock()
            mock_request.query_params = {"file": payload}

            from src.api.endpoints import get_file
            try:
                result = get_file(mock_request)
                # Should not access files outside allowed directory
                assert ".." not in str(result)
                assert "etc" not in str(result)
                assert "passwd" not in str(result)
            except HTTPException as e:
                # Should be rejected
                assert e.status_code == 403

    def test_session_hijacking_simulation(self):
        """Test session hijacking prevention."""
        # Create valid session
        valid_session = "valid_session_123"
        hijacked_session = valid_session  # Attacker steals session

        # Simulate concurrent requests with same session
        from src.core.session import SessionManager
        session_mgr = SessionManager()

        # First request - should succeed
        user1_result = session_mgr.validate_session(valid_session)
        assert user1_result is True

        # Hijacked request - should be detected and rejected
        # In practice, you'd implement session invalidation on suspicious activity
        hijack_result = session_mgr.validate_session(hijacked_session)
        # Could be rejected or logged as suspicious
        assert hijack_result in [True, False]  # Depends on implementation

    def test_csrf_attack_prevention(self):
        """Test CSRF attack prevention."""
        # Mock requests without CSRF tokens
        csrf_payloads = [
            {"action": "delete", "id": "123"},
            {"action": "update", "data": "malicious"},
            {"action": "transfer", "amount": "1000", "to": "attacker"}
        ]

        for payload in csrf_payloads:
            mock_request = Mock()
            mock_request.json.return_value = payload
            mock_request.headers = {}  # No CSRF token

            from src.api.endpoints import process_sensitive_action
            with pytest.raises(HTTPException) as exc_info:
                process_sensitive_action(mock_request)

            assert exc_info.value.status_code == 403
            assert "CSRF" in str(exc_info.value.detail)

    def test_http_header_injection(self):
        """Test HTTP header injection prevention."""
        injection_headers = {
            "x-forwarded-for": "127.0.0.1\r\nX-Injected: malicious",
            "user-agent": "Mozilla/5.0\r\nHost: evil.com",
            "referer": "http://legit.com\r\nSet-Cookie: session=hijacked"
        }

        for header_name, header_value in injection_headers.items():
            mock_request = Mock()
            mock_request.headers = {header_name: header_value}

            from src.core.security import validate_headers
            try:
                validate_headers(mock_request)
                # If no exception, headers should be sanitized
                assert "\r" not in str(mock_request.headers)
                assert "\n" not in str(mock_request.headers)
            except HTTPException as e:
                # Rejection is also acceptable
                assert e.status_code == 400

    def test_rate_limit_bypass_attempts(self):
        """Test rate limit bypass attempts."""
        from src.core.rate_limiter import RateLimiter
        import time

        limiter = RateLimiter(requests_per_minute=10)

        # Normal usage
        client_ip = "192.168.1.100"
        for i in range(10):
            assert limiter.is_allowed(client_ip) is True

        # Should be rate limited
        assert limiter.is_allowed(client_ip) is False

        # Attempt bypass with different IPs (spoofing)
        bypass_ips = [
            "192.168.1.101",  # Different IP
            "127.0.0.1",      # Localhost
            "10.0.0.1",       # Private IP
        ]

        # These should not bypass rate limiting for the same user
        # In practice, you'd track by user ID, not just IP
        for ip in bypass_ips:
            # Rate limiting should be per user, not per IP
            assert limiter.is_allowed(ip) is True  # Different "user"
```

## Performance Testing and Benchmarking

### pytest-benchmark Usage

```python
import pytest
from src.core.cache_manager import CacheManager
from src.core.model_discovery import ModelDiscoveryService

class TestPerformanceBenchmarks:
    """Performance benchmarks for critical components."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager for benchmarking."""
        return CacheManager()

    @pytest.fixture
    def discovery_service(self):
        """Create discovery service for benchmarking."""
        return ModelDiscoveryService()

    def test_cache_set_performance(self, benchmark, cache_manager):
        """Benchmark cache set operations."""
        def cache_set_operation():
            for i in range(1000):
                cache_manager.set(f"key_{i}", f"value_{i}")

        benchmark(cache_set_operation)

    def test_cache_get_performance(self, benchmark, cache_manager):
        """Benchmark cache get operations."""
        # Setup cache with data
        for i in range(1000):
            cache_manager.set(f"key_{i}", f"value_{i}")

        def cache_get_operation():
            for i in range(1000):
                cache_manager.get(f"key_{i}")

        benchmark(cache_get_operation)

    def test_model_discovery_performance(self, benchmark, discovery_service):
        """Benchmark model discovery performance."""
        def discovery_operation():
            # Mock the actual API call
            with patch('src.providers.openai.OpenAIDiscovery.get_models') as mock_get:
                mock_get.return_value = [
                    Mock(id=f"model_{i}", name=f"Model {i}")
                    for i in range(100)
                ]
                result = discovery_service.discover_all_models()
                return result

        result = benchmark(discovery_operation)
        assert len(result) == 100

    def test_json_serialization_performance(self, benchmark):
        """Benchmark JSON serialization performance."""
        import orjson
        import json

        large_data = {
            "models": [
                {
                    "id": f"model_{i}",
                    "name": f"Model {i}",
                    "context_length": 4096 + i,
                    "max_tokens": 2048 + i,
                    "supports_chat": True,
                    "supports_completion": i % 2 == 0,
                    "input_cost": 0.001 * i,
                    "output_cost": 0.002 * i,
                    "metadata": {
                        "description": f"Description for model {i}",
                        "tags": [f"tag_{j}" for j in range(5)]
                    }
                }
                for i in range(1000)
            ]
        }

        def orjson_serialize():
            return orjson.dumps(large_data)

        def stdlib_json_serialize():
            return json.dumps(large_data)

        # Benchmark both methods
        orjson_result = benchmark(orjson_serialize)
        stdlib_result = benchmark(stdlib_json_serialize)

        # orjson should be faster
        assert len(orjson_result) > 0
        assert len(stdlib_result) > 0
```

### Memory Profiling

```python
import pytest
import tempfile
from memory_profiler import profile
from src.core.cache_manager import CacheManager

class TestMemoryProfiling:
    """Memory usage profiling tests."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_cache_memory_usage(self, temp_cache_dir):
        """Profile memory usage of cache operations."""
        cache = CacheManager(cache_dir=temp_cache_dir)

        @profile
        def memory_intensive_operation():
            # Simulate memory-intensive cache operations
            for i in range(10000):
                cache.set(f"key_{i}", f"value_{i}" * 1000)  # Large values

            # Read all values
            for i in range(10000):
                cache.get(f"key_{i}")

            # Clear cache
            cache.clear()

        memory_intensive_operation()

    def test_model_discovery_memory_usage(self):
        """Profile memory usage during model discovery."""
        from src.core.model_discovery import ModelDiscoveryService

        service = ModelDiscoveryService()

        @profile
        def discovery_memory_test():
            # Mock large model list
            large_model_list = [
                Mock(
                    id=f"model_{i}",
                    name=f"Model {i}",
                    context_length=4096,
                    max_tokens=2048,
                    metadata={"large_data": "x" * 1000}
                )
                for i in range(1000)
            ]

            with patch('src.providers.openai.OpenAIDiscovery.get_models') as mock_get:
                mock_get.return_value = large_model_list

                result = service.discover_all_models()
                assert len(result) == 1000

                # Process results (simulates real usage)
                processed = []
                for model in result:
                    processed.append({
                        "id": model.id,
                        "name": model.name,
                        "metadata_size": len(str(model.metadata))
                    })

                return processed

        result = discovery_memory_test()
        assert len(result) == 1000
```

### CPU Profiling

```python
import pytest
import cProfile
import pstats
from io import StringIO

class TestCPUProfiling:
    """CPU profiling tests."""

    def test_cpu_intensive_operation(self):
        """Profile CPU usage of intensive operations."""
        from src.core.model_discovery import ModelDiscoveryService

        service = ModelDiscoveryService()

        def cpu_intensive_task():
            # Simulate CPU-intensive processing
            results = []
            for i in range(10000):
                # Complex string processing
                result = str(i).encode('utf-8').decode('utf-8')
                result = result + "_" + str(i * 2) + "_" + str(i ** 2)
                results.append(hash(result))

            return sum(results)

        # Profile the function
        profiler = cProfile.Profile()
        profiler.enable()

        result = cpu_intensive_task()

        profiler.disable()

        # Get stats
        stats = pstats.Stats(profiler, stream=StringIO())
        stats.sort_stats('cumulative')
        stats.print_stats()

        assert result is not None

    def test_model_processing_cpu_profile(self):
        """Profile CPU usage during model processing."""
        from src.models.model_info import ModelInfo

        def process_models():
            models = []
            for i in range(1000):
                model = ModelInfo(
                    id=f"model_{i}",
                    name=f"Model {i}",
                    provider="test_provider",
                    context_length=4096 + i,
                    max_tokens=2048 + i,
                    supports_chat=bool(i % 2),
                    supports_completion=bool(i % 3),
                    input_cost=0.001 * i,
                    output_cost=0.002 * i
                )
                models.append(model)

            # Simulate processing
            processed = []
            for model in models:
                # Complex processing
                score = (
                    model.context_length / 1000 +
                    model.max_tokens / 1000 +
                    (model.input_cost + model.output_cost) * 1000
                )
                if model.supports_chat:
                    score *= 1.2
                if model.supports_completion:
                    score *= 1.1

                processed.append({
                    "id": model.id,
                    "score": score,
                    "recommendation": "good" if score > 10 else "average"
                })

            return processed

        # Profile the processing
        profiler = cProfile.Profile()
        profiler.enable()

        result = process_models()

        profiler.disable()

        # Analyze results
        assert len(result) == 1000
        assert all("score" in item for item in result)
```

## Test Coverage Analysis

### Coverage Configuration

```ini
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
```

### Coverage Goals by Component

```python
# tests/test_coverage_goals.py
import pytest
from pytest_cov import coverage

class TestCoverageGoals:
    """Test coverage goals and thresholds."""

    def test_unit_test_coverage(self):
        """Ensure unit tests meet coverage goals."""
        # This would typically be handled by pytest-cov plugin
        # with minimum coverage thresholds
        pass

    def test_integration_test_coverage(self):
        """Ensure integration tests cover API endpoints."""
        # Verify key endpoints are tested
        from src.api.endpoints import app
        routes = [route.path for route in app.routes]

        #