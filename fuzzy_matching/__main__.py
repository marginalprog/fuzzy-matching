"""
Главный модуль для запуска библиотеки fuzzy_matching из командной строки.

Использование:
    python -m fuzzy_matching [пример]

Доступные примеры:
    simple - простой пример сопоставления
    translit - пример с транслитерацией
    benchmark - тест производительности
    advanced - расширенный тест производительности
"""

import sys
import os

def print_usage():
    """Выводит инструкцию по использованию."""
    print("Использование: python -m fuzzy_matching [пример]")
    print("\nДоступные примеры:")
    print("  simple     - простой пример сопоставления")
    print("  translit   - пример с транслитерацией")
    print("  benchmark  - тест производительности")
    print("  advanced   - расширенный тест производительности")

def main():
    """Основная функция для запуска примеров."""
    # Проверяем наличие аргументов
    if len(sys.argv) < 2:
        print_usage()
        return

    example = sys.argv[1].lower()

    # Запускаем соответствующий пример
    if example == 'simple':
        from fuzzy_matching.examples.simple_example import main
        main()
    elif example == 'translit':
        from fuzzy_matching.examples.transliteration_example import main
        main()
    elif example == 'benchmark':
        from fuzzy_matching.tests.benchmark_test import main
        main()
    elif example == 'advanced':
        from fuzzy_matching.tests.advanced_benchmark import main
        main()
    else:
        print(f"Неизвестный пример: {example}")
        print_usage()

if __name__ == "__main__":
    main() 