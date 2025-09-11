# 📋 Referência de Arquivos - LLM Proxy API

## Sumário

- [Arquivos Principais](#arquivos-principais)
- [Configuração](#configuracao)
- [Código Fonte (src/)](#codigo-fonte-src)
- [Provedores](#provedores)
- [Serviços e Utilitários](#servicos-e-utilitarios)
- [Testes](#testes)
- [Documentação](#documentacao)
- [Build e Deployment](#build-e-deployment)
- [Outros Arquivos](#outros-arquivos)

---

## 🎯 Arquivos Principais

### `main.py`

**Propósito**: Ponto de entrada principal da aplicação
**Localização**: `/`
**Tipo**: Python Script

**Conteúdo**:

- Inicialização do servidor FastAPI
- Configuração de middlewares
- Registro de rotas
- Inicialização de componentes core

**Dependências**:

- `src.core.config`
- `src.core.provider_factory`
- `src.api.routes`

### `main_dynamic.py`

**Propósito**: Versão dinâmica com hot-reload para desenvolvimento
**Localização**: `/`
**Tipo**: Python Script

**Características**:

- Suporte a hot-reload durante desenvolvimento
- Recarregamento automático de mudanças
- Logging aprimorado para debug
- Configuração otimizada para dev

### `web_ui.py`

**Propósito**: Interface web para configuração e administração
**Localização**: `/`
**Tipo**: Flask Application

**Funcionalidades**:

- Interface web para configuração
- Gerenciamento de provedores
- Visualização de métricas
- Configuração de ambiente

---

## ⚙️ Configuração

### `config.yaml`

**Propósito**: Configuração central do sistema
**Localização**: `/`
**Tipo**: YAML Configuration

**Seções**:

```yaml

# Configurações globais
app_name: "LLM Proxy API"
debug: false
host: "127.0.0.1"
port: 8000

# Autenticação e segurança
api_keys: [...]
cors_origins: [...]
rate_limit_rpm: 1000

# Provedores
providers:
  - name: "openai_default"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    models: ["gpt-4", "gpt-3.5-turbo"]
    enabled: true
    priority: 1

# Monitoramento
health_check_interval: 60
log_level: "INFO"
```

### `.env`

**Propósito**: Variáveis de ambiente sensíveis
**Localização**: `/`
**Tipo**: Environment Variables

**Conteúdo**:

```bash

# API Keys (sensíveis)
PROXY_API_OPENAI_API_KEY=sk-...
PROXY_API_ANTHROPIC_API_KEY=sk-ant-...

# Configurações do servidor
PROXY_API_PORT=8000
PROXY_API_HOST=127.0.0.1

# Logging
LOG_LEVEL=INFO

# Health monitoring
HEALTH_CHECK_INTERVAL=60
HEALTH_CHECK_CACHE_TTL=30
```

### `health_worker_providers.json`

**Propósito**: Configuração específica para health checks
**Localização**: `/`
**Tipo**: JSON Configuration

**Estrutura**:

```json
{
  "providers": [
    {
      "name": "openai",
      "base_url": "https://api.openai.com",
      "models": ["gpt-3.5-turbo", "gpt-4"]
    }
  ]
}
```

### `build_config.yaml`

**Propósito**: Configuração para build de executáveis
**Localização**: `/`
**Tipo**: YAML Configuration

**Uso**: Configuração do PyInstaller para criar executáveis standalone

---

## 📁 Código Fonte (src/)

### `src/__init__.py`

**Propósito**: Inicialização do pacote principal
**Localização**: `src/`
**Tipo**: Python Package

### `src/api/`

**Propósito**: Endpoints e rotas da API
**Localização**: `src/api/`
**Tipo**: Python Package

**Arquivos principais**:

- `__init__.py`: Inicialização do pacote API
- `routes.py`: Definição de todas as rotas FastAPI
- `middleware.py`: Middlewares customizados
- `dependencies.py`: Dependências injetáveis

### `src/core/`

**Propósito**: Componentes core do sistema
**Localização**: `src/core/`
**Tipo**: Python Package

#### `src/core/config.py`

**Propósito**: Gerenciamento centralizado de configuração
**Funcionalidades**:

- Carregamento de config.yaml
- Validação de configuração
- Hot-reload de configuração
- Cache de configuração

#### `src/core/provider_factory.py`

**Propósito**: Factory para criação e gerenciamento de provedores
**Funcionalidades**:

- Registro de provedores
- Instanciação lazy
- Health monitoring
- Cache de instâncias

#### `src/core/request_router.py`

**Propósito**: Roteamento inteligente de requests
**Funcionalidades**:

- Seleção de provedor baseada em saúde
- Failover automático
- Load balancing
- Métricas de roteamento

#### `src/core/unified_config.py`

**Propósito**: Configurações unificadas para provedores
**Funcionalidades**:

- Pydantic models para configuração
- Validação de tipos
- Serialização/Deserialização

### `src/models/`

**Propósito**: Modelos de dados e tipos
**Localização**: `src/models/`
**Tipo**: Python Package

**Conteúdo**:

- Modelos Pydantic para requests/responses
- Tipos customizados
- Validações de dados

### `src/utils/`

**Propósito**: Utilitários gerais
**Localização**: `src/utils/`
**Tipo**: Python Package

**Arquivos**:

- `cache.py`: Utilitários de cache
- `retry.py`: Lógica de retry com backoff
- `validation.py`: Funções de validação
- `formatting.py`: Utilitários de formatação

---

## 🔌 Provedores

### Estrutura Geral

Cada provedor segue o padrão:

```
src/providers/{provider_name}.py
```

### `src/providers/base.py`

**Propósito**: Classe base abstrata para todos os provedores
**Localização**: `src/providers/`
**Tipo**: Python Class

**Métodos abstratos**:

- `_perform_health_check()`: Health check específico
- `create_completion()`: Chat completions
- `create_text_completion()`: Text completions
- `create_embeddings()`: Geração de embeddings

### Provedores Implementados

#### `src/providers/openai.py`

**Provedor**: OpenAI
**Características**:

- Suporte a GPT-4, GPT-3.5
- Streaming SSE
- Embeddings
- Rate limiting handling

#### `src/providers/anthropic.py`

**Provedor**: Anthropic
**Características**:

- Claude 3 models
- Messages API
- Streaming
- Context management

#### `src/providers/grok.py`

**Provedor**: xAI Grok
**Características**:

- Grok models
- Prompt-based API
- Text completion focus

#### `src/providers/perplexity.py`

**Provedor**: Perplexity AI
**Características**:

- Search-focused
- Citations support
- Query-based API

#### `src/providers/blackbox.py`

**Provedor**: Blackbox AI
**Características**:

- Multi-modal support
- Image generation
- Chat completions

#### `src/providers/openrouter.py`

**Provedor**: OpenRouter
**Características**:

- Model aggregator
- Multiple providers
- Unified interface

#### `src/providers/cohere.py`

**Provedor**: Cohere
**Características**:

- Text generation
- Embeddings
- Command models

---

## 🛠️ Serviços e Utilitários

### `src/services/`

**Propósito**: Serviços utilitários do sistema
**Localização**: `src/services/`
**Tipo**: Python Package

#### `src/services/logging.py`

**Propósito**: Sistema de logging estruturado
**Funcionalidades**:

- Logging com contexto
- JSON formatting
- Request ID tracking
- Log levels configuráveis

#### `src/services/metrics.py`

**Propósito**: Coleta de métricas Prometheus
**Funcionalidades**:

- Counters para requests/errors
- Histograms para latência
- Gauges para estados
- Health check metrics

#### `src/services/health_monitor.py`

**Propósito**: Monitoramento de saúde dos provedores
**Funcionalidades**:

- Health checks periódicos
- Status tracking
- Circuit breaker
- Cache de resultados

### `src/scripts/`

**Propósito**: Scripts utilitários
**Localização**: `src/scripts/`
**Tipo**: Python Package

#### `src/scripts/export_dataset.py`

**Propósito**: Exportação de dados de conversas
**Funcionalidades**:

- Extração de logs
- Formatação JSONL
- Filtros por data/modelo
- Progress tracking

#### `src/scripts/validate_env.py`

**Propósito**: Validação de variáveis de ambiente
**Funcionalidades**:

- Verificação de API keys
- Validação de configurações
- Relatórios de problemas

---

## 🧪 Testes

### `tests/`

**Propósito**: Testes automatizados
**Localização**: `tests/`
**Tipo**: Python Package

#### `tests/test_providers.py`

**Propósito**: Testes de provedores
**Cobertura**:

- Inicialização de provedores
- Health checks
- Request handling
- Error handling

#### `tests/test_endpoints.py`

**Propósito**: Testes de endpoints da API
**Cobertura**:

- Chat completions
- Streaming
- Error responses
- Authentication

#### `tests/test_config.py`

**Propósito**: Testes de configuração
**Cobertura**:

- Carregamento de config
- Validação
- Hot-reload

#### `tests/test_context_condensation.py`

**Propósito**: Testes de condensação de contexto
**Cobertura**:

- Context length handling
- Summary generation
- Fallback mechanisms

### Configuração de Testes

#### `pytest.ini`

**Propósito**: Configuração do pytest
**Localização**: `/`
**Conteúdo**:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=src --cov-report=html
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

---

## 📚 Documentação

### `docs/`

**Propósito**: Documentação completa do projeto
**Localização**: `docs/`
**Tipo**: Markdown Files

#### `docs/README.md`

**Propósito**: Documentação principal
**Conteúdo**:

- Visão geral
- Instalação
- Uso básico
- Configuração

#### `docs/export_dataset.md`

**Propósito**: Documentação da funcionalidade de export
**Conteúdo**:

- Guia completo de exportação
- Exemplos de uso
- Configurações avançadas
- Troubleshooting

#### `docs/PROJECT_DOCUMENTATION.md`

**Propósito**: Documentação técnica completa
**Conteúdo**:

- Arquitetura detalhada
- APIs e endpoints
- Monitoramento
- Desenvolvimento
- Troubleshooting

#### `docs/FILE_REFERENCE.md`

**Propósito**: Referência de todos os arquivos
**Conteúdo**:

- Descrição de cada arquivo
- Propósito e localização
- Dependências
- Uso típico

---

## 🏗️ Build e Deployment

### `build_*.py`

**Propósito**: Scripts de build para diferentes plataformas
**Localização**: `/`
**Tipo**: Python Scripts

#### `build_windows.py`

**Propósito**: Build para Windows
**Funcionalidades**:

- PyInstaller para Windows
- Configuração específica do Windows
- Otimizações de performance

#### `build_linux.py`

**Propósito**: Build para Linux
**Funcionalidades**:

- PyInstaller para Linux
- Configuração de permissões
- Otimizações para distribuição

#### `build_macos.py`

**Propósito**: Build para macOS
**Funcionalidades**:

- PyInstaller para macOS
- Bundle do macOS
- Code signing

### `Dockerfile`

**Propósito**: Containerização da aplicação
**Localização**: `/`
**Tipo**: Dockerfile

**Características**:

- Multi-stage build
- Alpine Linux base
- Otimizações de tamanho
- Security hardening

### `docker-compose.yml`

**Propósito**: Orquestração de containers
**Localização**: `/`
**Tipo**: Docker Compose

**Serviços**:

- API principal
- Health worker
- Web UI
- Monitoring stack

### `systemd-services/`

**Propósito**: Serviços systemd para deployment
**Localização**: `systemd-services/`
**Tipo**: Systemd Unit Files

**Arquivos**:

- `llm-proxy-api.service`: Serviço principal
- `health-worker.service`: Serviço de health monitoring
- `web-ui.service`: Interface web

---

## 📦 Outros Arquivos

### `requirements.txt`

**Propósito**: Dependências Python
**Localização**: `/`
**Tipo**: Requirements File

**Conteúdo**:

```
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.2
pydantic==2.5.0
prometheus-client==0.19.0
apscheduler==3.10.4
python-multipart==0.0.6
jinja2==3.1.2
python-dotenv==1.0.0
pyyaml==6.0.1
```

### `pyrightconfig.json`

**Propósito**: Configuração do Pyright (type checking)
**Localização**: `/`
**Tipo**: JSON Configuration

### `.gitignore`

**Propósito**: Arquivos ignorados pelo Git
**Localização**: `/`
**Tipo**: Git Ignore

**Conteúdo**:

```
# Environment
.env
venv/
__pycache__/

# Logs
logs/
*.log

# Builds
dist/
build/
*.spec

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### `LICENSE`

**Propósito**: Licença do projeto
**Localização**: `/`
**Tipo**: Text File

**Licença**: MIT License

### `README.md`

**Propósito**: Documentação principal do repositório
**Localização**: `/`
**Tipo**: Markdown

---

## 🔍 Arquivos de Log e Dados

### `logs/`

**Propósito**: Logs do sistema
**Localização**: `logs/`
**Tipo**: Directory

**Arquivos**:

- `proxy_api.log`: Logs principais da aplicação
- `health_worker.log`: Logs do health monitoring
- `web_ui.log`: Logs da interface web

### `exports/`

**Propósito**: Dados exportados
**Localização**: `exports/`
**Tipo**: Directory

**Conteúdo**:

- Datasets JSONL exportados
- Arquivos de backup
- Relatórios gerados

### `static/`

**Propósito**: Assets estáticos
**Localização**: `static/`
**Tipo**: Directory

**Conteúdo**:

- CSS, JavaScript
- Imagens
- Fonts

### `templates/`

**Propósito**: Templates HTML
**Localização**: `templates/`
**Tipo**: Directory

**Conteúdo**:

- Templates Flask/Jinja2
- Páginas HTML
- Layouts base

---

## 📊 Arquivos de Monitoramento

### Métricas e Health Checks

#### `health_worker/`

**Propósito**: Serviço dedicado de health monitoring
**Localização**: `health_worker/`
**Tipo**: Python Application

**Arquivos**:

- `app.py`: Aplicação FastAPI para health checks
- `providers.json`: Configuração de provedores monitorados

#### Prometheus Integration

- Métricas expostas em `/metrics`
- Health checks em `/health`
- Status de provedores em `/status`

---

## 🚀 Arquivos de Deployment

### `venv_test/`

**Propósito**: Ambiente virtual de teste
**Localização**: `venv_test/`
**Tipo**: Python Virtual Environment

### `p/`

**Propósito**: Projetos relacionados
**Localização**: `p/`
**Tipo**: Directory

**Conteúdo**:

- Projetos complementares
- Utilitários relacionados
- Experimentos

---

## 📝 Resumo de Arquivos por Categoria

| Categoria | Quantidade | Localização Principal |
|-----------|------------|----------------------|
| **Core Application** | 3 | `/` |
| **Configuration** | 4 | `/` |
| **Source Code** | ~20 | `src/` |
| **Providers** | 8 | `src/providers/` |
| **Tests** | 5+ | `tests/` |
| **Documentation** | 4 | `docs/` |
| **Build Scripts** | 4 | `/` |
| **Deployment** | 3 | `systemd-services/` |
| **Logs/Data** | - | `logs/`, `exports/` |
| **Assets** | - | `static/`, `templates/` |

---

*Esta referência foi atualizada em Janeiro 2024*
*Para mais detalhes sobre qualquer arquivo, consulte a documentação específica*
