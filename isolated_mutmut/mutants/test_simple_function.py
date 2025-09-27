"""
Testes melhorados para a função simples baseados nos resultados dos testes de mutação
"""
import pytest
from simple_function import (
    add_numbers, multiply_numbers, is_even, get_max, calculate_average,
    is_palindrome, count_vowels, factorial, fibonacci, is_prime
)

def test_add_numbers():
    """Testa a função add_numbers"""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0
    assert add_numbers(-5, -3) == -8
    assert add_numbers(0.5, 0.5) == 1.0

def test_multiply_numbers():
    """Testa a função multiply_numbers"""
    assert multiply_numbers(2, 3) == 6
    assert multiply_numbers(-2, 3) == -6
    assert multiply_numbers(0, 5) == 0
    assert multiply_numbers(-3, -4) == 12
    assert multiply_numbers(0.5, 4) == 2.0

def test_is_even():
    """Testa a função is_even"""
    assert is_even(2) == True
    assert is_even(3) == False
    assert is_even(0) == True
    assert is_even(-2) == True
    assert is_even(-3) == False

def test_get_max():
    """Testa a função get_max"""
    assert get_max([1, 2, 3, 4, 5]) == 5
    assert get_max([-1, -2, -3]) == -1
    assert get_max([]) == None
    assert get_max([5]) == 5
    assert get_max([-5, -1, -10]) == -1

def test_calculate_average():
    """Testa a função calculate_average"""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20, 30]) == 20.0
    assert calculate_average([]) == 0
    assert calculate_average([5]) == 5.0
    assert calculate_average([-1, 0, 1]) == 0.0

def test_is_palindrome():
    """Testa a função is_palindrome"""
    assert is_palindrome("racecar") == True
    assert is_palindrome("hello") == False
    assert is_palindrome("") == True
    assert is_palindrome("a") == True
    assert is_palindrome("Aa") == True
    assert is_palindrome("RaceCar") == True

def test_count_vowels():
    """Testa a função count_vowels - versão melhorada"""
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
    
    # Teste com números e símbolos
    assert count_vowels("a1e2i3o4u5") == 5
    
    # Teste com espaços
    assert count_vowels("a e i o u") == 5

def test_factorial():
    """Testa a função factorial - versão melhorada"""
    # Teste com n=0
    assert factorial(0) == 1
    
    # Teste com n=1 (caso específico que falhou na mutação)
    assert factorial(1) == 1
    
    # Teste com n=5
    assert factorial(5) == 120
    
    # Teste com números negativos
    assert factorial(-1) == None
    assert factorial(-5) == None
    
    # Teste propriedade: n! = n * (n-1)!
    for n in range(2, 10):
        assert factorial(n) == n * factorial(n-1)

def test_fibonacci():
    """Testa a função fibonacci - versão melhorada"""
    # Teste com n=0
    assert fibonacci(0) == 0
    
    # Teste com n=1
    assert fibonacci(1) == 1
    
    # Teste com n=5
    assert fibonacci(5) == 5
    
    # Teste com n=10
    assert fibonacci(10) == 55
    
    # Teste com números negativos
    assert fibonacci(-1) == 0
    assert fibonacci(-5) == 0
    
    # Teste propriedade: F(n) = F(n-1) + F(n-2)
    for n in range(2, 10):
        assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2)

def test_is_prime():
    """Testa a função is_prime - versão melhorada"""
    # Teste com números primos
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(5) == True
    assert is_prime(7) == True
    assert is_prime(11) == True
    assert is_prime(13) == True
    
    # Teste com números compostos
    assert is_prime(4) == False
    assert is_prime(6) == False
    assert is_prime(8) == False
    assert is_prime(9) == False
    assert is_prime(10) == False
    
    # Teste com casos especiais
    assert is_prime(1) == False
    assert is_prime(0) == False
    assert is_prime(-1) == False
    assert is_prime(-5) == False
    
    # Teste com números maiores
    assert is_prime(17) == True
    assert is_prime(19) == True
    assert is_prime(23) == True
    assert is_prime(25) == False
    assert is_prime(29) == True

def test_edge_cases():
    """Testa casos extremos para todas as funções"""
    # Teste com valores muito grandes
    assert add_numbers(1000000, 1000000) == 2000000
    
    # Teste com valores decimais
    assert abs(multiply_numbers(0.1, 0.1) - 0.01) < 1e-10
    
    # Teste com listas grandes
    large_list = list(range(1000))
    assert get_max(large_list) == 999
    assert calculate_average(large_list) == 499.5
    
    # Teste com strings longas
    long_string = "a" * 1000
    assert count_vowels(long_string) == 1000
    
    # Teste com palíndromos longos
    long_palindrome = "a" * 1000 + "b" + "a" * 1000
    assert is_palindrome(long_palindrome) == True

def test_property_based_tests():
    """Testes baseados em propriedades"""
    # Propriedade do fatorial
    for n in range(2, 10):
        assert factorial(n) == n * factorial(n-1)
    
    # Propriedade da sequência de Fibonacci
    for n in range(2, 10):
        assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2)
    
    # Propriedade da soma
    for a in range(-10, 10):
        for b in range(-10, 10):
            assert add_numbers(a, b) == a + b
    
    # Propriedade da multiplicação
    for a in range(-10, 10):
        for b in range(-10, 10):
            assert multiply_numbers(a, b) == a * b