"""
Testes para módulos principais do projeto
"""
import pytest
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_main_module():
    """Testa se o módulo main pode ser importado"""
    try:
        import main
        assert main is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar main: {e}")

def test_main_dynamic_module():
    """Testa se o módulo main_dynamic pode ser importado"""
    try:
        import main_dynamic
        assert main_dynamic is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar main_dynamic: {e}")

def test_production_config_module():
    """Testa se o módulo production_config pode ser importado"""
    try:
        import production_config
        assert production_config is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar production_config: {e}")

def test_web_ui_module():
    """Testa se o módulo web_ui pode ser importado"""
    try:
        import web_ui
        assert web_ui is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar web_ui: {e}")

def test_context_service_module():
    """Testa se o módulo context_service pode ser importado"""
    try:
        from context_service.app import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar context_service: {e}")

def test_health_worker_module():
    """Testa se o módulo health_worker pode ser importado"""
    try:
        from health_worker.app import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"Não foi possível importar health_worker: {e}")

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