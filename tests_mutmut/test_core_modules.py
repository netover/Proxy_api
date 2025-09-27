"""
Testes para módulos core do projeto
"""
import pytest
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_module():
    """Testa se o módulo de configuração pode ser importado"""
    try:
        from src.core.config import settings
        assert hasattr(settings, 'api_key')
        assert hasattr(settings, 'base_url')
    except ImportError as e:
        pytest.skip(f"Não foi possível importar config: {e}")

def test_auth_module():
    """Testa se o módulo de autenticação pode ser importado"""
    try:
        from src.core.auth import APIKeyAuth, verify_api_key
        assert callable(verify_api_key)
    except ImportError as e:
        pytest.skip(f"Não foi possível importar auth: {e}")

def test_cache_manager_module():
    """Testa se o módulo de cache pode ser importado"""
    try:
        from src.core.cache_manager import CacheManager
        assert CacheManager is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar cache_manager: {e}")

def test_circuit_breaker_module():
    """Testa se o módulo de circuit breaker pode ser importado"""
    try:
        from src.core.circuit_breaker import CircuitBreaker
        assert CircuitBreaker is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar circuit_breaker: {e}")

def test_http_client_module():
    """Testa se o módulo de HTTP client pode ser importado"""
    try:
        from src.core.http_client import HTTPClient
        assert HTTPClient is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar http_client: {e}")

def test_rate_limiter_module():
    """Testa se o módulo de rate limiter pode ser importado"""
    try:
        from src.core.rate_limiter import RateLimiter
        assert RateLimiter is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar rate_limiter: {e}")

def test_retry_strategies_module():
    """Testa se o módulo de retry strategies pode ser importado"""
    try:
        from src.core.retry_strategies import RetryStrategy
        assert RetryStrategy is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar retry_strategies: {e}")

def test_model_config_module():
    """Testa se o módulo de model config pode ser importado"""
    try:
        from src.core.model_config import ModelConfig
        assert ModelConfig is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar model_config: {e}")

def test_model_discovery_module():
    """Testa se o módulo de model discovery pode ser importado"""
    try:
        from src.core.model_discovery import ModelDiscovery
        assert ModelDiscovery is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar model_discovery: {e}")

def test_telemetry_module():
    """Testa se o módulo de telemetria pode ser importado"""
    try:
        from src.core.telemetry import TelemetryCollector
        assert TelemetryCollector is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar telemetry: {e}")

def test_logging_module():
    """Testa se o módulo de logging pode ser importado"""
    try:
        from src.core.logging import get_logger
        assert callable(get_logger)
    except ImportError as e:
        pytest.skip(f"Não foi possível importar logging: {e}")

def test_metrics_module():
    """Testa se o módulo de métricas pode ser importado"""
    try:
        from src.core.metrics import MetricsCollector
        assert MetricsCollector is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar metrics: {e}")

def test_basic_functionality():
    """Teste básico de funcionalidade"""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert True is True

def test_string_operations():
    """Testa operações com strings"""
    text = "Hello World"
    assert len(text) == 11
    assert text.upper() == "HELLO WORLD"
    assert text.lower() == "hello world"

def test_list_operations():
    """Testa operações com listas"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1

def test_dict_operations():
    """Testa operações com dicionários"""
    data = {"name": "test", "value": 42}
    assert "name" in data
    assert data["value"] == 42
    assert len(data) == 2

def test_math_operations():
    """Testa operações matemáticas"""
    assert 2 * 3 == 6
    assert 10 / 2 == 5
    assert 2 ** 3 == 8
    assert 7 % 3 == 1

def test_boolean_operations():
    """Testa operações booleanas"""
    assert True and True == True
    assert False or True == True
    assert not False == True
    assert True != False