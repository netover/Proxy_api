"""
Função simples para teste de mutação
"""

def add_numbers(a, b):
    """Adiciona dois números"""
    return a + b

def multiply_numbers(a, b):
    """Multiplica dois números"""
    return a * b

def is_even(number):
    """Verifica se um número é par"""
    return number % 2 == 0

def get_max(numbers):
    """Retorna o maior número de uma lista"""
    if not numbers:
        return None
    return max(numbers)

def calculate_average(numbers):
    """Calcula a média de uma lista de números"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def is_palindrome(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() == text.lower()[::-1]

def count_vowels(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)

def factorial(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def is_prime(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True