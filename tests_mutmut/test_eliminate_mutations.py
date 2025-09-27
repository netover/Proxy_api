"""
Testes específicos para eliminar mutações restantes
"""
import pytest
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_count_vowels_implementation_specific():
    """Teste específico para eliminar mutação em count_vowels"""
    try:
        from simple_function import count_vowels
        
        # Teste que verifica especificamente a implementação
        # para detectar se caracteres extras foram adicionados à string de vogais
        
        # Teste com string que contém apenas vogais
        assert count_vowels("aeiou") == 5
        
        # Teste com string que contém apenas consoantes
        assert count_vowels("bcdfg") == 0
        
        # Teste com string vazia
        assert count_vowels("") == 0
        
        # Teste com maiúsculas e minúsculas
        assert count_vowels("AEIOU") == 5
        assert count_vowels("aeiou") == 5
        assert count_vowels("aeiouAEIOU") == 10
        
        # Teste com números e símbolos (não devem ser contados como vogais)
        assert count_vowels("a1e2i3o4u5") == 5
        assert count_vowels("a!e@i#o$u%") == 5
        
        # Teste com espaços
        assert count_vowels("a e i o u") == 5
        
        # Teste com caracteres especiais
        assert count_vowels("aéíóú") == 5  # Acentos não são vogais em inglês
        
        # Teste rigoroso: verificar que apenas aeiouAEIOU são contadas
        test_string = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        expected_vowels = 10  # a, e, i, o, u (maiúsculas e minúsculas)
        assert count_vowels(test_string) == expected_vowels
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")

def test_factorial_implementation_specific():
    """Teste específico para eliminar mutação em factorial"""
    try:
        from simple_function import factorial
        
        # Teste específico para n=1 (caso que falhou na mutação)
        assert factorial(1) == 1
        
        # Teste que verifica a condição de parada correta
        # Se n <= 1, deve retornar 1
        assert factorial(0) == 1
        assert factorial(1) == 1
        
        # Teste com números negativos
        assert factorial(-1) == None
        assert factorial(-5) == None
        
        # Teste propriedade: n! = n * (n-1)!
        for n in range(2, 10):
            assert factorial(n) == n * factorial(n-1)
        
        # Teste específico para verificar a condição de parada
        # A mutação mudou "n <= 1" para "n < 1", então testamos n=1 especificamente
        assert factorial(1) == 1
        
        # Teste com valores específicos
        assert factorial(2) == 2
        assert factorial(3) == 6
        assert factorial(4) == 24
        assert factorial(5) == 120
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")

def test_fibonacci_implementation_specific():
    """Teste específico para eliminar mutação em fibonacci"""
    try:
        from simple_function import fibonacci
        
        # Teste com n=0
        assert fibonacci(0) == 0
        
        # Teste com n=1
        assert fibonacci(1) == 1
        
        # Teste com n=2
        assert fibonacci(2) == 1
        
        # Teste com n=3
        assert fibonacci(3) == 2
        
        # Teste com n=4
        assert fibonacci(4) == 3
        
        # Teste com n=5
        assert fibonacci(5) == 5
        
        # Teste com números negativos
        assert fibonacci(-1) == 0
        assert fibonacci(-5) == 0
        
        # Teste propriedade: F(n) = F(n-1) + F(n-2)
        for n in range(2, 10):
            assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2)
        
        # Teste com valores específicos
        assert fibonacci(6) == 8
        assert fibonacci(7) == 13
        assert fibonacci(8) == 21
        assert fibonacci(9) == 34
        assert fibonacci(10) == 55
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")

def test_is_prime_implementation_specific():
    """Teste específico para eliminar mutação em is_prime"""
    try:
        from simple_function import is_prime
        
        # Teste com números primos
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for prime in primes:
            assert is_prime(prime) == True, f"{prime} deveria ser primo"
        
        # Teste com números compostos
        composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25]
        for composite in composites:
            assert is_prime(composite) == False, f"{composite} deveria ser composto"
        
        # Teste com casos especiais
        assert is_prime(1) == False
        assert is_prime(0) == False
        assert is_prime(-1) == False
        assert is_prime(-5) == False
        
        # Teste com números maiores
        assert is_prime(97) == True
        assert is_prime(101) == True
        assert is_prime(103) == True
        assert is_prime(107) == True
        assert is_prime(109) == True
        
        # Teste com números compostos maiores
        assert is_prime(100) == False
        assert is_prime(102) == False
        assert is_prime(104) == False
        assert is_prime(105) == False
        assert is_prime(106) == False
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")

def test_edge_cases_rigorous():
    """Testes rigorosos para casos extremos"""
    try:
        from simple_function import count_vowels, factorial, fibonacci, is_prime
        
        # Teste rigoroso para count_vowels
        # Verificar que apenas vogais são contadas
        assert count_vowels("aeiouAEIOU") == 10
        assert count_vowels("bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ") == 0
        
        # Teste rigoroso para factorial
        # Verificar que a condição de parada está correta
        assert factorial(1) == 1  # Caso específico que falhou na mutação
        
        # Teste rigoroso para fibonacci
        # Verificar que a sequência está correta
        fib_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        for i, expected in enumerate(fib_sequence):
            assert fibonacci(i) == expected, f"fibonacci({i}) deveria ser {expected}"
        
        # Teste rigoroso para is_prime
        # Verificar que a implementação está correta
        assert is_prime(2) == True  # Menor número primo
        assert is_prime(3) == True  # Segundo número primo
        assert is_prime(4) == False  # Menor número composto
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")

def test_property_based_rigorous():
    """Testes baseados em propriedades rigorosos"""
    try:
        from simple_function import factorial, fibonacci, is_prime
        
        # Propriedade do fatorial: n! = n * (n-1)!
        for n in range(2, 15):
            assert factorial(n) == n * factorial(n-1), f"Propriedade falhou para n={n}"
        
        # Propriedade da sequência de Fibonacci: F(n) = F(n-1) + F(n-2)
        for n in range(2, 15):
            assert fibonacci(n) == fibonacci(n-1) + fibonacci(n-2), f"Propriedade falhou para n={n}"
        
        # Propriedade dos números primos: se n é primo, não é divisível por nenhum número entre 2 e sqrt(n)
        for n in range(2, 100):
            if is_prime(n):
                for i in range(2, int(n**0.5) + 1):
                    assert n % i != 0, f"{n} é primo mas é divisível por {i}"
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")

def test_implementation_details():
    """Testes que verificam detalhes específicos da implementação"""
    try:
        from simple_function import count_vowels, factorial, fibonacci, is_prime
        
        # Teste que força a verificação da string de vogais
        # Se a string de vogais for modificada, estes testes devem falhar
        assert count_vowels("aeiou") == 5
        assert count_vowels("AEIOU") == 5
        assert count_vowels("aeiouAEIOU") == 10
        
        # Teste que força a verificação da condição de parada do fatorial
        # Se a condição for modificada, estes testes devem falhar
        assert factorial(1) == 1
        assert factorial(0) == 1
        
        # Teste que força a verificação da sequência de Fibonacci
        # Se a implementação for modificada, estes testes devem falhar
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
        assert fibonacci(2) == 1
        
        # Teste que força a verificação da implementação de is_prime
        # Se a implementação for modificada, estes testes devem falhar
        assert is_prime(2) == True
        assert is_prime(4) == False
        assert is_prime(1) == False
        
    except ImportError:
        pytest.skip("simple_function não pode ser importado")