# Relatório de Dependências do LLM Proxy API

## Dependências Atuais (requirements.txt)

```txt
# Core FastAPI stack
fastapi==0.116.1
uvicorn[standard]==0.35.0
pydantic==2.11.7
pydantic-settings==2.10.1

# HTTP client
httpx==0.28.1

# Configuration
pyyaml==6.0.2
python-dotenv==1.1.1

# Security & Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Rate limiting
slowapi==0.1.9

# Logging & Monitoring
structlog==25.4.0

# Development tools
black==25.1.0
ruff==0.12.12
pytest==8.4.2
pytest-asyncio==1.1.0

# Windows executable
pyinstaller==6.15.0
```

## Dependências Instaladas (pip list)

### Principais Dependências do Projeto
| Pacote | Versão Instalada | Versão Requerida | Status |
|--------|------------------|------------------|--------|
| fastapi | 0.104.1 | 0.116.1 | ❌ Desatualizado |
| uvicorn | 0.24.0 | 0.35.0 | ❌ Desatualizado |
| pydantic | 2.5.0 | 2.11.7 | ❌ Desatualizado |
| pydantic-settings | 2.1.0 | 2.10.1 | ❌ Desatualizado |
| httpx | 0.25.2 | 0.28.1 | ❌ Desatualizado |
| pyyaml | 6.0.1 | 6.0.2 | ⚠️ Levemente desatualizado |
| python-jose | 3.3.0 | 3.3.0 | ✅ Atualizado |
| python-dotenv | 1.0.0 | 1.1.1 | ❌ Desatualizado |
| slowapi | 0.1.9 | 0.1.9 | ✅ Atualizado |
| structlog | 23.2.0 | 25.4.0 | ❌ Desatualizado |
| black | 23.11.0 | 25.1.0 | ❌ Desatualizado |
| ruff | 0.1.6 | 0.12.12 | ❌ Desatualizado |
| pytest | 7.4.3 | 8.4.2 | ❌ Desatualizado |
| pytest-asyncio | 0.21.1 | 1.1.0 | ❌ Desatualizado |
| pyinstaller | 6.2.0 | 6.15.0 | ⚠️ Versão mais recente instalada |

### Dependências com Vulnerabilidades de Segurança
| Pacote | Versão | Vulnerabilidade | Severidade | Versão Corrigida |
|--------|--------|-----------------|------------|------------------|
| black | 23.11.0 | PYSEC-2024-48 | Média | 24.3.0+ |
| ecdsa | 0.19.1 | GHSA-wj6h-64fc-37mp | Alta | Não especificada |
| fastapi | 0.104.1 | PYSEC-2024-38 | Média | 0.109.1+ |
| py | 1.11.0 | PYSEC-2022-42969 | Alta | Não afetada |
| python-jose | 3.3.0 | PYSEC-2024-232 | Média | 3.4.0+ |
| python-jose | 3.3.0 | PYSEC-2024-233 | Média | 3.4.0+ |
| starlette | 0.27.0 | GHSA-f96h-pmfr-66vw | Alta | 0.40.0+ |
| starlette | 0.27.0 | GHSA-2c2j-9gv5-cj73 | Alta | 0.47.2+ |
| torch | 2.3.0 | PYSEC-2025-41 | Média | 2.6.0+ |
| torch | 2.3.0 | PYSEC-2024-259 | Média | 2.5.0+ |
| torch | 2.3.0 | GHSA-3749-ghw9-m3mg | Baixa | 2.7.1rc1+ |
| torch | 2.3.0 | GHSA-887c-mr87-cxwp | Baixa | 2.8.0+ |

### Incompatibilidades Detectadas (pip check)
```
duckduckgo-mcp-server 0.1.1 has requirement httpx>=0.28.1 but you have httpx 0.25.2.
langchain-core 0.3.75 has requirement pydantic>=2.7.4 but you have pydantic 2.5.0.
langgraph 0.6.6 has requirement pydantic>=2.7.4 but you have pydantic 2.5.0.
mcp 1.13.1 has requirement anyio>=4.5 but you have anyio 3.7.1.
mcp 1.13.1 has requirement httpx>=0.27.1 but you have httpx 0.25.2.
mcp 1.13.1 has requirement pydantic<3.0.0>=2.11.0 but you have pydantic 2.5.0.
mcp 1.13.1 has requirement pydantic-settings>=2.5.2 but you have pydantic-settings 2.1.0.
mcp 1.13.1 has requirement uvicorn>=0.31.1; sys_platform != "emscripten" but you have uvicorn 0.24.0.
ollama 0.5.3 has requirement httpx>=0.27 but you have httpx 0.25.2.
ollama 0.5.3 has requirement pydantic>=2.9 but you have pydantic 2.5.0.
sse-starlette 3.0.2 has requirement anyio>=4.7.0 but you have anyio 3.7.1.
```

## Recomendações de Atualização

### Atualizações Críticas (Segurança)
1. **fastapi**: 0.104.1 → 0.116.1
2. **httpx**: 0.25.2 → 0.28.1
3. **pydantic**: 2.5.0 → 2.11.7
4. **pydantic-settings**: 2.1.0 → 2.10.1
5. **uvicorn**: 0.24.0 → 0.35.0
6. **python-jose**: 3.3.0 → 3.4.0
7. **black**: 23.11.0 → 25.1.0
8. **structlog**: 23.2.0 → 25.4.0
9. **python-dotenv**: 1.0.0 → 1.1.1
10. **ruff**: 0.1.6 → 0.12.12
11. **pytest**: 7.4.3 → 8.4.2
12. **pytest-asyncio**: 0.21.1 → 1.1.0

### Atualizações Recomendadas (Compatibilidade)
1. **anyio**: 3.7.1 → 4.5+
2. **starlette**: 0.27.0 → 0.40.0+
3. **torch**: 2.3.0 → 2.6.0+

## Impacto das Atualizações

### Baixo Impacto
- **pyyaml**: Alterações mínimas, compatibilidade mantida
- **passlib**: API estável, poucas mudanças
- **slowapi**: Poucas mudanças significativas
- **pyinstaller**: Alterações principalmente em build process

### Médio Impacto
- **fastapi/pydantic**: Mudanças na API de validação, migração de `@validator` para `@field_validator`
- **httpx**: Algumas alterações na API, especialmente em tratamento de exceções
- **uvicorn**: Possíveis alterações em configurações e inicialização

### Alto Impacto
- **python-jose**: Possíveis mudanças em APIs criptográficas
- **pytest**: Alterações em fixtures e plugins

## Plano de Atualização Sugerido

1. **Etapa 1**: Atualizar dependências de desenvolvimento (black, ruff, pytest)
2. **Etapa 2**: Atualizar dependências principais (fastapi, httpx, pydantic)
3. **Etapa 3**: Atualizar dependências de infraestrutura (uvicorn, pyinstaller)
4. **Etapa 4**: Atualizar dependências secundárias (structlog, python-dotenv)
5. **Etapa 5**: Verificar e resolver incompatibilidades restantes

## Considerações Especiais

- Algumas dependências como `torch` parecem não pertencer ao escopo principal do projeto LLM Proxy API e podem ser removidas se não forem utilizadas
- O pacote `py` com vulnerabilidade crítica parece ser uma dependência indireta e pode ser resolvido atualizando dependências diretas
- A versão do `pyinstaller` instalada (6.2.0) é mais recente que a especificada no requirements.txt (6.15.0), o que pode indicar uma atualização manual
