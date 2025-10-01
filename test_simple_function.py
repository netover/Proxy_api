"""
Testes para a função simples
"""
from simple_function import (
    add_numbers, multiply_numbers, is_even, get_max, calculate_average,
    is_palindrome, count_vowels, factorial, fibonacci, is_prime
)

def test_add_numbers() -> None:
    """Testa a função add_numbers"""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_multiply_numbers() -> None:
    """Testa a função multiply_numbers"""
    assert multiply_numbers(2, 3) == 6
    assert multiply_numbers(-2, 3) == -6
    assert multiply_numbers(0, 5) == 0

def test_is_even() -> None:
    """Testa a função is_even"""
    assert is_even(2) is True
    assert is_even(3) is False
    assert is_even(0) is True

def test_get_max() -> None:
    """Testa a função get_max"""
    assert get_max([1, 2, 3, 4, 5]) == 5
    assert get_max([-1, -2, -3]) == -1
    assert get_max([]) is None

def test_calculate_average() -> None:
    """Testa a função calculate_average"""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20, 30]) == 20.0
    assert calculate_average([]) == 0

def test_is_palindrome() -> None:
    """Testa a função is_palindrome"""
    assert is_palindrome("racecar") is True
    assert is_palindrome("hello") is False
    assert is_palindrome("") is True

def test_count_vowels() -> None:
    """Testa a função count_vowels"""
    assert count_vowels("hello") == 2
    assert count_vowels("world") == 1
    assert count_vowels("") == 0
    # Test with uppercase vowels
    assert count_vowels("AEIOU") == 5
    # Test with a word without vowels
    assert count_vowels("Rhythm") == 0
    # Test with a word containing non-vowel characters
    assert count_vowels("Xylophone") == 3

def test_factorial() -> None:
    """Testa a função factorial"""
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(-1) is None

def test_fibonacci() -> None:
    """Testa a função fibonacci"""
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55

def test_is_prime() -> None:
    """Testa a função is_prime"""
    assert is_prime(2) is True
    assert is_prime(3) is True
    assert is_prime(4) is False
    assert is_prime(1) is False
