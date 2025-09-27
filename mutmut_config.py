"""
Configuração do mutmut para testes de mutação
"""
import os

# Diretórios a serem testados (sem src/)
paths_to_mutate = [
    "main.py",
    "main_dynamic.py", 
    "production_config.py",
    "web_ui.py",
]

# Diretórios a serem ignorados
exclude_paths = [
    "tests/",
    "tests_mutmut/",
    "test_*.py",
    "build/",
    "dist/",
    "node_modules/",
    "venv/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git/",
    ".pytest_cache/",
    "*.egg-info/",
    "src/",  # Excluir src/ completamente
    "context_service/",
    "health_worker/",
    "monitoring/",
]

# Comando para executar os testes
def pytest_command():
    return "python3 -m pytest tests_mutmut/test_simple.py -v"

# Configurações adicionais
def pre_mutation(context):
    """Executado antes de cada mutação"""
    pass

def post_mutation(context):
    """Executado após cada mutação"""
    pass

# Configurações do mutmut
def init():
    """Inicialização do mutmut"""
    return {
        'paths_to_mutate': paths_to_mutate,
        'exclude_paths': exclude_paths,
        'pytest_command': pytest_command(),
        'pre_mutation': pre_mutation,
        'post_mutation': post_mutation,
    }