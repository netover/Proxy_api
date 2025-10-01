"""
Função simples para teste de mutação
"""
from typing import List, Optional

def add_numbers(a: int, b: int) -> int:
    """Adiciona dois números"""
    return a + b

def multiply_numbers(a: int, b: int) -> int:
    """Multiplica dois números"""
    return a * b

def is_even(number: int) -> bool:
    """Verifica se um número é par"""
    return number % 2 == 0

def get_max(numbers: List[int]) -> Optional[int]:
    """Retorna o maior número de uma lista"""
    if not numbers:
        return None
    return max(numbers)

def calculate_average(numbers: List[int]) -> float:
    """Calcula a média de uma lista de números"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def is_palindrome(text: str) -> bool:
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() == text.lower()[::-1]

def count_vowels(text: str) -> int:
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)

def factorial(n: int) -> Optional[int]:
    """Calcula o fatorial de um número"""
    if n < 0:
        return None

    def _fact(k: int) -> int:
        if k <= 1:
            return 1
        return k * _fact(k - 1)

    return _fact(n)

def fibonacci(n: int) -> int:
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def is_prime(number: int) -> bool:
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True
