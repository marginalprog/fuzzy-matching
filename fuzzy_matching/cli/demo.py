#!/usr/bin/env python
"""
Демонстрационный модуль библиотеки fuzzy_matching.
Запускает интерактивное меню для выбора примеров транслитерации и нечеткого сопоставления.

Этот скрипт предназначен для демонстрации возможностей библиотеки, но не является
основным интерфейсом для выполнения задач транслитерации и сопоставления данных.
Для практического использования рекомендуется:
- CLI-интерфейс: fuzzy_matching/cli/process_data.py
- API: Непосредственное использование классов из fuzzy_matching/core/
"""

import sys
import os
import argparse
import cProfile
import pstats
import pandas as pd
import re

from fuzzy_matching.utils.data_generator import DataGenerator, Language
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.utils.transliteration.transliteration_utils import *
from fuzzy_matching.utils.cli_utils import (
    print_table, display_matches, display_consolidated,
    generate_test_data, generate_and_save_test_data, run_matching, save_results
)


def generate_transliteration_test_data():
    """
    Генерирует тестовые данные для демонстрации транслитерации.
    Создает два списка: русский и транслитерированный английский.
    
    :return: кортеж (русский список, английский список)
    """
    russian_data = [
        {
            'id': 'ru_1',
            'Фамилия': 'Иванов',
            'Имя': 'Александр',
            'Отчество': 'Сергеевич',
            'email': 'ivanov@example.ru'
        },
        {
            'id': 'ru_2',
            'Фамилия': 'Петров',
            'Имя': 'Иван',
            'Отчество': 'Петрович',
            'email': 'petrov@example.ru'
        },
        {
            'id': 'ru_3',
            'Фамилия': 'Сидоров',
            'Имя': 'Михаил',
            'Отчество': 'Иванович',
            'email': 'sidorov@example.ru'
        },
        {
            'id': 'ru_4',
            'Фамилия': 'Кузнецов',
            'Имя': 'Алексей',
            'Отчество': 'Дмитриевич',
            'email': 'kuznetsov@example.ru'
        },
        {
            'id': 'ru_5',
            'Фамилия': 'Смирнов',
            'Имя': 'Дмитрий',
            'Отчество': 'Александрович',
            'email': 'smirnov@example.ru'
        }
    ]
    
    english_data = [
        {
            'id': 'en_1',
            'last_name': 'Ivanov',
            'first_name': 'Alexander',
            'middle_name': 'Sergeevich',
            'email': 'ivanov@example.com'
        },
        {
            'id': 'en_2',
            'last_name': 'Petrov',
            'first_name': 'Ivan',
            'middle_name': 'Petrovich',
            'email': 'petrov@example.com'
        },
        {
            'id': 'en_3',
            'last_name': 'Sidorov',
            'first_name': 'Mikhail',
            'middle_name': 'Ivanovich',
            'email': 'sidorov@example.com'
        },
        {
            'id': 'en_4',
            'last_name': 'Kuznetsov',
            'first_name': 'Alexey',
            'middle_name': 'Dmitrievich',
            'email': 'kuznetsov@example.com'
        },
        {
            'id': 'en_5',
            'last_name': 'Smirnov',
            'first_name': 'Dmitry',
            'middle_name': 'Alexandrovich',
            'email': 'smirnov@example.com'
        }
    ]
    
    return russian_data, english_data


def demo_transliteration():
    """
    Демонстрирует работу транслитерации.
    """
    print("\n=== Демонстрация транслитерации ===\n")
    
    # Примеры имен на русском
    russian_names = [
        "Иванов Александр Сергеевич",
        "Петрова Екатерина Ивановна",
        "Кузнецов Дмитрий Алексеевич",
        "Смирнова Ольга Владимировна",
        "Попов Сергей Николаевич"
    ]
    
    print("Русские имена:")
    for name in russian_names:
        print(f"  {name}")
    
    print("\nТранслитерация по стандарту ГОСТ 7.79-2000:")
    for name in russian_names:
        trans = transliterate_ru_to_en(name, GOST_STANDARD)
        print(f"  {name} -> {trans}")
    
    print("\nТранслитерация по научному стандарту:")
    for name in russian_names:
        trans = transliterate_ru_to_en(name, SCIENTIFIC_STANDARD)
        print(f"  {name} -> {trans}")
    
    print("\nТранслитерация по паспортному стандарту:")
    for name in russian_names:
        trans = transliterate_ru_to_en(name, PASSPORT_STANDARD)
        print(f"  {name} -> {trans}")
    
    # Примеры имен на английском
    english_names = [
        "Ivanov Alexander Sergeevich",
        "Petrova Ekaterina Ivanovna",
        "Kuznetsov Dmitry Alekseevich",
        "Smirnova Olga Vladimirovna",
        "Popov Sergey Nikolaevich"
    ]
    
    print("\nАнглийские имена:")
    for name in english_names:
        print(f"  {name}")
    
    print("\nОбратная транслитерация на русский:")
    for name in english_names:
        trans = transliterate_en_to_ru(name, PASSPORT_STANDARD)
        print(f"  {name} -> {trans}")
    
    print("\nОпределение языка текста:")
    for name in russian_names + english_names:
        lang = detect_language(name)
        print(f"  {name} -> {lang}")


def demo_transliteration_matching():
    """
    Демонстрирует сопоставление данных с использованием транслитерации.
    """
    print("\n=== Демонстрация сопоставления с паспортной транслитерацией ===\n")
    
    # Генерируем тестовые данные
    russian_data, english_data = generate_transliteration_test_data()
    
    print("Русские данные:")
    print_table(russian_data)
    
    print("\nАнглийские данные:")
    print_table(english_data)
    
    # Настраиваем конфигурацию для сопоставления
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Паспортная",
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    match_fields = [
        MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True),
        MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
        MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True),
        MatchFieldConfig(field='email', weight=0.1, transliterate=False)
    ]
    
    config = MatchConfig(
        fields=match_fields,
        threshold=0.7,
        transliteration=transliteration_config
    )
    
    # Выполняем сопоставление
    matcher = DataMatcher(config=config)
    
    # Преобразуем английские данные к формату русских
    english_data_mapped = []
    for record in english_data:
        mapped_record = {
            'id': record['id'],
            'Фамилия': record['last_name'],
            'Имя': record['first_name'],
            'Отчество': record['middle_name'],
            'email': record['email']
        }
        english_data_mapped.append(mapped_record)
    
    matches, consolidated = matcher.match_and_consolidate(russian_data, english_data_mapped)
    
    print("\nНайденные совпадения:")
    for match in matches:
        print(f"Запись 1: {match['Запись 1']}")
        print(f"Запись 2: {match['Запись 2']}")
        print(f"Совпадение: {match['Совпадение'][0]:.2f}")
        print()
    
    print("\nКонсолидированные данные:")
    print_table(consolidated)


def run_example(example_name):
    """
    Запускает выбранный пример.
    
    :param example_name: название примера для запуска
    """
    if example_name == "transliteration":
        demo_transliteration()
    elif example_name == "transliteration_matching":
        demo_transliteration_matching()
    else:
        print(f"Пример '{example_name}' не найден.")
        print_usage()


def print_menu():
    """
    Выводит интерактивное меню для выбора примера.
    """
    print("\n=== Меню примеров fuzzy_matching ===\n")
    print("1. Демонстрация транслитерации")
    print("2. Демонстрация сопоставления с транслитерацией")
    print("0. Выход")
    
    choice = input("\nВыберите пример (введите номер): ")
    
    if choice == "1":
        demo_transliteration()
    elif choice == "2":
        demo_transliteration_matching()
    elif choice == "0":
        print("Выход из программы.")
        sys.exit(0)
    else:
        print("Неверный выбор. Попробуйте снова.")
    
    # Рекурсивно вызываем меню снова
    input("\nНажмите Enter для продолжения...")
    print_menu()


def print_usage():
    """
    Выводит справку по использованию скрипта.
    """
    print("Использование:")
    print("  python -m fuzzy_matching.cli.demo [пример]")
    print("\nДоступные примеры:")
    print("  transliteration          - Демонстрация транслитерации")
    print("  transliteration_matching - Демонстрация сопоставления с транслитерацией")
    print("\nБез аргументов запускает интерактивное меню.")


def main():
    """
    Основная функция скрипта.
    """
    parser = argparse.ArgumentParser(description="Демонстрация возможностей библиотеки fuzzy_matching")
    parser.add_argument("example", nargs="?", help="Название примера для запуска")
    parser.add_argument("--profile", action="store_true", help="Запустить профилирование")
    
    args = parser.parse_args()
    
    if args.profile:
        # Запускаем профилирование
        profiler = cProfile.Profile()
        profiler.enable()
        
        if args.example:
            run_example(args.example)
        else:
            print_menu()
        
        profiler.disable()
        
        # Сохраняем результаты профилирования
        with open("profile_data.prof", "w") as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.sort_stats("cumulative")
            stats.print_stats()
        
        print("\nРезультаты профилирования сохранены в profile_data.prof")
    else:
        # Обычный запуск
        if args.example:
            run_example(args.example)
        else:
            print_menu()


if __name__ == "__main__":
    main() 