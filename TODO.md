# Roteiro de Melhorias (Rodada 3)

Este arquivo rastreia as tarefas para a terceira rodada de revisão de código, focada em robustez e eficiência.

- [x] **1. Corrigir chamada de data/hora depreciada**
  - Em `src/core/logging.py`, substituir `datetime.utcnow()` por `datetime.now(datetime.UTC)`.
  - Adicionar `from datetime import timezone` às importações.

- [x] **2. Adicionar método `debug` ao Logger**
  - Em `src/core/logging.py`, adicionar um método `debug(self, msg: str, **kwargs)` à classe `ContextualLogger`.

- [x] **3. Remover configurações obsoletas**
  - Em `src/core/config.py`, remover as configurações `openai_api_key` e `anthropic_api_key` da classe `Settings`, pois não são mais utilizadas.

- [x] **4. Verificação Final**
  - Executar todos os testes para garantir que nenhuma regressão foi introduzida.
  - Submeter o trabalho finalizado.

# Roteiro de Melhorias (Rodada 4: Web UI Improvements)

Consolidação de todos os comentários inline (Issue, Opt, NOTE) de `web_ui.py` em todos os arquivos Python do projeto. Priorizados por severidade: High (segurança, crashes), Medium (validação, robustez), Low (otimizações, UX menor).

## High Severity (Segurança e Estabilidade Crítica)
- [ ] **Adicionar proteção CSRF completa**: Em `web_ui.py` (linha 12), integrar Flask-WTF para tokens CSRF em forms, em vez de simples session check (linha 218). Risco de ataques CSRF em /save_config.
- [ ] **Eximir arquivos estáticos de autenticação**: Em `web_ui.py` (linha 186), garantir que /static seja sempre público para CSS/JS, evitando bloqueio desnecessário.
- [ ] **Tornar ALLOWED_ENV_VARS imutável e dinâmica**: Em `web_ui.py` (linha 27), usar frozenset gerado de VALID_PROVIDERS para evitar bypass de segurança ao adicionar env vars arbitrárias.
- [ ] **Adicionar backup antes de writes em arquivos**: Em `save_config_and_env` (linhas 137, 148), usar shutil.copy para backup (e.g., config.yaml.bak) antes de set_key ou yaml.dump, prevenindo perda de dados em falhas.
- [ ] **Desabilitar debug mode em prod**: Em `web_ui.py` (linha 248), usar os.getenv('FLASK_DEBUG', 'False') e desabilitar debug=True para evitar vazamento de info sensível.

## Medium Severity (Validação e Robustez)
- [ ] **Integrar schema validation para YAML load**: Em `load_config` (linha 9), usar Pydantic ou Cerberus para validar estrutura de providers (e.g., required 'name', 'type'), flash erros específicos.
- [ ] **Validação de range para port**: Em `save_config_and_env` (linha 157), garantir 1 <= port <= 65535 e verificar se port está em uso (socket test).
- [ ] **Tornar VALID_PROVIDERS dinâmica**: Em `web_ui.py` (linha 18), carregar de src/services/provider_loader.py ou config.yaml para auto-sync com novos providers.
- [ ] **Adicionar logging para erros**: Em múltiplas exceções (e.g., linha 178), importar logging e usar logger.error(str(e)) para rastreamento, em vez de apenas flash.
- [ ] **Suporte a JSON POST para /save_config**: Em `save_config` (linha 215), detectar Content-Type e retornar JSON {'success': bool, 'message': str} para uso API, com rate limiting (Flask-Limiter).
- [ ] **Validação única de nomes de providers**: Em `save_config_and_env` (linha 91), verificar duplicatas em providers list, flash erro se nomes repetidos.
- [ ] **Adicionar campo 'enabled' ao form e dict**: Em `save_config_and_env` (linha 122), incluir checkbox para enabled, default True, salvar no provider dict.

## Low Severity (Otimizações e Melhorias Menores)
- [ ] **Carregar secret_key de env para persistência**: Em `web_ui.py` (linha 15), usar os.getenv('SECRET_KEY') ou file, evitando invalidação de sessions em restarts.
- [ ] **Centralizar regex patterns**: Em `web_ui.py` (linha 11), mover ENV_VAR_PATTERN e PROVIDER_NAME_PATTERN para src/core/config para reutilização.
- [ ] **Cache loads de config/env**: Em `index` (linha 206), usar Flask-Caching para evitar reload full em cada GET, especialmente para configs grandes.
- [ ] **Auto-restart ou notify para changes**: Em `save_config_and_env` (linha 170), adicionar hook para restart server ou websocket para notify main API de changes.
- [ ] **Adicionar suporte a perfis .env**: Em `load_env` (linha 65), suportar .env.dev/.env.prod via env var, com flash warning se missing.
- [ ] **Paginação para providers >10**: Em `index` (linha 206), paginar form se len(config['providers']) >10, usando Flask-Paginate.
- [ ] **Usar gunicorn para prod**: Em `__main__` (linha 247), documentar uso de gunicorn em README, com SSL context para HTTPS.
