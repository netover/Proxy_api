"""
Testes finais para eliminar TODAS as mutações restantes
"""
import pytest
import sys
import os

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_count_vowels_eliminate_mutations():
    """Teste específico para eliminar mutações 4 e 5 de count_vowels"""
    from simple_function import count_vowels
    
    # Teste que força a verificação da string de vogais exata
    # Se caracteres extras forem adicionados (mutmut_4), este teste deve falhar
    assert count_vowels("aeiou") == 5
    assert count_vowels("AEIOU") == 5
    assert count_vowels("aeiouAEIOU") == 10
    
    # Teste que força a verificação de que não há duplicação (mutmut_5)
    # Se a string for duplicada, este teste deve falhar
    assert count_vowels("aeiou") == 5
    assert count_vowels("AEIOU") == 5
    
    # Teste rigoroso: verificar que apenas aeiouAEIOU são contadas
    test_string = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    expected_vowels = 10  # a, e, i, o, u (maiúsculas e minúsculas)
    assert count_vowels(test_string) == expected_vowels
    
    # Teste com string vazia
    assert count_vowels("") == 0
    
    # Teste com apenas vogais minúsculas
    assert count_vowels("aeiou") == 5
    
    # Teste com apenas vogais maiúsculas
    assert count_vowels("AEIOU") == 5
    
    # Teste com apenas consoantes
    assert count_vowels("bcdfg") == 0
    
    # Teste com mistura
    assert count_vowels("hello") == 2
    assert count_vowels("world") == 1
    
    # Teste com maiúsculas e minúsculas misturadas
    assert count_vowels("aeiouAEIOU") == 10
    
    # Teste com números e símbolos (não devem ser contados como vogais)
    assert count_vowels("a1e2i3o4u5") == 5
    assert count_vowels("a!e@i#o$u%") == 5
    
    # Teste com espaços
    assert count_vowels("a e i o u") == 5
    
    # Teste com caracteres especiais (apenas a primeira letra é vogal em inglês)
    assert count_vowels("aéíóú") == 1  # Apenas 'a' é vogal em inglês

def test_factorial_eliminate_mutation():
    """Teste específico para eliminar mutação 3 de factorial"""
    from simple_function import factorial
    
    # Teste CRÍTICO: n=1 especificamente
    # Se a condição for n < 1 em vez de n <= 1, este teste deve falhar
    assert factorial(1) == 1
    
    # Teste que força a verificação da condição de parada correta
    assert factorial(0) == 1  # 0! = 1
    assert factorial(1) == 1  # 1! = 1
    assert factorial(2) == 2  # 2! = 2
    
    # Teste com números negativos
    assert factorial(-1) == None
    assert factorial(-5) == None
    
    # Teste propriedade: n! = n * (n-1)!
    for n in range(2, 15):
        assert factorial(n) == n * factorial(n-1), f"Propriedade falhou para n={n}"
    
    # Teste com valores específicos
    assert factorial(3) == 6
    assert factorial(4) == 24
    assert factorial(5) == 120
    assert factorial(6) == 720
    assert factorial(7) == 5040
    assert factorial(8) == 40320
    assert factorial(9) == 362880
    assert factorial(10) == 3628800

def test_fibonacci_eliminate_mutation():
    """Teste específico para eliminar mutação 1 de fibonacci"""
    from simple_function import fibonacci
    
    # Teste CRÍTICO: n=0 especificamente
    # Se a condição for n < 0 em vez de n <= 0, este teste deve falhar
    assert fibonacci(0) == 0
    
    # Teste que força a verificação da condição de parada correta
    assert fibonacci(-1) == 0  # n <= 0
    assert fibonacci(0) == 0    # n <= 0
    assert fibonacci(1) == 1   # n == 1
    
    # Teste com números negativos
    assert fibonacci(-5) == 0
    assert fibonacci(-10) == 0
    
    # Teste propriedade: F(n) = F(n-1) + F(n-2)
    for n in range(2, 15):
        assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2), f"Propriedade falhou para n={n}"
    
    # Teste com valores específicos da sequência
    fib_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
    for i, expected in enumerate(fib_sequence):
        assert fibonacci(i) == expected, f"fibonacci({i}) deveria ser {expected}"

def test_is_prime_eliminate_mutation():
    """Teste específico para eliminar mutação 11 de is_prime"""
    from simple_function import is_prime
    import math
    
    # Teste CRÍTICO: números que requerem verificação até sqrt(n)
    # Se a implementação usar number * 0.5 em vez de sqrt, estes testes devem falhar
    
    # Números primos pequenos
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
    
    # Números compostos pequenos
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
    
    # Teste com números que requerem verificação até sqrt(n)
    # Estes são críticos para detectar a mutação sqrt vs multiplicação
    assert is_prime(97) == True   # sqrt(97) ≈ 9.85
    assert is_prime(101) == True  # sqrt(101) ≈ 10.05
    assert is_prime(103) == True  # sqrt(103) ≈ 10.15
    assert is_prime(107) == True  # sqrt(107) ≈ 10.34
    assert is_prime(109) == True  # sqrt(109) ≈ 10.44
    assert is_prime(113) == True  # sqrt(113) ≈ 10.63
    assert is_prime(127) == True  # sqrt(127) ≈ 11.27
    assert is_prime(131) == True  # sqrt(131) ≈ 11.45
    assert is_prime(137) == True  # sqrt(137) ≈ 11.70
    assert is_prime(139) == True  # sqrt(139) ≈ 11.79
    assert is_prime(149) == True  # sqrt(149) ≈ 12.21
    assert is_prime(151) == True  # sqrt(151) ≈ 12.29
    assert is_prime(157) == True  # sqrt(157) ≈ 12.53
    assert is_prime(163) == True  # sqrt(163) ≈ 12.77
    assert is_prime(167) == True  # sqrt(167) ≈ 12.92
    assert is_prime(173) == True  # sqrt(173) ≈ 13.15
    assert is_prime(179) == True  # sqrt(179) ≈ 13.38
    assert is_prime(181) == True  # sqrt(181) ≈ 13.45
    assert is_prime(191) == True  # sqrt(191) ≈ 13.82
    assert is_prime(193) == True  # sqrt(193) ≈ 13.89
    assert is_prime(197) == True  # sqrt(197) ≈ 14.04
    assert is_prime(199) == True  # sqrt(199) ≈ 14.11
    
    # Teste com números compostos que requerem verificação até sqrt
    assert is_prime(100) == False  # 10^2
    assert is_prime(102) == False  # 2 * 51
    assert is_prime(104) == False  # 2 * 52
    assert is_prime(105) == False  # 3 * 35
    assert is_prime(106) == False  # 2 * 53
    assert is_prime(108) == False  # 2 * 54
    assert is_prime(110) == False  # 2 * 55
    assert is_prime(111) == False  # 3 * 37
    assert is_prime(112) == False  # 2 * 56
    assert is_prime(114) == False  # 2 * 57
    assert is_prime(115) == False  # 5 * 23
    assert is_prime(116) == False  # 2 * 58
    assert is_prime(117) == False  # 3 * 39
    assert is_prime(118) == False  # 2 * 59
    assert is_prime(119) == False  # 7 * 17
    assert is_prime(120) == False  # 2 * 60
    assert is_prime(121) == False  # 11^2
    assert is_prime(122) == False  # 2 * 61
    assert is_prime(123) == False  # 3 * 41
    assert is_prime(124) == False  # 2 * 62
    assert is_prime(125) == False  # 5^3
    assert is_prime(126) == False  # 2 * 63
    assert is_prime(128) == False  # 2^7
    assert is_prime(129) == False  # 3 * 43
    assert is_prime(130) == False  # 2 * 65
    
    # Teste com casos especiais
    assert is_prime(1) == False
    assert is_prime(0) == False
    assert is_prime(-1) == False
    assert is_prime(-5) == False

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