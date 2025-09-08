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
