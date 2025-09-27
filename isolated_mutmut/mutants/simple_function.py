"""
Função simples para teste de mutação
"""
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result

def x_add_numbers__mutmut_orig(a, b):
    """Adiciona dois números"""
    return a + b

def x_add_numbers__mutmut_1(a, b):
    """Adiciona dois números"""
    return a - b

x_add_numbers__mutmut_mutants : ClassVar[MutantDict] = {
'x_add_numbers__mutmut_1': x_add_numbers__mutmut_1
}

def add_numbers(*args, **kwargs):
    result = _mutmut_trampoline(x_add_numbers__mutmut_orig, x_add_numbers__mutmut_mutants, args, kwargs)
    return result 

add_numbers.__signature__ = _mutmut_signature(x_add_numbers__mutmut_orig)
x_add_numbers__mutmut_orig.__name__ = 'x_add_numbers'

def x_multiply_numbers__mutmut_orig(a, b):
    """Multiplica dois números"""
    return a * b

def x_multiply_numbers__mutmut_1(a, b):
    """Multiplica dois números"""
    return a / b

x_multiply_numbers__mutmut_mutants : ClassVar[MutantDict] = {
'x_multiply_numbers__mutmut_1': x_multiply_numbers__mutmut_1
}

def multiply_numbers(*args, **kwargs):
    result = _mutmut_trampoline(x_multiply_numbers__mutmut_orig, x_multiply_numbers__mutmut_mutants, args, kwargs)
    return result 

multiply_numbers.__signature__ = _mutmut_signature(x_multiply_numbers__mutmut_orig)
x_multiply_numbers__mutmut_orig.__name__ = 'x_multiply_numbers'

def x_is_even__mutmut_orig(number):
    """Verifica se um número é par"""
    return number % 2 == 0

def x_is_even__mutmut_1(number):
    """Verifica se um número é par"""
    return number / 2 == 0

def x_is_even__mutmut_2(number):
    """Verifica se um número é par"""
    return number % 3 == 0

def x_is_even__mutmut_3(number):
    """Verifica se um número é par"""
    return number % 2 != 0

def x_is_even__mutmut_4(number):
    """Verifica se um número é par"""
    return number % 2 == 1

x_is_even__mutmut_mutants : ClassVar[MutantDict] = {
'x_is_even__mutmut_1': x_is_even__mutmut_1, 
    'x_is_even__mutmut_2': x_is_even__mutmut_2, 
    'x_is_even__mutmut_3': x_is_even__mutmut_3, 
    'x_is_even__mutmut_4': x_is_even__mutmut_4
}

def is_even(*args, **kwargs):
    result = _mutmut_trampoline(x_is_even__mutmut_orig, x_is_even__mutmut_mutants, args, kwargs)
    return result 

is_even.__signature__ = _mutmut_signature(x_is_even__mutmut_orig)
x_is_even__mutmut_orig.__name__ = 'x_is_even'

def x_get_max__mutmut_orig(numbers):
    """Retorna o maior número de uma lista"""
    if not numbers:
        return None
    return max(numbers)

def x_get_max__mutmut_1(numbers):
    """Retorna o maior número de uma lista"""
    if numbers:
        return None
    return max(numbers)

def x_get_max__mutmut_2(numbers):
    """Retorna o maior número de uma lista"""
    if not numbers:
        return None
    return max(None)

x_get_max__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_max__mutmut_1': x_get_max__mutmut_1, 
    'x_get_max__mutmut_2': x_get_max__mutmut_2
}

def get_max(*args, **kwargs):
    result = _mutmut_trampoline(x_get_max__mutmut_orig, x_get_max__mutmut_mutants, args, kwargs)
    return result 

get_max.__signature__ = _mutmut_signature(x_get_max__mutmut_orig)
x_get_max__mutmut_orig.__name__ = 'x_get_max'

def x_calculate_average__mutmut_orig(numbers):
    """Calcula a média de uma lista de números"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def x_calculate_average__mutmut_1(numbers):
    """Calcula a média de uma lista de números"""
    if numbers:
        return 0
    return sum(numbers) / len(numbers)

def x_calculate_average__mutmut_2(numbers):
    """Calcula a média de uma lista de números"""
    if not numbers:
        return 1
    return sum(numbers) / len(numbers)

def x_calculate_average__mutmut_3(numbers):
    """Calcula a média de uma lista de números"""
    if not numbers:
        return 0
    return sum(numbers) * len(numbers)

def x_calculate_average__mutmut_4(numbers):
    """Calcula a média de uma lista de números"""
    if not numbers:
        return 0
    return sum(None) / len(numbers)

x_calculate_average__mutmut_mutants : ClassVar[MutantDict] = {
'x_calculate_average__mutmut_1': x_calculate_average__mutmut_1, 
    'x_calculate_average__mutmut_2': x_calculate_average__mutmut_2, 
    'x_calculate_average__mutmut_3': x_calculate_average__mutmut_3, 
    'x_calculate_average__mutmut_4': x_calculate_average__mutmut_4
}

def calculate_average(*args, **kwargs):
    result = _mutmut_trampoline(x_calculate_average__mutmut_orig, x_calculate_average__mutmut_mutants, args, kwargs)
    return result 

calculate_average.__signature__ = _mutmut_signature(x_calculate_average__mutmut_orig)
x_calculate_average__mutmut_orig.__name__ = 'x_calculate_average'

def x_is_palindrome__mutmut_orig(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() == text.lower()[::-1]

def x_is_palindrome__mutmut_1(text):
    """Verifica se uma string é um palíndromo"""
    if text:
        return True
    return text.lower() == text.lower()[::-1]

def x_is_palindrome__mutmut_2(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return False
    return text.lower() == text.lower()[::-1]

def x_is_palindrome__mutmut_3(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.upper() == text.lower()[::-1]

def x_is_palindrome__mutmut_4(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() != text.lower()[::-1]

def x_is_palindrome__mutmut_5(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() == text.upper()[::-1]

def x_is_palindrome__mutmut_6(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() == text.lower()[::+1]

def x_is_palindrome__mutmut_7(text):
    """Verifica se uma string é um palíndromo"""
    if not text:
        return True
    return text.lower() == text.lower()[::-2]

x_is_palindrome__mutmut_mutants : ClassVar[MutantDict] = {
'x_is_palindrome__mutmut_1': x_is_palindrome__mutmut_1, 
    'x_is_palindrome__mutmut_2': x_is_palindrome__mutmut_2, 
    'x_is_palindrome__mutmut_3': x_is_palindrome__mutmut_3, 
    'x_is_palindrome__mutmut_4': x_is_palindrome__mutmut_4, 
    'x_is_palindrome__mutmut_5': x_is_palindrome__mutmut_5, 
    'x_is_palindrome__mutmut_6': x_is_palindrome__mutmut_6, 
    'x_is_palindrome__mutmut_7': x_is_palindrome__mutmut_7
}

def is_palindrome(*args, **kwargs):
    result = _mutmut_trampoline(x_is_palindrome__mutmut_orig, x_is_palindrome__mutmut_mutants, args, kwargs)
    return result 

is_palindrome.__signature__ = _mutmut_signature(x_is_palindrome__mutmut_orig)
x_is_palindrome__mutmut_orig.__name__ = 'x_is_palindrome'

def x_count_vowels__mutmut_orig(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_1(text):
    """Conta o número de vogais em uma string"""
    if text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_2(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 1
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_3(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = None
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_4(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "XXaeiouAEIOUXX"
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_5(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouaeiou"
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_6(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "AEIOUAEIOU"
    return sum(1 for char in text if char in vowels)

def x_count_vowels__mutmut_7(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(None)

def x_count_vowels__mutmut_8(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(2 for char in text if char in vowels)

def x_count_vowels__mutmut_9(text):
    """Conta o número de vogais em uma string"""
    if not text:
        return 0
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char not in vowels)

x_count_vowels__mutmut_mutants : ClassVar[MutantDict] = {
'x_count_vowels__mutmut_1': x_count_vowels__mutmut_1, 
    'x_count_vowels__mutmut_2': x_count_vowels__mutmut_2, 
    'x_count_vowels__mutmut_3': x_count_vowels__mutmut_3, 
    'x_count_vowels__mutmut_4': x_count_vowels__mutmut_4, 
    'x_count_vowels__mutmut_5': x_count_vowels__mutmut_5, 
    'x_count_vowels__mutmut_6': x_count_vowels__mutmut_6, 
    'x_count_vowels__mutmut_7': x_count_vowels__mutmut_7, 
    'x_count_vowels__mutmut_8': x_count_vowels__mutmut_8, 
    'x_count_vowels__mutmut_9': x_count_vowels__mutmut_9
}

def count_vowels(*args, **kwargs):
    result = _mutmut_trampoline(x_count_vowels__mutmut_orig, x_count_vowels__mutmut_mutants, args, kwargs)
    return result 

count_vowels.__signature__ = _mutmut_signature(x_count_vowels__mutmut_orig)
x_count_vowels__mutmut_orig.__name__ = 'x_count_vowels'

def x_factorial__mutmut_orig(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def x_factorial__mutmut_1(n):
    """Calcula o fatorial de um número"""
    if n <= 0:
        return None
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def x_factorial__mutmut_2(n):
    """Calcula o fatorial de um número"""
    if n < 1:
        return None
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def x_factorial__mutmut_3(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n < 1:
        return 1
    return n * factorial(n - 1)

def x_factorial__mutmut_4(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 2:
        return 1
    return n * factorial(n - 1)

def x_factorial__mutmut_5(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 2
    return n * factorial(n - 1)

def x_factorial__mutmut_6(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 1
    return n / factorial(n - 1)

def x_factorial__mutmut_7(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 1
    return n * factorial(None)

def x_factorial__mutmut_8(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 1
    return n * factorial(n + 1)

def x_factorial__mutmut_9(n):
    """Calcula o fatorial de um número"""
    if n < 0:
        return None
    if n <= 1:
        return 1
    return n * factorial(n - 2)

x_factorial__mutmut_mutants : ClassVar[MutantDict] = {
'x_factorial__mutmut_1': x_factorial__mutmut_1, 
    'x_factorial__mutmut_2': x_factorial__mutmut_2, 
    'x_factorial__mutmut_3': x_factorial__mutmut_3, 
    'x_factorial__mutmut_4': x_factorial__mutmut_4, 
    'x_factorial__mutmut_5': x_factorial__mutmut_5, 
    'x_factorial__mutmut_6': x_factorial__mutmut_6, 
    'x_factorial__mutmut_7': x_factorial__mutmut_7, 
    'x_factorial__mutmut_8': x_factorial__mutmut_8, 
    'x_factorial__mutmut_9': x_factorial__mutmut_9
}

def factorial(*args, **kwargs):
    result = _mutmut_trampoline(x_factorial__mutmut_orig, x_factorial__mutmut_mutants, args, kwargs)
    return result 

factorial.__signature__ = _mutmut_signature(x_factorial__mutmut_orig)
x_factorial__mutmut_orig.__name__ = 'x_factorial'

def x_fibonacci__mutmut_orig(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_1(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n < 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_2(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 1:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_3(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 1
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_4(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n != 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_5(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 2:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_6(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 2
    return fibonacci(n - 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_7(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) - fibonacci(n - 2)

def x_fibonacci__mutmut_8(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(None) + fibonacci(n - 2)

def x_fibonacci__mutmut_9(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n + 1) + fibonacci(n - 2)

def x_fibonacci__mutmut_10(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 2) + fibonacci(n - 2)

def x_fibonacci__mutmut_11(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(None)

def x_fibonacci__mutmut_12(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n + 2)

def x_fibonacci__mutmut_13(n):
    """Calcula o n-ésimo número de Fibonacci"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 3)

x_fibonacci__mutmut_mutants : ClassVar[MutantDict] = {
'x_fibonacci__mutmut_1': x_fibonacci__mutmut_1, 
    'x_fibonacci__mutmut_2': x_fibonacci__mutmut_2, 
    'x_fibonacci__mutmut_3': x_fibonacci__mutmut_3, 
    'x_fibonacci__mutmut_4': x_fibonacci__mutmut_4, 
    'x_fibonacci__mutmut_5': x_fibonacci__mutmut_5, 
    'x_fibonacci__mutmut_6': x_fibonacci__mutmut_6, 
    'x_fibonacci__mutmut_7': x_fibonacci__mutmut_7, 
    'x_fibonacci__mutmut_8': x_fibonacci__mutmut_8, 
    'x_fibonacci__mutmut_9': x_fibonacci__mutmut_9, 
    'x_fibonacci__mutmut_10': x_fibonacci__mutmut_10, 
    'x_fibonacci__mutmut_11': x_fibonacci__mutmut_11, 
    'x_fibonacci__mutmut_12': x_fibonacci__mutmut_12, 
    'x_fibonacci__mutmut_13': x_fibonacci__mutmut_13
}

def fibonacci(*args, **kwargs):
    result = _mutmut_trampoline(x_fibonacci__mutmut_orig, x_fibonacci__mutmut_mutants, args, kwargs)
    return result 

fibonacci.__signature__ = _mutmut_signature(x_fibonacci__mutmut_orig)
x_fibonacci__mutmut_orig.__name__ = 'x_fibonacci'

def x_is_prime__mutmut_orig(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_1(number):
    """Verifica se um número é primo"""
    if number <= 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_2(number):
    """Verifica se um número é primo"""
    if number < 3:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_3(number):
    """Verifica se um número é primo"""
    if number < 2:
        return True
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_4(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(None, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_5(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, None):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_6(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_7(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, ):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_8(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(3, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_9(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) - 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_10(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(None) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_11(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number * 0.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_12(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 1.5) + 1):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_13(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 2):
        if number % i == 0:
            return False
    return True

def x_is_prime__mutmut_14(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number / i == 0:
            return False
    return True

def x_is_prime__mutmut_15(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i != 0:
            return False
    return True

def x_is_prime__mutmut_16(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 1:
            return False
    return True

def x_is_prime__mutmut_17(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return True
    return True

def x_is_prime__mutmut_18(number):
    """Verifica se um número é primo"""
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return False

x_is_prime__mutmut_mutants : ClassVar[MutantDict] = {
'x_is_prime__mutmut_1': x_is_prime__mutmut_1, 
    'x_is_prime__mutmut_2': x_is_prime__mutmut_2, 
    'x_is_prime__mutmut_3': x_is_prime__mutmut_3, 
    'x_is_prime__mutmut_4': x_is_prime__mutmut_4, 
    'x_is_prime__mutmut_5': x_is_prime__mutmut_5, 
    'x_is_prime__mutmut_6': x_is_prime__mutmut_6, 
    'x_is_prime__mutmut_7': x_is_prime__mutmut_7, 
    'x_is_prime__mutmut_8': x_is_prime__mutmut_8, 
    'x_is_prime__mutmut_9': x_is_prime__mutmut_9, 
    'x_is_prime__mutmut_10': x_is_prime__mutmut_10, 
    'x_is_prime__mutmut_11': x_is_prime__mutmut_11, 
    'x_is_prime__mutmut_12': x_is_prime__mutmut_12, 
    'x_is_prime__mutmut_13': x_is_prime__mutmut_13, 
    'x_is_prime__mutmut_14': x_is_prime__mutmut_14, 
    'x_is_prime__mutmut_15': x_is_prime__mutmut_15, 
    'x_is_prime__mutmut_16': x_is_prime__mutmut_16, 
    'x_is_prime__mutmut_17': x_is_prime__mutmut_17, 
    'x_is_prime__mutmut_18': x_is_prime__mutmut_18
}

def is_prime(*args, **kwargs):
    result = _mutmut_trampoline(x_is_prime__mutmut_orig, x_is_prime__mutmut_mutants, args, kwargs)
    return result 

is_prime.__signature__ = _mutmut_signature(x_is_prime__mutmut_orig)
x_is_prime__mutmut_orig.__name__ = 'x_is_prime'