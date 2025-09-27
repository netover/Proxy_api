#!/usr/bin/env python3
"""
Script para executar testes específicos para eliminar mutações restantes
"""
import subprocess
import sys
import os
import json
import re
from pathlib import Path

class EliminateMutationsRunner:
    def __init__(self, threshold=95.0):
        self.threshold = threshold
        self.results = {}
        
    def run_mutation_tests(self, config_file="pyproject.toml"):
        """Executa os testes de mutação com foco em eliminar mutações restantes"""
        print(f"🎯 Executando testes específicos para eliminar mutações restantes...")
        
        # Copiar configuração para teste isolado
        if os.path.exists("simple_pyproject.toml"):
            subprocess.run(["cp", "simple_pyproject.toml", "pyproject.toml"], check=True)
        
        try:
            # Executar mutmut
            result = subprocess.run(
                ["mutmut", "run"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                print(f"❌ Erro ao executar mutmut: {result.stderr}")
                return False
                
            # Parse dos resultados
            self.parse_results()
            
            # Verificar threshold
            return self.check_threshold()
            
        except Exception as e:
            print(f"❌ Erro ao executar testes de mutação: {e}")
            return False
    
    def parse_results(self):
        """Parse dos resultados do mutmut"""
        try:
            # Executar mutmut results para obter estatísticas
            result = subprocess.run(
                ["mutmut", "results"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.results["survived"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            else:
                self.results["survived"] = 0
                
            # Executar mutmut show para obter estatísticas detalhadas
            result = subprocess.run(
                ["mutmut", "show"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Parse das estatísticas do output
                output = result.stdout
                
                # Extrair números das estatísticas
                killed_match = re.search(r'🎉 (\d+)', output)
                survived_match = re.search(r'🙁 (\d+)', output)
                timeout_match = re.search(r'⏰ (\d+)', output)
                error_match = re.search(r'🤔 (\d+)', output)
                silenced_match = re.search(r'🔇 (\d+)', output)
                
                self.results["killed"] = int(killed_match.group(1)) if killed_match else 0
                self.results["survived"] = int(survived_match.group(1)) if survived_match else 0
                self.results["timeout"] = int(timeout_match.group(1)) if timeout_match else 0
                self.results["error"] = int(error_match.group(1)) if error_match else 0
                self.results["silenced"] = int(silenced_match.group(1)) if silenced_match else 0
                
                total = (self.results["killed"] + self.results["survived"] + 
                        self.results["timeout"] + self.results["error"] + 
                        self.results["silenced"])
                
                self.results["total"] = total
                self.results["detection_rate"] = (self.results["killed"] / total * 100) if total > 0 else 0
                
        except Exception as e:
            print(f"⚠️ Erro ao parsear resultados: {e}")
            self.results = {
                "killed": 0,
                "survived": 0,
                "timeout": 0,
                "error": 0,
                "silenced": 0,
                "total": 0,
                "detection_rate": 0
            }
    
    def check_threshold(self):
        """Verifica se o threshold foi atingido"""
        detection_rate = self.results.get("detection_rate", 0)
        
        print(f"\n📊 Resultados dos Testes de Mutação (Eliminação):")
        print(f"   🎉 Mutações mortas: {self.results.get('killed', 0)}")
        print(f"   🙁 Mutações sobreviventes: {self.results.get('survived', 0)}")
        print(f"   ⏰ Timeouts: {self.results.get('timeout', 0)}")
        print(f"   🤔 Erros: {self.results.get('error', 0)}")
        print(f"   🔇 Silenciadas: {self.results.get('silenced', 0)}")
        print(f"   📈 Taxa de detecção: {detection_rate:.1f}%")
        print(f"   🎯 Threshold mínimo: {self.threshold}%")
        
        if detection_rate >= self.threshold:
            print(f"✅ Threshold atingido! ({detection_rate:.1f}% >= {self.threshold}%)")
            return True
        else:
            print(f"❌ Threshold não atingido! ({detection_rate:.1f}% < {self.threshold}%)")
            return False
    
    def show_survived_mutations(self):
        """Mostra as mutações que ainda sobrevivem"""
        try:
            result = subprocess.run(
                ["mutmut", "results"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"\n🔍 Mutações que ainda sobrevivem:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"   - {line.strip()}")
                        
                        # Mostrar detalhes da mutação
                        mutation_name = line.strip()
                        if mutation_name:
                            detail_result = subprocess.run(
                                ["mutmut", "show", mutation_name],
                                capture_output=True,
                                text=True,
                                cwd=os.getcwd()
                            )
                            
                            if detail_result.returncode == 0:
                                print(f"     Detalhes: {detail_result.stdout.strip()}")
            else:
                print("✅ Nenhuma mutação sobrevive!")
                
        except Exception as e:
            print(f"⚠️ Erro ao obter mutações sobreviventes: {e}")
    
    def generate_report(self, output_file="eliminate_mutations_report.json"):
        """Gera relatório dos testes de mutação para eliminação"""
        report = {
            "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            "threshold": self.threshold,
            "results": self.results,
            "passed": self.results.get("detection_rate", 0) >= self.threshold,
            "focus": "eliminate_remaining_mutations"
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Relatório de eliminação salvo em: {output_file}")
        return report

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Executar testes específicos para eliminar mutações restantes")
    parser.add_argument("--threshold", type=float, default=95.0, 
                       help="Threshold mínimo de detecção (padrão: 95.0)")
    parser.add_argument("--config", type=str, default="simple_pyproject.toml",
                       help="Arquivo de configuração (padrão: simple_pyproject.toml)")
    parser.add_argument("--report", type=str, default="eliminate_mutations_report.json",
                       help="Arquivo de relatório (padrão: eliminate_mutations_report.json)")
    parser.add_argument("--show-survived", action="store_true",
                       help="Mostrar mutações que ainda sobrevivem")
    
    args = parser.parse_args()
    
    # Verificar se mutmut está instalado
    try:
        subprocess.run(["mutmut", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ mutmut não está instalado. Instale com: pip install mutmut")
        sys.exit(1)
    
    # Executar testes de mutação para eliminação
    runner = EliminateMutationsRunner(threshold=args.threshold)
    
    if runner.run_mutation_tests(config_file=args.config):
        print("✅ Testes de mutação passaram no threshold!")
        if args.show_survived:
            runner.show_survived_mutations()
        runner.generate_report(args.report)
        sys.exit(0)
    else:
        print("❌ Testes de mutação falharam no threshold!")
        if args.show_survived:
            runner.show_survived_mutations()
        runner.generate_report(args.report)
        sys.exit(1)

if __name__ == "__main__":
    main()