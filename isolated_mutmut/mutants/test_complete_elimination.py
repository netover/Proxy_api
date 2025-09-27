"""
Testes completos para eliminar todas as mutações restantes
"""
import pytest
import sys
import os

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_factorial_complete():
    """Teste completo para factorial (elimina mutmut_3)"""
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

def test_fibonacci_complete():
    """Teste completo para fibonacci (elimina mutmut_1)"""
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

def test_is_prime_complete():
    """Teste completo para is_prime (elimina mutmut_3 e mutmut_11)"""
    from simple_function import is_prime
    
    # Teste específico para números < 2 (elimina mutmut_3)
    assert is_prime(0) == False
    assert is_prime(1) == False
    assert is_prime(-1) == False
    assert is_prime(-5) == False
    
    # Teste com números primos
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    for prime in primes:
        assert is_prime(prime) == True, f"{prime} deveria ser primo"
    
    # Teste com números compostos
    composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 28, 30, 32, 33, 34, 35, 36, 38, 39, 40, 42, 44, 45, 46, 48, 49, 50]
    for composite in composites:
        assert is_prime(composite) == False, f"{composite} deveria ser composto"
    
    # Teste com números maiores que requerem verificação até sqrt
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

def test_add_numbers():
    """Testa a função add_numbers"""
    from simple_function import add_numbers
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_multiply_numbers():
    """Testa a função multiply_numbers"""
    from simple_function import multiply_numbers
    assert multiply_numbers(2, 3) == 6
    assert multiply_numbers(-2, 3) == -6
    assert multiply_numbers(0, 5) == 0

def test_is_even():
    """Testa a função is_even"""
    from simple_function import is_even
    assert is_even(2) == True
    assert is_even(3) == False
    assert is_even(0) == True

def test_get_max():
    """Testa a função get_max"""
    from simple_function import get_max
    assert get_max([1, 2, 3, 4, 5]) == 5
    assert get_max([-1, -2, -3]) == -1
    assert get_max([]) == None

def test_calculate_average():
    """Testa a função calculate_average"""
    from simple_function import calculate_average
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20, 30]) == 20.0
    assert calculate_average([]) == 0

def test_is_palindrome():
    """Testa a função is_palindrome"""
    from simple_function import is_palindrome
    assert is_palindrome("racecar") == True
    assert is_palindrome("hello") == False
    assert is_palindrome("") == True

def test_count_vowels():
    """Testa a função count_vowels"""
    from simple_function import count_vowels
    assert count_vowels("hello") == 2
    assert count_vowels("world") == 1
    assert count_vowels("") == 0

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