"""
Configuração expandida do mutmut para testes de mutação em múltiplos módulos
"""
import os

# Módulos principais a serem testados
core_modules = [
    "src/core/config.py",
    "src/core/auth.py", 
    "src/core/cache_manager.py",
    "src/core/circuit_breaker.py",
    "src/core/http_client.py",
    "src/core/rate_limiter.py",
    "src/core/retry_strategies.py",
    "src/core/model_config.py",
    "src/core/model_discovery.py",
    "src/core/telemetry.py",
    "src/core/logging.py",
    "src/core/metrics.py",
]

# Módulos de API
api_modules = [
    "src/api/endpoints.py",
    "src/api/model_endpoints.py",
    "src/api/router.py",
]

# Módulos de serviços
service_modules = [
    "src/services/model_config_service.py",
    "src/services/provider_loader.py",
]

# Módulos de utilitários
utils_modules = [
    "src/utils/context_condenser.py",
    "src/utils/cache_utils.py",
    "src/utils/validation.py",
]

# Módulos de contexto e health
context_modules = [
    "context_service/app.py",
    "context_service/utils/context_condenser_impl.py",
    "health_worker/app.py",
]

# Módulos principais do projeto
main_modules = [
    "main.py",
    "main_dynamic.py",
    "production_config.py",
    "web_ui.py",
]

# Todos os módulos a serem testados
all_modules = (
    core_modules + 
    api_modules + 
    service_modules + 
    utils_modules + 
    context_modules + 
    main_modules
)

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
    "src/components/",  # React components
    "src/providers/",   # Provider implementations (muito complexos)
    "src/models/",       # Model definitions
    "src/scripts/",      # Scripts utilitários
    "monitoring/",       # Configurações de monitoramento
    "docs/",
    "examples/",
    "static/",
    "templates/",
]

# Comando para executar os testes
def pytest_command():
    return "python3 -m pytest tests_mutmut/ -v --tb=short"

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
        'paths_to_mutate': all_modules,
        'exclude_paths': exclude_paths,
        'pytest_command': pytest_command(),
        'pre_mutation': pre_mutation,
        'post_mutation': post_mutation,
    }