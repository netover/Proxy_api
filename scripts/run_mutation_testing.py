#!/usr/bin/env python3
"""
Script para executar mutation testing com mutmut localmente.

Usage:
    python scripts/run_mutation_testing.py [--fast] [--full] [--report]

Options:
    --fast      Executa apenas mutações não testadas (incremental)
    --full      Executa todas as mutações (pode demorar)
    --report    Gera relatório HTML sem executar mutações
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True):
    """Executa um comando e retorna o resultado."""
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Erro: {result.stderr}")
        sys.exit(1)
    return result


def main():
    """Função principal."""
    args = sys.argv[1:]

    # Verificar se mutmut está instalado
    try:
        import mutmut
        print(f"mutmut versão: {mutmut.__version__}")
    except ImportError:
        print("Instalando mutmut...")
        run_command([sys.executable, "-m", "pip", "install", "mutmut>=2.4.0"])

    # Criar diretório de cache se não existir
    cache_dir = Path(".mutmut-cache")
    cache_dir.mkdir(exist_ok=True)

    if "--fast" in args or len(args) == 0:
        print("🚀 Executando mutation testing incremental...")
        # Executar mutações não testadas
        run_command([
            "mutmut", "run",
            "--paths-to-mutate=src/",
            "--tests-dir=tests/",
            "--runner=python -m pytest -x --tb=no -q",
            "--dict-synonyms=True,False",
            "--dict-synonyms=true,false"
        ])

    elif "--full" in args:
        print("🔬 Executando mutation testing completo...")
        # Executar todas as mutações (pode demorar muito)
        run_command([
            "mutmut", "run",
            "--paths-to-mutate=src/",
            "--tests-dir=tests/",
            "--runner=python -m pytest -x --tb=no -q",
            "--dict-synonyms=True,False",
            "--dict-synonyms=true,false",
            "--rerun-all"
        ])

    elif "--report" in args:
        print("📊 Gerando relatório de mutation testing...")
        # Gerar apenas o relatório
        run_command(["mutmut", "results"])
        run_command(["mutmut", "html"])
        print("✅ Relatório gerado em html/index.html")

    else:
        print("❌ Opção inválida. Use --fast, --full ou --report")
        sys.exit(1)

    # Mostrar resultados
    print("\n📊 Resultados do Mutation Testing:")
    results = run_command(["mutmut", "results"], check=False)
    print(results.stdout)

    if results.returncode == 0:
        print("✅ Mutation testing concluído com sucesso!")
    else:
        print("⚠️ Alguns testes falharam. Verifique os resultados acima.")


if __name__ == "__main__":
    main()
