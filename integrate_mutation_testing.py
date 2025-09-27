#!/usr/bin/env python3
"""
Script de integração completa para testes de mutação
"""
import subprocess
import sys
import os
import json
import argparse
from pathlib import Path

class MutationTestingIntegration:
    def __init__(self, threshold=95.0):
        self.threshold = threshold
        self.results = {}
        self.integration_results = {}
        
    def setup_environment(self):
        """Configura o ambiente para testes de mutação"""
        print("🔧 Configurando ambiente para testes de mutação...")
        
        # Verificar se mutmut está instalado
        try:
            subprocess.run(["mutmut", "--version"], capture_output=True, check=True)
            print("✅ mutmut já está instalado")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("📦 Instalando mutmut...")
            subprocess.run(["pip", "install", "--break-system-packages", "mutmut"], check=True)
            print("✅ mutmut instalado com sucesso!")
        
        # Criar diretório de testes se não existir
        os.makedirs("tests_mutmut", exist_ok=True)
        
        # Copiar testes se necessário
        if not os.path.exists("tests_mutmut/test_simple.py"):
            if os.path.exists("test_simple_function.py"):
                subprocess.run(["cp", "test_simple_function.py", "tests_mutmut/test_simple.py"])
        
        print("✅ Ambiente configurado com sucesso!")
    
    def run_basic_mutation_tests(self):
        """Executa testes de mutação básicos"""
        print("\n🧬 Executando testes de mutação básicos...")
        
        try:
            result = subprocess.run([
                "python3", "run_mutation_tests.py",
                "--threshold", str(self.threshold),
                "--config", "simple_pyproject.toml",
                "--report", "basic_mutation_report.json"
            ], capture_output=True, text=True, check=True)
            
            print("✅ Testes básicos executados com sucesso!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro nos testes básicos: {e.stderr}")
            return False
    
    def run_expanded_mutation_tests(self):
        """Executa testes de mutação expandidos"""
        print("\n🧬 Executando testes de mutação expandidos...")
        
        try:
            result = subprocess.run([
                "python3", "run_expanded_mutation_tests.py",
                "--threshold", str(self.threshold - 5),  # Threshold mais baixo para expandidos
                "--config", "expanded_pyproject.toml",
                "--report", "expanded_mutation_report.json"
            ], capture_output=True, text=True, check=True)
            
            print("✅ Testes expandidos executados com sucesso!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro nos testes expandidos: {e.stderr}")
            return False
    
    def run_eliminate_mutation_tests(self):
        """Executa testes para eliminar mutações restantes"""
        print("\n🧬 Executando testes para eliminar mutações restantes...")
        
        try:
            result = subprocess.run([
                "python3", "run_eliminate_mutations.py",
                "--threshold", str(self.threshold),
                "--config", "simple_pyproject.toml",
                "--report", "eliminate_mutation_report.json",
                "--show-survived"
            ], capture_output=True, text=True, check=True)
            
            print("✅ Testes de eliminação executados com sucesso!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro nos testes de eliminação: {e.stderr}")
            return False
    
    def generate_integration_report(self):
        """Gera relatório de integração"""
        print("\n📊 Gerando relatório de integração...")
        
        reports = []
        report_files = [
            "basic_mutation_report.json",
            "expanded_mutation_report.json", 
            "eliminate_mutation_report.json"
        ]
        
        for report_file in report_files:
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r') as f:
                        report = json.load(f)
                        reports.append({
                            "file": report_file,
                            "data": report
                        })
                except Exception as e:
                    print(f"⚠️ Erro ao ler {report_file}: {e}")
        
        integration_report = {
            "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            "threshold": self.threshold,
            "reports": reports,
            "summary": self.generate_summary(reports)
        }
        
        with open("integration_mutation_report.json", 'w') as f:
            json.dump(integration_report, f, indent=2)
        
        print("✅ Relatório de integração gerado!")
        return integration_report
    
    def generate_summary(self, reports):
        """Gera resumo dos resultados"""
        summary = {
            "total_reports": len(reports),
            "passed_reports": 0,
            "average_detection_rate": 0,
            "best_detection_rate": 0,
            "worst_detection_rate": 100
        }
        
        detection_rates = []
        
        for report in reports:
            data = report["data"]
            if data.get("passed", False):
                summary["passed_reports"] += 1
            
            detection_rate = data.get("results", {}).get("detection_rate", 0)
            detection_rates.append(detection_rate)
            
            if detection_rate > summary["best_detection_rate"]:
                summary["best_detection_rate"] = detection_rate
            
            if detection_rate < summary["worst_detection_rate"]:
                summary["worst_detection_rate"] = detection_rate
        
        if detection_rates:
            summary["average_detection_rate"] = sum(detection_rates) / len(detection_rates)
        
        return summary
    
    def print_summary(self):
        """Imprime resumo dos resultados"""
        if os.path.exists("integration_mutation_report.json"):
            with open("integration_mutation_report.json", 'r') as f:
                report = json.load(f)
                summary = report.get("summary", {})
                
                print(f"\n📊 Resumo da Integração de Testes de Mutação:")
                print(f"   📈 Taxa média de detecção: {summary.get('average_detection_rate', 0):.1f}%")
                print(f"   🏆 Melhor taxa de detecção: {summary.get('best_detection_rate', 0):.1f}%")
                print(f"   📉 Pior taxa de detecção: {summary.get('worst_detection_rate', 0):.1f}%")
                print(f"   ✅ Relatórios que passaram: {summary.get('passed_reports', 0)}/{summary.get('total_reports', 0)}")
                print(f"   🎯 Threshold: {self.threshold}%")
    
    def run_integration(self):
        """Executa integração completa"""
        print("🚀 Iniciando integração completa de testes de mutação...")
        
        # Configurar ambiente
        self.setup_environment()
        
        # Executar testes
        basic_success = self.run_basic_mutation_tests()
        expanded_success = self.run_expanded_mutation_tests()
        eliminate_success = self.run_eliminate_mutation_tests()
        
        # Gerar relatório
        self.generate_integration_report()
        
        # Imprimir resumo
        self.print_summary()
        
        # Verificar se todos os testes passaram
        all_success = basic_success and expanded_success and eliminate_success
        
        if all_success:
            print("\n✅ Integração completa executada com sucesso!")
            return True
        else:
            print("\n❌ Alguns testes falharam na integração!")
            return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Integração completa de testes de mutação")
    parser.add_argument("--threshold", type=float, default=95.0,
                       help="Threshold mínimo de detecção (padrão: 95.0)")
    parser.add_argument("--basic-only", action="store_true",
                       help="Executa apenas testes básicos")
    parser.add_argument("--expanded-only", action="store_true",
                       help="Executa apenas testes expandidos")
    parser.add_argument("--eliminate-only", action="store_true",
                       help="Executa apenas testes de eliminação")
    
    args = parser.parse_args()
    
    # Criar instância da integração
    integration = MutationTestingIntegration(threshold=args.threshold)
    
    if args.basic_only:
        integration.setup_environment()
        success = integration.run_basic_mutation_tests()
    elif args.expanded_only:
        integration.setup_environment()
        success = integration.run_expanded_mutation_tests()
    elif args.eliminate_only:
        integration.setup_environment()
        success = integration.run_eliminate_mutation_tests()
    else:
        success = integration.run_integration()
    
    if success:
        print("🎉 Integração de testes de mutação concluída com sucesso!")
        sys.exit(0)
    else:
        print("💥 Integração de testes de mutação falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main()