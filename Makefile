# Makefile para Testes de Mutação

.PHONY: help install-mutmut test-mutation test-mutation-expanded test-mutation-eliminate test-mutation-threshold clean-mutation

# Configurações padrão
THRESHOLD ?= 95.0
CONFIG ?= pyproject.toml
REPORT ?= mutation_test_report.json

help: ## Mostra ajuda
	@echo "🧬 Testes de Mutação - Comandos Disponíveis:"
	@echo ""
	@echo "  make install-mutmut              - Instala o mutmut"
	@echo "  make test-mutation               - Executa testes de mutação básicos"
	@echo "  make test-mutation-expanded      - Executa testes de mutação expandidos"
	@echo "  make test-mutation-eliminate     - Executa testes para eliminar mutações restantes"
	@echo "  make test-mutation-threshold     - Executa testes com threshold específico"
	@echo "  make clean-mutation             - Limpa arquivos de mutação"
	@echo ""
	@echo "Exemplos:"
	@echo "  make test-mutation THRESHOLD=90.0"
	@echo "  make test-mutation-expanded THRESHOLD=98.0"
	@echo "  make test-mutation-eliminate THRESHOLD=95.0"

install-mutmut: ## Instala o mutmut
	@echo "📦 Instalando mutmut..."
	pip install --break-system-packages mutmut
	@echo "✅ mutmut instalado com sucesso!"

test-mutation: ## Executa testes de mutação básicos
	@echo "🧬 Executando testes de mutação básicos..."
	python run_mutation_tests.py --threshold $(THRESHOLD) --config $(CONFIG) --report $(REPORT)

test-mutation-expanded: ## Executa testes de mutação expandidos
	@echo "🧬 Executando testes de mutação expandidos..."
	python run_expanded_mutation_tests.py --threshold $(THRESHOLD) --config expanded_pyproject.toml --report expanded_$(REPORT)

test-mutation-eliminate: ## Executa testes para eliminar mutações restantes
	@echo "🧬 Executando testes para eliminar mutações restantes..."
	python run_eliminate_mutations.py --threshold $(THRESHOLD) --config simple_pyproject.toml --report eliminate_$(REPORT) --show-survived

test-mutation-threshold: ## Executa testes com threshold específico
	@echo "🧬 Executando testes de mutação com threshold $(THRESHOLD)%..."
	python run_mutation_tests.py --threshold $(THRESHOLD) --config $(CONFIG) --report threshold_$(THRESHOLD)_$(REPORT)

clean-mutation: ## Limpa arquivos de mutação
	@echo "🧹 Limpando arquivos de mutação..."
	rm -rf mutants/
	rm -f mutation_test_report.json
	rm -f expanded_mutation_test_report.json
	rm -f eliminate_mutations_report.json
	rm -f threshold_*_mutation_test_report.json
	@echo "✅ Arquivos de mutação limpos!"

# Comandos específicos para diferentes thresholds
test-mutation-90: ## Executa testes com threshold 90%
	@$(MAKE) test-mutation THRESHOLD=90.0

test-mutation-95: ## Executa testes com threshold 95%
	@$(MAKE) test-mutation THRESHOLD=95.0

test-mutation-98: ## Executa testes com threshold 98%
	@$(MAKE) test-mutation THRESHOLD=98.0

# Comandos para diferentes tipos de teste
test-mutation-core: ## Executa testes apenas nos módulos core
	@echo "🧬 Executando testes de mutação nos módulos core..."
	cp expanded_pyproject.toml pyproject.toml
	python run_mutation_tests.py --threshold $(THRESHOLD) --config pyproject.toml --report core_$(REPORT)

test-mutation-api: ## Executa testes apenas nos módulos de API
	@echo "🧬 Executando testes de mutação nos módulos de API..."
	cp expanded_pyproject.toml pyproject.toml
	python run_mutation_tests.py --threshold $(THRESHOLD) --config pyproject.toml --report api_$(REPORT)

# Comandos para relatórios
report-mutation: ## Gera relatório dos testes de mutação
	@echo "📊 Gerando relatório dos testes de mutação..."
	@if [ -f mutation_test_report.json ]; then \
		python -c "import json; data=json.load(open('mutation_test_report.json')); print(f'Taxa de detecção: {data[\"results\"][\"detection_rate\"]:.1f}%'); print(f'Threshold: {data[\"threshold\"]}%'); print(f'Passou: {data[\"passed\"]}')"; \
	else \
		echo "❌ Nenhum relatório encontrado. Execute os testes primeiro."; \
	fi

# Comandos para CI/CD
ci-mutation-test: ## Executa testes de mutação para CI/CD
	@echo "🚀 Executando testes de mutação para CI/CD..."
	@$(MAKE) test-mutation THRESHOLD=95.0
	@$(MAKE) test-mutation-expanded THRESHOLD=90.0
	@$(MAKE) test-mutation-eliminate THRESHOLD=95.0
	@echo "✅ Todos os testes de mutação executados!"

# Comandos para desenvolvimento
dev-mutation-test: ## Executa testes de mutação para desenvolvimento
	@echo "🔧 Executando testes de mutação para desenvolvimento..."
	@$(MAKE) test-mutation THRESHOLD=90.0
	@echo "✅ Testes de mutação para desenvolvimento executados!"

# Comandos para produção
prod-mutation-test: ## Executa testes de mutação para produção
	@echo "🏭 Executando testes de mutação para produção..."
	@$(MAKE) test-mutation THRESHOLD=98.0
	@$(MAKE) test-mutation-expanded THRESHOLD=95.0
	@echo "✅ Testes de mutação para produção executados!"