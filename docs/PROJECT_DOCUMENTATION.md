# 📚 Documentação Completa - LLM Proxy API

## Sumário

- [Visão Geral](#visao-geral)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Instalação e Configuração](#instalacao-e-configuracao)
- [Guia de Uso](#guia-de-uso)
- [APIs e Endpoints](#apis-e-endpoints)
- [Arquivos de Configuração](#arquivos-de-configuracao)
- [Monitoramento e Métricas](#monitoramento-e-metricas)
- [Estrutura de Diretórios](#estrutura-de-diretorios)
- [Desenvolvimento](#desenvolvimento)
- [Troubleshooting](#troubleshooting)
- [Referências](#referencias)

---

## 🎯 Visão Geral

O **LLM Proxy API** é uma solução enterprise-ready para proxy de APIs de Language Learning Models (LLMs), oferecendo:

### ✨ Principais Características

- **🔄 Roteamento Inteligente**: Failover automático entre provedores baseado em saúde e prioridade
- **🏥 Monitoramento de Saúde**: Sistema avançado de health checks com cache e circuit breakers
- **📊 Métricas Abrangentes**: Monitoramento completo com Prometheus e métricas customizadas
- **🔧 Configuração Flexível**: Suporte a múltiplas fontes de configuração (YAML, JSON, env vars)
- **🛡️ Segurança**: Autenticação, rate limiting e validação de entrada
- **📈 Escalabilidade**: Connection pooling, concorrência controlada e cache inteligente
- **🔍 Observabilidade**: Logging estruturado, tracing e dashboards
- **🚀 Auto-Discovery**: Descoberta automática de provedores via registry/K8s/Consul

### 🎯 Casos de Uso

- **Proxy Unificado**: Interface única para múltiplos provedores de LLM
- **Load Balancing**: Distribuição inteligente de carga entre provedores
- **Failover Automático**: Continuidade de serviço com fallback inteligente
- **Monitoramento Centralizado**: Dashboard único para todos os provedores
- **Custo Otimização**: Roteamento baseado em custo e performance

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Proxy API                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  FastAPI    │  │  Config     │  │  Metrics    │            │
│  │  Server     │  │  Manager    │  │  Collector  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Provider    │  │ Health      │  │ Circuit     │            │
│  │ Factory     │  │ Monitor     │  │ Breaker     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Request     │  │ Rate        │  │ Cache       │            │
│  │ Router      │  │ Limiter     │  │ Manager     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

1. **Recebimento**: Request chega via FastAPI
2. **Autenticação**: Validação de API key e rate limiting
3. **Roteamento**: Seleção do provedor baseado em saúde/prioridade
4. **Processamento**: Chamada para provedor com retry/circuit breaker
5. **Cache**: Armazenamento de resultados para otimização
6. **Monitoramento**: Coleta de métricas e logging
7. **Resposta**: Retorno formatado para cliente

### Provedores Suportados

| Provedor | Status | Endpoint | Características |
|----------|--------|----------|-----------------|
| OpenAI | ✅ | `/v1/chat/completions` | GPT-4, GPT-3.5, Embeddings |
| Anthropic | ✅ | `/v1/messages` | Claude 3, Opus, Sonnet |
| Grok | ✅ | `/v1/complete` | xAI Models |
| Perplexity | ✅ | `/v1/ask` | Search-focused |
| Blackbox | ✅ | `/v1/chat/completions` | Multi-modal |
| OpenRouter | ✅ | `/v1/chat/completions` | Aggregator |
| Cohere | ✅ | `/v1/generate` | Text Generation |
| Azure OpenAI | ✅ | `/openai/deployments/*` | Enterprise |

---

## 📦 Instalação e Configuração

### Pré-requisitos

- **Python**: 3.9+
- **Sistema Operacional**: Linux/Windows/macOS
- **Memória**: 2GB+ RAM
- **Espaço em Disco**: 500MB+

### Instalação Rápida

```bash

# 1. Clone o repositório
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api

# 2. Crie ambiente virtual
python -m venv venv

source venv/bin/activate  # Linux/macOS

# ou
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente

cp .env.example .env
# Edite .env com suas chaves de API

# 5. Execute o servidor
python main_dynamic.py
```

### Configuração Avançada

#### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  llm-proxy:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

#### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-proxy-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-proxy-api
  template:
    metadata:
      labels:
        app: llm-proxy-api
    spec:
      containers:
      - name: llm-proxy
        image: llm-proxy-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

```

### Verificação da Instalação

```bash
# Teste básico
curl http://localhost:8000/health

# Teste com provedor
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🚀 Guia de Uso

### Uso Básico

```python
import requests

# Configuração
API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

# Chat Completion
response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Explain quantum computing"}
        ],
        "max_tokens": 500
    }
)

print(response.json())
```

### Streaming

```python
import requests

response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Tell me a story"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### JavaScript/TypeScript

```javascript
// Usando fetch
const response = await fetch('/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4',
    messages: [{role: 'user', content: 'Hello!'}],
    stream: true
  })
});

// Para streaming
const reader = response.body.getReader();
while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  console.log(new TextDecoder().decode(value));
}
```

---

## 🔌 APIs e Endpoints

### Endpoints Principais

#### Chat Completions
```http
POST /v1/chat/completions
```

**Parâmetros:**
- `model` (string): Nome do modelo
- `messages` (array): Array de mensagens
- `max_tokens` (int, opcional): Máximo de tokens
- `temperature` (float, opcional): Criatividade (0.0-2.0)
- `stream` (boolean, opcional): Streaming habilitado

**Exemplo:**
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain AI"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

#### Text Completions
```http
POST /v1/completions
```

#### Embeddings
```http
POST /v1/embeddings
```

### Endpoints de Monitoramento

#### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": 1699999999.123,
  "providers": {
    "total": 8,
    "healthy": 7,
    "degraded": 1,
    "unhealthy": 0
  },
  "uptime": "99.95%",
  "last_check": "2023-11-01T12:00:00Z"
}
```

#### Métricas
```http
GET /metrics
```

#### Status dos Provedores
```http
GET /providers
```

### Endpoints Administrativos

#### Health Worker
```http
GET /status          # Status detalhado de todos os provedores
GET /status/{name}   # Status de provedor específico
POST /check          # Trigger manual de health check
POST /discover       # Trigger descoberta de provedores
POST /cache/clear    # Limpar cache de health checks
```

### Autenticação

Todos os endpoints requerem autenticação via header:

```
Authorization: Bearer your-api-key
```

Ou via header customizado:

```
X-API-Key: your-api-key
```

---

## ⚙️ Arquivos de Configuração

### Estrutura de Configuração

#### `config.yaml` - Configuração Principal

```yaml
# Configurações globais
app_name: "LLM Proxy API"
app_version: "2.0.0"
debug: false
host: "127.0.0.1"
port: 8000

# Autenticação
api_keys:
  - "your-api-key-here"
api_key_header: "X-API-Key"

# Segurança
cors_origins:
  - "*"

# Rate Limiting
rate_limit_rpm: 1000
rate_limit_window: 60

# Timeouts
request_timeout: 300

# Circuit Breaker
circuit_breaker_threshold: 5
circuit_breaker_timeout: 60

# Logging
log_level: "INFO"
log_file: null

# Health Monitoring
health_check_interval: 60
health_check_cache_ttl: 30

# Provider Discovery
provider_discovery_interval: 300
provider_registry_url: null

# Condensation (Context Management)
condensation:
  max_tokens_default: 512
  error_keywords:
    - "context_length_exceeded"
    - "maximum context length"
  adaptive_factor: 0.5
  cache_ttl: 300

# Provedores
providers:
  - name: "openai_default"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "PROXY_API_OPENAI_API_KEY"
    models:
      - "gpt-4"
      - "gpt-3.5-turbo"
    enabled: true
    priority: 1
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    max_connections: 10
    keepalive_timeout: 30
```

#### `health_worker_providers.json` - Configuração de Health Checks

```json
{
  "providers": [
    {
      "name": "openai",
      "base_url": "https://api.openai.com",
      "models": ["gpt-3.5-turbo", "gpt-4"]
    },
    {
      "name": "anthropic",
      "base_url": "https://api.anthropic.com",
      "models": ["claude-3-sonnet"]
    }

  ]

}
```

#### `.env` - Variáveis de Ambiente

```bash
# API Keys
PROXY_API_OPENAI_API_KEY=sk-your-openai-key
PROXY_API_ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
PROXY_API_GROK_API_KEY=xai-your-grok-key

# Server Configuration
PROXY_API_PORT=8000
PROXY_API_HOST=127.0.0.1
LOG_LEVEL=INFO

# Health Worker
HEALTH_CHECK_INTERVAL=60
HEALTH_CHECK_CACHE_TTL=30
PROVIDER_DISCOVERY_INTERVAL=300

# HTTP Client
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE=20
HTTP_TIMEOUT=5.0
```

### Validação de Configuração

O sistema valida automaticamente todas as configurações na inicialização:

```bash
python validate_env.py
```

---

## 📊 Monitoramento e Métricas

### Métricas Prometheus

#### Counters
- `llm_proxy_requests_total{provider, endpoint, status}` - Total de requests
- `llm_proxy_errors_total{provider, error_type}` - Total de erros
- `llm_proxy_tokens_total{provider, operation}` - Total de tokens

#### Histograms
- `llm_proxy_request_duration_seconds{provider, endpoint}` - Duração de requests
- `llm_proxy_response_time_seconds{provider}` - Tempo de resposta

#### Gauges
- `llm_proxy_active_connections{provider}` - Conexões ativas
- `llm_proxy_circuit_breaker_state{provider}` - Estado do circuit breaker
- `llm_proxy_health_check_cache_size` - Tamanho do cache

### Health Checks

#### Provedor Health
```json
{
  "name": "openai",
  "status": "healthy",
  "last_check": 1699999999.123,
  "response_time": 0.245,
  "models": ["gpt-4", "gpt-3.5-turbo"],
  "circuit_breaker": {
    "state": "closed",
    "failure_count": 0,
    "last_failure_time": null
  }
}
```

#### Sistema Health
```json
{
  "status": "healthy",
  "uptime": "99.95%",
  "version": "2.0.0",
  "components": {
    "api_server": "healthy",
    "health_worker": "healthy",
    "metrics_collector": "healthy",
    "config_manager": "healthy"
  }
}
```

### Logging

#### Estrutura de Log

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "llm_proxy.core.request_router",
  "request_id": "req_123456",
  "message": "Request completed successfully",
  "provider": "openai",
  "model": "gpt-4",
  "tokens": 150,
  "duration": 0.245,
  "status_code": 200
}
```

#### Níveis de Log

- `DEBUG`: Detalhes técnicos e debugging
- `INFO`: Operações normais e métricas
- `WARNING`: Problemas não críticos
- `ERROR`: Erros que afetam funcionalidade
- `CRITICAL`: Erros críticos do sistema

### Dashboards

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "LLM Proxy API",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_proxy_requests_total[5m])",
            "legendFormat": "{{provider}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_proxy_errors_total[5m])",
            "legendFormat": "{{provider}} - {{error_type}}"
          }
        ]
      }
    ]
  }
}
```

---

## 📁 Estrutura de Diretórios

```
llm-proxy-api/
├── 📄 main.py                 # Ponto de entrada principal
├── 📄 main_dynamic.py         # Versão dinâmica com hot-reload
├── 📄 web_ui.py              # Interface web de configuração
├── 📄 health_worker/         # Serviço de monitoramento de saúde
│   └── 📄 app.py
├── 📄 requirements.txt       # Dependências Python
├── 📄 config.yaml           # Configuração principal
├── 📄 .env                  # Variáveis de ambiente
├── 📄 pytest.ini            # Configuração de testes
├── 📄 build_config.yaml     # Configuração de build
├── 📁 src/                  # Código fonte
│   ├── 📁 api/              # Endpoints da API
│   ├── 📁 core/             # Componentes core
│   │   ├── 📄 config.py     # Gerenciamento de configuração
│   │   ├── 📄 provider_factory.py  # Factory de provedores
│   │   └── 📄 request_router.py    # Roteamento de requests
│   ├── 📁 providers/        # Implementações de provedores
│   │   ├── 📄 openai.py
│   │   ├── 📄 anthropic.py
│   │   └── 📄 ...
│   ├── 📁 services/         # Serviços utilitários
│   │   ├── 📄 logging.py
│   │   └── 📄 metrics.py
│   ├── 📁 scripts/          # Scripts utilitários
│   │   ├── 📄 export_dataset.py
│   │   └── 📄 validate_env.py
│   └── 📁 utils/            # Utilitários
├── 📁 tests/                # Testes
│   ├── 📄 test_providers.py
│   ├── 📄 test_endpoints.py
│   └── 📄 test_config.py
├── 📁 docs/                 # Documentação
│   ├── 📄 README.md
│   ├── 📄 export_dataset.md
│   └── 📄 PROJECT_DOCUMENTATION.md
├── 📁 static/               # Assets estáticos
├── 📁 templates/            # Templates HTML
├── 📁 logs/                 # Logs do sistema
├── 📁 exports/              # Dados exportados
├── 📁 systemd-services/     # Serviços systemd
├── 📁 venv_test/            # Ambiente virtual de teste
└── 📁 p/                    # Projetos relacionados
```

### Arquivos Importantes

#### Core Files
- `main_dynamic.py`: Ponto de entrada principal com hot-reload
- `config.yaml`: Configuração central do sistema
- `requirements.txt`: Dependências Python

#### Configuration Files
- `.env`: Variáveis de ambiente sensíveis
- `health_worker_providers.json`: Configuração de health checks
- `build_config.yaml`: Configuração de build executáveis

#### Documentation
- `README.md`: Documentação principal
- `docs/export_dataset.md`: Guia de exportação de dados
- `docs/PROJECT_DOCUMENTATION.md`: Esta documentação completa

#### Services
- `health_worker/app.py`: Serviço de monitoramento de saúde
- `web_ui.py`: Interface web de administração
- `src/scripts/export_dataset.py`: Utilitário de exportação

---

## 💻 Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

```bash
# 1. Clone e setup
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api
python -m venv venv
source venv/bin/activate

# 2. Instale dependências de desenvolvimento
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Configure pre-commit hooks
pre-commit install

# 4. Execute testes
pytest tests/ -v

# 5. Execute linting
black src/

isort src/

flake8 src/
```

### Estrutura de Código

#### Padrões de Codificação

```python
# Exemplo de implementação de provedor
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig

class MyProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Implementação de health check"""
        async with self.http_client.get("/health") as response:
            return {
                "status": "healthy" if response.status == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds() * 1000
            }

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação de chat completion"""
        # Lógica específica do provedor
        pass
```

#### Testes

```python
# Exemplo de teste
import pytest
from unittest.mock import AsyncMock, patch

class TestMyProvider:
    @pytest.fixture
    def provider(self):
        config = ProviderConfig(
            name="test_provider",
            base_url="https://api.example.com",
            api_key="test-key"
        )
        return MyProvider(config)

    @pytest.mark.asyncio
    async def test_create_completion_success(self, provider):
        # Arrange
        request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        # Act
        with patch.object(provider.http_client, 'post') as mock_post:
            mock_post.return_value = AsyncMock(
                status=200,
                json=AsyncMock(return_value={"choices": []})
            )
            result = await provider.create_completion(request)

        # Assert
        assert result is not None
```

### Adicionando Novos Provedores

1. **Criar classe do provedor** em `src/providers/`

2. **Implementar métodos abstratos** da `BaseProvider`
3. **Registrar no ProviderFactory**

4. **Adicionar configuração** em `config.yaml`
5. **Escrever testes** abrangentes
6. **Atualizar documentação**

### Debugging

#### Logs Detalhados

```bash

# Execute com debug
LOG_LEVEL=DEBUG python main_dynamic.py

# Ou configure em config.yaml
log_level: "DEBUG"
log_file: "logs/debug.log"
```

#### Health Check Debug

```bash
# Verificar status de provedores
curl http://localhost:8000/providers

# Executar health check manual
curl -X POST http://localhost:8000/check

# Ver métricas detalhadas
curl http://localhost:8000/metrics
```

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Autenticação

**Sintomas:**
```
HTTP 401: Invalid API key
```

**Soluções:**
```bash
# Verificar se API key está configurada
echo $PROXY_API_OPENAI_API_KEY

# Verificar formato do header
curl -H "Authorization: Bearer your-key" http://localhost:8000/v1/models

# Verificar configuração
cat config.yaml | grep api_keys
```

#### 2. Provedor Indisponível

**Sintomas:**
```
HTTP 503: All providers are currently unavailable
```

**Soluções:**
```bash
# Verificar status dos provedores
curl http://localhost:8000/health

# Executar health check manual

curl -X POST http://localhost:8000/check

# Verificar circuit breaker
curl http://localhost:8000/providers
```

#### 3. Rate Limiting

**Sintomas:**
```
HTTP 429: Too Many Requests
```

**Soluções:**
```yaml

# Aumentar limites em config.yaml
rate_limit_rpm: 2000  # Aumentar RPM
rate_limit_window: 120  # Aumentar janela
```

#### 4. Timeout de Request

**Sintomas:**
```
HTTP 504: Gateway Timeout
```

**Soluções:**

```yaml
# Aumentar timeouts em config.yaml
request_timeout: 600  # 10 minutos
circuit_breaker_timeout: 120  # 2 minutos
```

#### 5. Problemas de Memória

**Sintomas:**

```
MemoryError ou alta utilização de RAM
```

**Soluções:**
```yaml
# Otimizar configurações
max_connections: 50  # Reduzir conexões
health_check_cache_ttl: 15  # Cache menor
```

### Diagnóstico Avançado

#### Verificar Logs

```bash
# Logs em tempo real
tail -f logs/proxy_api.log

# Filtrar por nível
grep "ERROR" logs/proxy_api.log

# Filtrar por provedor
grep "openai" logs/proxy_api.log

```

#### Analisar Métricas

```bash
# Request rate por provedor
curl http://localhost:8000/metrics | grep llm_proxy_requests_total

# Latência média
curl http://localhost:8000/metrics | grep llm_proxy_request_duration

# Taxa de erro

curl http://localhost:8000/metrics | grep llm_proxy_errors_total
```

#### Debug de Conexões

```bash
# Verificar conexões ativas
netstat -tlnp | grep :8000

# Verificar processos
ps aux | grep python

# Verificar uso de recursos
top -p $(pgrep python)
```

### Recuperação de Desastres

#### Backup de Configuração

```bash
# Backup automático
cp config.yaml config.yaml.backup
cp .env .env.backup

# Restauração
cp config.yaml.backup config.yaml
cp .env.backup .env
```

#### Reset de Estado

```bash
# Limpar cache de health checks
curl -X POST http://localhost:8000/cache/clear

# Reset circuit breakers
# Reiniciar o serviço
systemctl restart llm-proxy-api
```

---

## 📚 Referências

### Documentação Relacionada

- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Metrics](https://prometheus.io/docs/practices/naming/)

#recursos-externos-llm-comparison-https-llm-comparison-com)
- [API Rate Limiting Best Practices](https://stripe.com/docs/rate-limits)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

#ferramentas-de-desenvolvimento-poetry-https-python-poetry-org) - Gerenciamento de dependências
- [Black](https://black.readthedocs.io/) - Formatação de código
- [Pylint](https://pylint.readthedocs.io/) - Linting
- [pytest](https://docs.pytest.org/) - Testes

### Suporte

- **GitHub Issues**: Para bugs e feature requests
- **Discussions**: Para perguntas gerais
- **Wiki**: Tutoriais e guias avançados

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License**. Veja o arquivo `LICENSE` para detalhes.

---

*Última atualização: Janeiro 2024*
*Versão: 2.0.0*
