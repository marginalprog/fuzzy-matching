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
from prettytable import PrettyTable

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig, FuzzyAlgorithm
from fuzzy_matching.utils.transliteration.transliteration_utils import *
from fuzzy_matching.utils.cli_utils import (
    print_table, display_matches, display_consolidated,
    generate_test_data, generate_and_save_test_data, run_matching, save_results
)

# Классы для цветного вывода в терминале
class Colors:
    """Класс с ANSI-кодами цветов для терминала"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
        standard="Passport",
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
        print(f"Оригинал: {match['Оригинал']}")
        print(f"Вариант: {match['Вариант']}")
        print(f"Схожесть: {match['Схожесть']:.2f}")
        print()
    
    print("\nКонсолидированные данные:")
    print_table(consolidated)


def run_personal_data_demo():
    """Запускает демо сопоставления персональных данных"""
    print(f"\n{Colors.CYAN}=== Демо сопоставления персональных данных ==={Colors.ENDC}")
    
    # Создаем тестовые данные
    original_data = [
        {
            'id': '1',
            'Фамилия': 'Иванов',
            'Имя': 'Иван',
            'Отчество': 'Иванович',
            'email': 'ivanov@example.com'
        },
        {
            'id': '2',
            'Фамилия': 'Петров-Сидоров',
            'Имя': 'Петр',
            'Отчество': 'Петрович',
            'email': 'petrov@example.com'
        }
    ]
    
    variant_data = [
        {
            'id': '1',
            'Фамилия': 'Иванов',
            'Имя': 'Ваня',  # Уменьшительная форма
            'Отчество': 'Иванович',
            'email': 'ivanov@example.com'
        },
        {
            'id': '2',
            'Фамилия': 'Сидоров-Петров',  # Изменен порядок частей фамилии
            'Имя': 'Петр',
            'Отчество': 'Петрович',
            'email': 'petrov@example.com'
        }
    ]
    
    # Создаем конфигурацию для персональных данных
    config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SORT),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.PARTIAL_RATIO),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.RATIO),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.RATIO)
        ],
        threshold=0.7,
        block_field='id'
    )
    
    # Создаем экземпляр DataMatcher
    matcher = DataMatcher(config=config)
    
    # Выполняем сопоставление
    print(f"\n{Colors.YELLOW}Выполняем сопоставление персональных данных...{Colors.ENDC}")
    matches, consolidated = matcher.match_and_consolidate(original_data, variant_data)
    
    # Выводим результаты
    print(f"\n{Colors.GREEN}Найдено совпадений: {len(matches)}{Colors.ENDC}")
    
    # Создаем таблицу для вывода результатов
    table = PrettyTable()
    table.field_names = ["Тип", "Фамилия", "Имя", "Отчество", "email", "Схожесть"]
    
    for match in matches:
        orig = match['Оригинал']
        var = match['Вариант']
        similarity = match['Схожесть']
        
        # Добавляем строку для оригинала
        table.add_row([
            "Оригинал", 
            orig['Фамилия'], 
            orig['Имя'], 
            orig['Отчество'], 
            orig['email'],
            ""  # Пустая ячейка для схожести
        ])
        
        # Добавляем строку для варианта
        table.add_row([
            "Вариант", 
            var['Фамилия'], 
            var['Имя'], 
            var['Отчество'], 
            var['email'],
            f"{similarity:.2%}"
        ])
        
        # Добавляем пустую строку для разделения пар записей
        if match != matches[-1]:
            table.add_row([""] * 6)
    
    # Настраиваем стиль таблицы
    table.align = "l"
    table.border = True
    table.header = True
    
    print("\nРезультаты сопоставления:")
    print(table)
    
    # Выводим консолидированные данные
    print(f"\n{Colors.CYAN}Консолидированные данные:{Colors.ENDC}")
    cons_table = PrettyTable()
    cons_table.field_names = ["id", "Фамилия", "Имя", "Отчество", "email"]
    
    for record in consolidated:
        cons_table.add_row([
            record.get('id', ""),
            record.get('Фамилия', ""),
            record.get('Имя', ""),
            record.get('Отчество', ""),
            record.get('email', "")
        ])
    
    cons_table.align = "l"
    print(cons_table)
    
    input(f"\n{Colors.GREEN}Нажмите Enter для продолжения...{Colors.ENDC}")

def run_business_data_demo():
    """Запускает демо сопоставления бизнес-данных"""
    print(f"\n{Colors.CYAN}=== Демо сопоставления бизнес-данных ==={Colors.ENDC}")
    
    # Создаем тестовые данные
    original_data = [
        {
            'id': '1',
            'company_name': 'ООО Ромашка',
            'legal_name': 'Общество с ограниченной ответственностью Ромашка',
            'inn': '1234567890',
            'kpp': '123456789'
        },
        {
            'id': '2',
            'company_name': 'АО ТехноПром',
            'legal_name': 'Акционерное общество ТехноПром',
            'inn': '0987654321',
            'kpp': '987654321'
        }
    ]
    
    variant_data = [
        {
            'id': '1',
            'company_name': 'Ромашка ООО',  # Изменен порядок слов
            'legal_name': 'ООО Ромашка',  # Сокращенное название
            'inn': '1234567890',
            'kpp': '123456789'
        },
        {
            'id': '2',
            'company_name': 'ТехноПром АО',  # Изменен порядок слов
            'legal_name': 'АО ТехноПром',  # Сокращенное название
            'inn': '0987654321',
            'kpp': '987654321'
        }
    ]
    
    # Создаем конфигурацию для бизнес-данных
    config = MatchConfig(
        fields=[
            MatchFieldConfig(field='company_name', weight=0.4, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET),
            MatchFieldConfig(field='legal_name', weight=0.3, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SORT),
            MatchFieldConfig(field='inn', weight=0.2, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.RATIO),
            MatchFieldConfig(field='kpp', weight=0.1, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.RATIO)
        ],
        threshold=0.7,
        block_field='id'
    )
    
    # Создаем экземпляр DataMatcher
    matcher = DataMatcher(config=config)
    
    # Выполняем сопоставление
    print(f"\n{Colors.YELLOW}Выполняем сопоставление бизнес-данных...{Colors.ENDC}")
    matches, consolidated = matcher.match_and_consolidate(original_data, variant_data)
    
    # Выводим результаты
    print(f"\n{Colors.GREEN}Найдено совпадений: {len(matches)}{Colors.ENDC}")
    
    # Создаем таблицу для вывода результатов
    table = PrettyTable()
    table.field_names = ["Тип", "Название", "Юр. название", "ИНН", "КПП", "Схожесть"]
    
    for match in matches:
        orig = match['Оригинал']
        var = match['Вариант']
        similarity = match['Схожесть']
        
        # Добавляем строку для оригинала
        table.add_row([
            "Оригинал", 
            orig['company_name'], 
            orig['legal_name'], 
            orig['inn'], 
            orig['kpp'],
            ""  # Пустая ячейка для схожести
        ])
        
        # Добавляем строку для варианта
        table.add_row([
            "Вариант", 
            var['company_name'], 
            var['legal_name'], 
            var['inn'], 
            var['kpp'],
            f"{similarity:.2%}"
        ])
        
        # Добавляем пустую строку для разделения пар записей
        if match != matches[-1]:
            table.add_row([""] * 6)
    
    # Настраиваем стиль таблицы
    table.align = "l"
    table.border = True
    table.header = True
    
    print("\nРезультаты сопоставления:")
    print(table)
    
    # Выводим консолидированные данные
    print(f"\n{Colors.CYAN}Консолидированные данные:{Colors.ENDC}")
    cons_table = PrettyTable()
    cons_table.field_names = ["id", "Название", "Юр. название", "ИНН", "КПП"]
    
    for record in consolidated:
        cons_table.add_row([
            record.get('id', ""),
            record.get('company_name', ""),
            record.get('legal_name', ""),
            record.get('inn', ""),
            record.get('kpp', "")
        ])
    
    cons_table.align = "l"
    print(cons_table)
    
    input(f"\n{Colors.GREEN}Нажмите Enter для продолжения...{Colors.ENDC}")

def run_technical_data_demo():
    """Запускает демо сопоставления технических данных"""
    print(f"\n{Colors.CYAN}=== Демо сопоставления технических данных ==={Colors.ENDC}")
    
    # Создаем тестовые данные
    original_data = [
        {
            'id': '1',
            'serial_number': 'SN-2023-001',
            'product_code': 'PC-123-ABC',
            'technical_description': 'High-performance server with 32GB RAM',
            'url': 'https://example.com/products/server-1'
        },
        {
            'id': '2',
            'serial_number': 'SN-2023-002',
            'product_code': 'PC-456-DEF',
            'technical_description': 'Enterprise storage system 10TB',
            'url': 'https://example.com/products/storage-1'
        }
    ]
    
    variant_data = [
        {
            'id': '1',
            'serial_number': 'SN2023001',  # Убраны дефисы
            'product_code': 'PC123ABC',    # Убраны дефисы
            'technical_description': 'Server with 32GB RAM high-performance',  # Изменен порядок слов
            'url': 'example.com/products/server-1'  # Убран протокол
        },
        {
            'id': '2',
            'serial_number': 'SN-2023-002',
            'product_code': 'PC-456-DEF',
            'technical_description': '10TB Enterprise storage system',  # Изменен порядок слов
            'url': 'https://example.com/storage-1'  # Упрощен URL
        }
    ]
    
    # Создаем конфигурацию для технических данных
    config = MatchConfig(
        fields=[
            MatchFieldConfig(field='serial_number', weight=0.3, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.RATIO),
            MatchFieldConfig(field='product_code', weight=0.3, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.RATIO),
            MatchFieldConfig(field='technical_description', weight=0.3, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET),
            MatchFieldConfig(field='url', weight=0.1, transliterate=False, fuzzy_algorithm=FuzzyAlgorithm.PARTIAL_RATIO)
        ],
        threshold=0.7,
        block_field='id'
    )
    
    # Создаем экземпляр DataMatcher
    matcher = DataMatcher(config=config)
    
    # Выполняем сопоставление
    print(f"\n{Colors.YELLOW}Выполняем сопоставление технических данных...{Colors.ENDC}")
    matches, consolidated = matcher.match_and_consolidate(original_data, variant_data)
    
    # Выводим результаты
    print(f"\n{Colors.GREEN}Найдено совпадений: {len(matches)}{Colors.ENDC}")
    
    # Создаем таблицу для вывода результатов
    table = PrettyTable()
    table.field_names = ["Тип", "Серийный номер", "Код продукта", "Описание", "URL", "Схожесть"]
    
    for match in matches:
        orig = match['Оригинал']
        var = match['Вариант']
        similarity = match['Схожесть']
        
        # Добавляем строку для оригинала
        table.add_row([
            "Оригинал", 
            orig['serial_number'], 
            orig['product_code'], 
            orig['technical_description'], 
            orig['url'],
            ""  # Пустая ячейка для схожести
        ])
        
        # Добавляем строку для варианта
        table.add_row([
            "Вариант", 
            var['serial_number'], 
            var['product_code'], 
            var['technical_description'], 
            var['url'],
            f"{similarity:.2%}"
        ])
        
        # Добавляем пустую строку для разделения пар записей
        if match != matches[-1]:
            table.add_row([""] * 6)
    
    # Настраиваем стиль таблицы
    table.align = "l"
    table.border = True
    table.header = True
    
    print("\nРезультаты сопоставления:")
    print(table)
    
    # Выводим консолидированные данные
    print(f"\n{Colors.CYAN}Консолидированные данные:{Colors.ENDC}")
    cons_table = PrettyTable()
    cons_table.field_names = ["id", "Серийный номер", "Код продукта", "Описание", "URL"]
    
    for record in consolidated:
        cons_table.add_row([
            record.get('id', ""),
            record.get('serial_number', ""),
            record.get('product_code', ""),
            record.get('technical_description', ""),
            record.get('url', "")
        ])
    
    cons_table.align = "l"
    print(cons_table)
    
    input(f"\n{Colors.GREEN}Нажмите Enter для продолжения...{Colors.ENDC}")

def run_transliteration_demo():
    """Запускает демо транслитерации"""
    print(f"\n{Colors.CYAN}=== Демо транслитерации ==={Colors.ENDC}")
    
    # Создаем тестовые данные
    test_data = [
        {
            'id': '1',
            'Фамилия': 'Иванов',
            'Имя': 'Иван',
            'Отчество': 'Иванович'
        },
        {
            'id': '2',
            'Фамилия': 'Петров',
            'Имя': 'Петр',
            'Отчество': 'Петрович'
        },
        {
            'id': '3',
            'Фамилия': 'Щербаков',
            'Имя': 'Евгений',
            'Отчество': 'Александрович'
        }
    ]
    
    # Создаем таблицу для вывода результатов
    table = PrettyTable()
    table.field_names = ["№", "Фамилия", "Имя", "Отчество", "ГОСТ", "Научный", "Паспортный"]
    
    for i, record in enumerate(test_data):
        # Получаем ФИО
        last_name = record['Фамилия']
        first_name = record['Имя']
        middle_name = record['Отчество']
        full_name = f"{last_name} {first_name} {middle_name}"
        
        # Транслитерация по разным стандартам
        gost = transliterate_ru_to_en(full_name, GOST_STANDARD)
        scientific = transliterate_ru_to_en(full_name, SCIENTIFIC_STANDARD)
        passport = transliterate_ru_to_en(full_name, PASSPORT_STANDARD)
        
        table.add_row([i+1, last_name, first_name, middle_name, gost, scientific, passport])
    
    # Настраиваем стиль таблицы
    table.align = "l"
    table.border = True
    table.header = True
    
    print("\nРезультаты транслитерации по разным стандартам:")
    print(table)
    
    # Показываем примеры обратной транслитерации
    print(f"\n{Colors.YELLOW}Примеры обратной транслитерации (с английского на русский):{Colors.ENDC}")
    
    english_names = [
        "Ivanov Ivan Ivanovich",
        "Petrov Petr Petrovich",
        "Shcherbakov Evgeniy Aleksandrovich"
    ]
    
    # Создаем таблицу для обратной транслитерации
    back_table = PrettyTable()
    back_table.field_names = ["№", "Английский вариант", "Русский вариант"]
    
    for i, name in enumerate(english_names):
        russian = transliterate_en_to_ru(name, PASSPORT_STANDARD)
        back_table.add_row([i+1, name, russian])
    
    # Настраиваем стиль таблицы
    back_table.align = "l"
    back_table.border = True
    back_table.header = True
    
    print("\nРезультаты обратной транслитерации:")
    print(back_table)
    
    # Демонстрация автоопределения языка
    print(f"\n{Colors.YELLOW}Автоопределение языка текста:{Colors.ENDC}")
    
    mixed_names = [
        "Иванов Иван Иванович",
        "Ivanov Ivan Ivanovich",
        "Смирнова Ольга Петровна",
        "Smirnova Olga Petrovna",
        "Щербаков-Иванов Алексей",
        "Shcherbakov-Ivanov Alexey"
    ]
    
    # Создаем таблицу для определения языка
    lang_table = PrettyTable()
    lang_table.field_names = ["№", "Текст", "Определенный язык"]
    
    for i, name in enumerate(mixed_names):
        lang = detect_language(name)
        lang_display = "Русский" if lang == "ru" else "Английский" if lang == "en" else "Неизвестный"
        lang_table.add_row([i+1, name, lang_display])
    
    # Настраиваем стиль таблицы
    lang_table.align = "l"
    lang_table.border = True
    lang_table.header = True
    
    print("\nРезультаты определения языка:")
    print(lang_table)
    
    input(f"\n{Colors.GREEN}Нажмите Enter для продолжения...{Colors.ENDC}")

def run_example(example_name):
    """
    Запускает выбранный пример.
    
    :param example_name: название примера для запуска
    """
    if example_name == "transliteration":
        demo_transliteration()
    elif example_name == "transliteration_matching":
        demo_transliteration_matching()
    elif example_name == "personal_data_demo":
        run_personal_data_demo()
    elif example_name == "business_data_demo":
        run_business_data_demo()
    elif example_name == "technical_data_demo":
        run_technical_data_demo()
    elif example_name == "transliteration_demo":
        run_transliteration_demo()
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
    print("3. Демо сопоставления персональных данных")
    print("4. Демо сопоставления бизнес-данных")
    print("5. Демо сопоставления технических данных")
    print("6. Демо транслитерации")
    print("0. Выход")
    
    choice = input("\nВыберите пример (введите номер): ")
    
    if choice == "1":
        demo_transliteration()
    elif choice == "2":
        demo_transliteration_matching()
    elif choice == "3":
        run_personal_data_demo()
    elif choice == "4":
        run_business_data_demo()
    elif choice == "5":
        run_technical_data_demo()
    elif choice == "6":
        run_transliteration_demo()
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
    print("  personal_data_demo       - Демо сопоставления персональных данных")
    print("  business_data_demo       - Демо сопоставления бизнес-данных")
    print("  technical_data_demo      - Демо сопоставления технических данных")
    print("  transliteration_demo     - Демо транслитерации")
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