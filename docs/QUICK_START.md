# 🚀 Guia Rápido - LLM Proxy API

## Em 5 Minutos

Este guia mostra como colocar o LLM Proxy API funcionando rapidamente.

---

## 📦 Instalação Rápida

### 1. Baixar e Configurar

```bash

# Clone o repositório
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api

# Crie ambiente virtual
python -m venv venv

source venv/bin/activate  # Linux/macOS

# ou no Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt
```

### 2. Configurar API Keys

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas chaves de API
nano .env
```

Conteúdo do `.env`:
```bash
# API Keys (obtenha em: https://platform.openai.com/api-keys)
PROXY_API_OPENAI_API_KEY=sk-your-openai-key-here

# Configurações do servidor
PROXY_API_PORT=8000
LOG_LEVEL=INFO
```

### 3. Executar o Servidor

```bash
# Execute o servidor
python main_dynamic.py
```

**Saída esperada:**
```
INFO: Started server process [12345]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 🧪 Teste Básico

### Verificar se está funcionando

```bash
# Abra outro terminal e teste
curl http://localhost:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": 1699999999.123,
  "providers": {
    "total": 1,
    "healthy": 1,
    "degraded": 0,
    "unhealthy": 0
  }

}

```

### Primeiro Request

```bash
# Teste com chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Olá! Como você está?"}
    ],
    "max_tokens": 100
  }'
```

---

## ⚙️ Configuração Básica

### Arquivo `config.yaml`

```yaml
# Configurações mínimas
app_name: "LLM Proxy API"
debug: false
host: "127.0.0.1"
port: 8000

# API Key (mesma do .env)
api_keys:
  - "your-api-key-here"

# Provedores
providers:
  - name: "openai_default"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "PROXY_API_OPENAI_API_KEY"
    models:
      - "gpt-3.5-turbo"
      - "gpt-4"
    enabled: true
    priority: 1
    timeout: 30
```

---

## 📱 Exemplos de Uso

### Python

```python
import requests

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
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Explique inteligência artificial"}
        ],
        "max_tokens": 200
    }
)

print(response.json())
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [{role: 'user', content: 'Olá!'}],
    max_tokens: 100
  })
});

const data = await response.json();
console.log(data);
```

### cURL

```bash
# Chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Olá!"}],
    "max_tokens": 50
  }'

# Listar modelos disponíveis
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer your-api-key"

# Health check
curl http://localhost:8000/health

```

---

## 🔍 Verificação e Debug

### Verificar Status dos Provedores

```bash

# Status detalhado
curl http://localhost:8000/providers

# Executar health check manual
curl -X POST http://localhost:8000/check
```

### Verificar Logs

```bash
# Logs em tempo real
tail -f logs/proxy_api.log

# Últimas 20 linhas
tail -20 logs/proxy_api.log
```

### Verificar Métricas

```bash
# Métricas Prometheus

curl http://localhost:8000/metrics
```

---

## 🐳 Docker (Opcional)

### Usando Docker Compose

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
```

```bash
# Executar

docker-compose up -d

# Verificar logs

docker-compose logs -f llm-proxy
```

---

## 🚨 Solução de Problemas

### Problema: "Invalid API key"

**Solução:**

```bash
# Verificar se a chave está correta
echo $PROXY_API_OPENAI_API_KEY

# Verificar formato do header
curl -H "Authorization: Bearer YOUR_KEY_HERE" http://localhost:8000/health
```

### Problema: "Provider unavailable"

**Solução:**
```bash
# Verificar status
curl http://localhost:8000/health

# Executar health check
curl -X POST http://localhost:8000/check
```

### Problema: "Connection refused"

**Solução:**
```bash
# Verificar se o servidor está rodando
ps aux | grep python

# Verificar porta
netstat -tlnp | grep :8000

# Reiniciar servidor
python main_dynamic.py
```

---

## 📚 Próximos Passos

1. **Leia a documentação completa**: [`docs/PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md)
2. **Configure múltiplos provedores**: Adicione Anthropic, Grok, etc.
3. **Configure monitoramento**: Integre com Prometheus/Grafana
4. **Setup produção**: Use Docker/Kubernetes para deployment

---

#suporte-documentacao-completa-docs-project-documentation-md-project-documentation-md)
- **Referência de arquivos**: [`docs/FILE_REFERENCE.md`](FILE_REFERENCE.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/llm-proxy-api/issues)

---

*Guia criado para LLM Proxy API v2.0.0*
