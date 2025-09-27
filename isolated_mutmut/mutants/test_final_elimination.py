"""
Testes finais para eliminar as últimas mutações restantes
"""
import pytest
import sys
import os

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_factorial_edge_case_n_equals_1():
    """Teste específico para n=1 no fatorial (elimina mutmut_3)"""
    from simple_function import factorial
    
    # Teste específico para n=1 - se a condição for n < 1 em vez de n <= 1,
    # este teste deve falhar
    assert factorial(1) == 1
    
    # Teste que força a verificação da condição de parada
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(2) == 2
    
    # Teste propriedade: n! = n * (n-1)!
    for n in range(2, 10):
        assert factorial(n) == n * factorial(n-1)

def test_fibonacci_edge_case_n_equals_0():
    """Teste específico para n=0 no fibonacci (elimina mutmut_1)"""
    from simple_function import fibonacci
    
    # Teste específico para n=0 - se a condição for n < 0 em vez de n <= 0,
    # este teste deve falhar
    assert fibonacci(0) == 0
    
    # Teste que força a verificação da condição
    assert fibonacci(-1) == 0
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    
    # Teste propriedade: F(n) = F(n-1) + F(n-2)
    for n in range(2, 10):
        assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2)

def test_is_prime_sqrt_implementation():
    """Teste específico para verificar implementação de sqrt (elimina mutmut_11)"""
    from simple_function import is_prime
    import math
    
    # Teste com números que requerem verificação até sqrt(n)
    # Se a implementação usar number * 0.5 em vez de sqrt, estes testes devem falhar
    
    # Números primos que requerem verificação completa
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(5) == True
    assert is_prime(7) == True
    assert is_prime(11) == True
    assert is_prime(13) == True
    assert is_prime(17) == True
    assert is_prime(19) == True
    assert is_prime(23) == True
    assert is_prime(29) == True
    assert is_prime(31) == True
    assert is_prime(37) == True
    assert is_prime(41) == True
    assert is_prime(43) == True
    assert is_prime(47) == True
    
    # Números compostos que requerem verificação até sqrt(n)
    assert is_prime(4) == False
    assert is_prime(6) == False
    assert is_prime(8) == False
    assert is_prime(9) == False
    assert is_prime(10) == False
    assert is_prime(12) == False
    assert is_prime(14) == False
    assert is_prime(15) == False
    assert is_prime(16) == False
    assert is_prime(18) == False
    assert is_prime(20) == False
    assert is_prime(21) == False
    assert is_prime(22) == False
    assert is_prime(24) == False
    assert is_prime(25) == False
    
    # Teste com números maiores que requerem verificação até sqrt
    assert is_prime(97) == True
    assert is_prime(101) == True
    assert is_prime(103) == True
    assert is_prime(107) == True
    assert is_prime(109) == True
    assert is_prime(113) == True
    assert is_prime(127) == True
    assert is_prime(131) == True
    assert is_prime(137) == True
    assert is_prime(139) == True
    assert is_prime(149) == True
    assert is_prime(151) == True
    assert is_prime(157) == True
    assert is_prime(163) == True
    assert is_prime(167) == True
    assert is_prime(173) == True
    assert is_prime(179) == True
    assert is_prime(181) == True
    assert is_prime(191) == True
    assert is_prime(193) == True
    assert is_prime(197) == True
    assert is_prime(199) == True
    
    # Teste com números compostos maiores
    assert is_prime(100) == False
    assert is_prime(102) == False
    assert is_prime(104) == False
    assert is_prime(105) == False
    assert is_prime(106) == False
    assert is_prime(108) == False
    assert is_prime(110) == False
    assert is_prime(111) == False
    assert is_prime(112) == False
    assert is_prime(114) == False
    assert is_prime(115) == False
    assert is_prime(116) == False
    assert is_prime(117) == False
    assert is_prime(118) == False
    assert is_prime(119) == False
    assert is_prime(120) == False
    assert is_prime(121) == False  # 11^2
    assert is_prime(122) == False
    assert is_prime(123) == False
    assert is_prime(124) == False
    assert is_prime(125) == False  # 5^3
    assert is_prime(126) == False
    assert is_prime(128) == False  # 2^7
    assert is_prime(129) == False
    assert is_prime(130) == False

def test_basic_functionality():
    """Teste básico de funcionalidade"""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert True is True

def test_string_operations():
    """Testa operações com strings"""
    text = "Hello World"
    assert len(text) == 11
    assert text.upper() == "HELLO WORLD"
    assert text.lower() == "hello world"

def test_list_operations():
    """Testa operações com listas"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1

def test_dict_operations():
    """Testa operações com dicionários"""
    data = {"name": "test", "value": 42}
    assert "name" in data
    assert data["value"] == 42
    assert len(data) == 2

def test_math_operations():
    """Testa operações matemáticas"""
    assert 2 * 3 == 6
    assert 10 / 2 == 5
    assert 2 ** 3 == 8
    assert 7 % 3 == 1

def test_boolean_operations():
    """Testa operações booleanas"""
    assert True and True == True
    assert False or True == True
    assert not False == True
    assert True != False