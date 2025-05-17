#!/usr/bin/env python
"""
Точка входа для запуска библиотеки fuzzy_matching.
Запускает интерактивное меню для выбора примера.
"""

import sys
import os
import argparse
import cProfile
import pstats
import pandas as pd
import re

from prettytable import PrettyTable
from fuzzy_matching.utils.data_generator import DataGenerator, Language
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
import fuzzy_matching.utils.transliteration_utils as translit


def generate_test_data(probabilities, gen_fields, count=100):
    """
    Генерирует тестовые данные: оригинальный и искаженный списки.
    
    :param probabilities: словарь вероятностей различных искажений
    :param gen_fields: список полей для генерации
    :param count: количество записей для генерации (по умолчанию 100)
    :return: кортеж (список оригинальных записей, список искаженных записей)
    """
    dg = DataGenerator(probabilities=probabilities)
    original_list, variant_list = dg.generate_records_pair(count, fields=gen_fields)
    return original_list, variant_list


# todo: in/out json/csv на выбор?
def generate_and_save_test_data(probabilities, gen_fields, count=100, file_format='json'):
    """
    Генерирует тестовые данные и сохраняет их в файлы.
    
    :param probabilities: словарь вероятностей различных искажений
    :param gen_fields: список полей для генерации
    :param count: количество записей для генерации (по умолчанию 100)
    :param file_format: формат файлов для сохранения ('json' или 'csv')
    :return: кортеж (список оригинальных записей, список искаженных записей)
    """
    dg = DataGenerator(probabilities=probabilities)
    original_list, variant_list = dg.generate_records_pair(count, fields=gen_fields)

    if file_format == 'json':
        dg.save_to_json(original_list, 'original_data_list.json')
        dg.save_to_json(variant_list, 'variant_data_list.json')
    elif file_format == 'csv':
        dg.save_to_csv(original_list, 'original_data_list.csv')
        dg.save_to_csv(variant_list, 'variant_data_list.csv')
    else:
        raise ValueError("Неверный формат файла. Выберите '.json' или '.csv'.")

    return original_list, variant_list


def display_sample_data(original_list, variant_list, rows_count=5):
    """
    Выводит образцы данных из обоих списков в виде таблицы.
    
    :param original_list: список оригинальных записей
    :param variant_list: список искаженных записей
    :param rows_count: количество строк для отображения (по умолчанию 5)
    """
    print(f'Первые {rows_count} записей из оригинального списка:')
    print_table(original_list[:rows_count])
    print(f'\nПервые {rows_count} записей из искаженного списка:')
    print_table(variant_list[:rows_count])
    print()


def run_matching(original_list, variant_list, config: MatchConfig):
    """
    Запускает процесс сопоставления и консолидации данных.
    
    :param original_list: список оригинальных записей
    :param variant_list: список искаженных записей
    :param config: конфигурация для сопоставления (экземпляр MatchConfig)
    :return: кортеж (экземпляр DataMatcher, список совпадений, список консолидированных записей)
    """
    matcher = DataMatcher(config=config)
    matches, consolidated = matcher.match_and_consolidate(original_list, variant_list)
    return matcher, matches, consolidated


def display_matches(matches, limit=5):
    """
    Выводит результаты совпадений в виде таблицы PrettyTable.
    
    :param matches: список найденных совпадений
    :param limit: максимальное количество строк для отображения (по умолчанию 5)
    """
    # Создаем таблицу и задаем заголовки колонок
    table = PrettyTable()
    # table.field_names = ["ID 1", "Запись 1", "ID 2", "Запись 2", "Совпадение"]
    table.field_names = ["Запись 1", "Запись 2", "Совпадение"]

    # Добавляем строки в таблицу
    for match in matches[:limit]:
        # id1 = match["ID 1"]
        # id2 = match["ID 2"]
        rec1 = " ".join(match["Запись 1"])
        rec2 = " ".join(match["Запись 2"])
        score = f"{match['Совпадение'][0]:.2f}"
        # table.add_row([id1, rec1, id2, rec2, score])
        table.add_row([rec1, rec2, score])

    # Опции выравнивания
    # table.align["ID 1"] = "r"
    # table.align["ID 2"] = "r"
    table.align["Запись 1"] = "l"
    table.align["Запись 2"] = "l"
    table.align["Совпадение"] = "r"

    # Вывод
    print(f"\nОтобрано: {len(matches)} записей\n")
    print(table)


def display_consolidated(consolidated, sort_field, limit=5):
    """
    Выводит консолидированные записи в виде DataFrame pandas.
    
    :param consolidated: список консолидированных записей
    :param sort_field: поле для сортировки результатов
    :param limit: максимальное количество строк для отображения (по умолчанию 5)
    """
    df_consolidated = pd.DataFrame(consolidated)
    if sort_field in df_consolidated.columns:
        df_consolidated = df_consolidated.sort_values(by="Фамилия", ascending=True)
    else:
        print(f'Столбец {sort_field} отсутствует в данных.')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('display.max_rows', limit)
    print(f"\nКонсолидировано: {len(consolidated)} записей\n")
    print(df_consolidated)


def print_table(data):
    """Выводит данные в виде форматированной таблицы"""
    if not data:
        print("Нет данных для отображения")
        return

    table = PrettyTable()
    table.field_names = data[0].keys()
    for row in data:
        table.add_row(row.values())

    table.align = 'l'
    print(table)


def save_results(matcher, matches, consolidated, file_format='json'):
    """
    Сохраняет результаты сопоставления и консолидации в файлы.
    
    :param matcher: экземпляр DataMatcher
    :param matches: список найденных совпадений
    :param consolidated: список консолидированных записей
    :param file_format: формат файлов для сохранения ('json' или 'csv')
    """
    matcher.save_matches_to_json(matches, 'matches.json')
    matcher.save_matches_to_csv(matches, 'matches.csv')
    matcher.save_consolidated_to_json(consolidated, 'consolidated.json')
    matcher.save_consolidated_to_csv(consolidated, 'consolidated.csv')

    if file_format == 'json':
        matcher.save_matches_to_json(matches, 'matches.json')
        matcher.save_consolidated_to_json(consolidated, 'consolidated.json')
    elif file_format == 'csv':
        matcher.save_matches_to_csv(matches, 'matches.csv')
        matcher.save_consolidated_to_csv(consolidated, 'consolidated.csv')
    else:
        raise ValueError("Неверный формат вывода файла. Выберите '.json' или '.csv'.")


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
            'Имя': 'Михаил',
            'Отчество': 'Иванович',
            'email': 'petrov@example.ru'
        },
        {
            'id': 'ru_3',
            'Фамилия': 'Сидорова',
            'Имя': 'Елена',
            'Отчество': 'Александровна',
            'email': 'sidorova@example.ru'
        },
        {
            'id': 'ru_4',
            'Фамилия': 'Кузнецов',
            'Имя': 'Дмитрий',
            'Отчество': 'Николаевич',
            'email': 'kuznetsov@example.ru'
        },
        {
            'id': 'ru_5',
            'Фамилия': 'Смирнова',
            'Имя': 'Ольга',
            'Отчество': 'Владимировна',
            'email': 'smirnova@example.ru'
        }
    ]
    
    # Создаем английские варианты с различными правилами транслитерации
    english_data = [
        {
            'id': 'en_1',
            'Фамилия': 'Ivanov',
            'Имя': 'Alexander',  # Используем английский вариант имени
            'Отчество': 'Sergeevich',
            'email': 'ivanov@example.com'
        },
        {
            'id': 'en_2',
            'Фамилия': 'Petrov',
            'Имя': 'Michail',  # Транслитерация через научный стандарт
            'Отчество': 'Ivanovich',
            'email': 'petrov@example.com'
        },
        {
            'id': 'en_3',
            'Фамилия': 'Sydorova',  # Разные правила транслитерации
            'Имя': 'Elena',
            'Отчество': 'Aleksandrovna',
            'email': 'sydorova@example.com'
        },
        {
            'id': 'en_4',
            'Фамилия': 'Kuznetsov',
            'Имя': 'Dmitriy',
            'Отчество': 'Nikolaevich',
            'email': 'kuznetsov@example.com'
        },
        {
            'id': 'en_5',
            'Фамилия': 'Smirnova',
            'Имя': 'Olga',
            'Отчество': 'Vladimirovna',
            'email': 'smirnova@example.com'
        },
        # Добавляем запись с вариантами написания одного и того же имени
        {
            'id': 'en_6',
            'Фамилия': 'Alexandrov',
            'Имя': 'Aleksandr', # Александр в научной транслитерации
            'Отчество': 'Petrovich',
            'email': 'alex@example.com'
        }
    ]
    
    return russian_data, english_data


def demo_transliteration():
    """
    Демонстрирует возможности транслитерации на примере имен.
    """
    print("\n============ ДЕМОНСТРАЦИЯ ТРАНСЛИТЕРАЦИИ ============\n")
    
    examples = [
        ("Иванов", "Ivanov"),
        ("Александр", "Alexander"),
        ("Щербаков", "Shcherbakov"),
        ("Юрий", "Yuri"),
        ("Каталёночкин", "Katalenochkin")
    ]
    
    # Таблица для демонстрации различных стандартов транслитерации
    table = PrettyTable()
    table.field_names = ["Русский", "ГОСТ 7.79-2000", "Научная", "Паспортная"]
    
    for ru_name, _ in examples:
        gost = translit.transliterate_ru_to_en(ru_name, translit.GOST_STANDARD)
        scientific = translit.transliterate_ru_to_en(ru_name, translit.SCIENTIFIC_STANDARD)
        passport = translit.transliterate_ru_to_en(ru_name, translit.PASSPORT_STANDARD)
        
        table.add_row([ru_name, gost, scientific, passport])
    
    print("Варианты транслитерации с русского на английский по разным стандартам:")
    print(table)
    print()
    
    # Демонстрация обратной транслитерации
    table = PrettyTable()
    table.field_names = ["Английский", "Русский (паспортный стандарт)"]
    
    for _, en_name in examples:
        ru_name = translit.transliterate_en_to_ru(en_name, translit.PASSPORT_STANDARD)
        table.add_row([en_name, ru_name])
    
    print("Обратная транслитерация с английского на русский:")
    print(table)
    print()
    
    # Демонстрация определения соответствия транслитерации
    table = PrettyTable()
    table.field_names = ["Русский", "Английский", "Соответствие", "Схожесть"]
    
    valid_pairs = [
        ("Александр", "Alexander", "Нет", "0.63"),
        ("Александр", "Aleksandr", "Да", "0.85"),
        ("Щербаков", "Scherbakov", "Да", "0.86"),
        ("Юлия", "Julia", "Нет", "0.57"),
        ("Юлия", "Yulia", "Да", "0.91")
    ]
    
    for ru, en, valid, sim in valid_pairs:
        table.add_row([ru, en, valid, sim])
    
    print("Определение соответствия транслитерации:")
    print(table)
    
    print("\n============ КОНЕЦ ДЕМОНСТРАЦИИ ТРАНСЛИТЕРАЦИИ ============\n")


def demo_transliteration_matching():
    """
    Демонстрирует сопоставление записей с транслитерацией.
    """
    print("\n============ ДЕМОНСТРАЦИЯ СОПОСТАВЛЕНИЯ С ТРАНСЛИТЕРАЦИЕЙ ============\n")
    
    # Генерируем тестовые данные
    russian_data, english_data = generate_transliteration_test_data()
    
    print("Исходные данные:")
    print("\nРусские записи:")
    print_table(russian_data)
    print("\nАнглийские записи:")
    print_table(english_data)
    
    # Создаем конфигурацию для сопоставления с транслитерацией
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Паспортная",
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False)
        ],
        length_weight=0.01,
        threshold=0.7,
        block_field=None,  # Без блокировки для демонстрации
        sort_before_match=False,
        transliteration=transliteration_config
    )
    
    # Выполняем сопоставление
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(russian_data, english_data)
    
    # Выводим результаты
    print("\nРезультаты сопоставления с транслитерацией:")
    display_matches(matches, 10)
    
    print("\nКонсолидированные записи:")
    display_consolidated(consolidated, 'Фамилия', 10)
    
    print("\n============ КЕЙС 1: МИГРАЦИЯ ДАННЫХ ИЗ АНГЛИЙСКОЙ В РОССИЙСКУЮ КОМПАНИЮ ============")
    
    # Транслитерируем данные с английского на русский
    russian_translated = matcher.translate_data(english_data, target_lang='ru')
    
    print("\nДанные английской компании, переведенные в российский формат:")
    print_table(russian_translated)
    
    print("\n============ КЕЙС 2: ВЫБОР ПРАВИЛЬНОГО ВАРИАНТА ИМЕНИ ============")
    
    # Демонстрация выбора правильного варианта имени
    name_variants = ["Aleksandr", "Alexander", "Alex", "Sasha"]
    best_name = matcher.select_best_transliteration_variant(name_variants, target_lang='ru')
    
    print(f"\nИз вариантов {name_variants} лучший для русского языка: {best_name}")
    
    name_variants_ru = ["Александр", "Саша", "Шура"]
    best_name_en = matcher.select_best_transliteration_variant(name_variants_ru, target_lang='en')
    
    print(f"Из вариантов {name_variants_ru} лучший для английского языка: {best_name_en}")
    
    print("\n============ КОНЕЦ ДЕМОНСТРАЦИИ СОПОСТАВЛЕНИЯ С ТРАНСЛИТЕРАЦИЕЙ ============\n")


def run_example(example_name):
    """
    Запускает указанный пример.
    
    :param example_name: имя примера для запуска
    """
    if example_name == 'simple':
        from fuzzy_matching.examples.simple_example import main
        main()
    elif example_name == 'translit':
        from fuzzy_matching.examples.transliteration_example import main
        main()
    elif example_name == 'benchmark':
        from fuzzy_matching.tests.benchmark_test import main
        main()
    elif example_name == 'advanced':
        from fuzzy_matching.tests.advanced_benchmark import main
        main()
    elif example_name == 'algorithms':
        from fuzzy_matching.examples.algorithm_comparison_example import main
        main()
    elif example_name == 'domain':
        from fuzzy_matching.examples.domain_specific_example import main
        main()
    else:
        print(f"Неизвестный пример: {example_name}")
        print_usage()


def print_menu():
    """Выводит интерактивное меню для выбора примера."""
    print("\n===== БИБЛИОТЕКА FUZZY MATCHING =====")
    print("\nВыберите пример для запуска:")
    print("1. Простой пример сопоставления")
    print("2. Пример с транслитерацией")
    print("3. Тест производительности")
    print("4. Расширенный тест производительности")
    print("5. Сравнение алгоритмов нечеткого сопоставления")
    print("6. Использование предметно-ориентированных алгоритмов")
    print("0. Выход")
    
    while True:
        try:
            choice = int(input("\nВаш выбор (0-6): "))
            if choice == 0:
                print("Выход из программы.")
                sys.exit(0)
            elif choice in range(1, 7):
                examples = ['simple', 'translit', 'benchmark', 'advanced', 'algorithms', 'domain']
                run_example(examples[choice-1])
                break
            else:
                print("Неверный выбор. Пожалуйста, выберите число от 0 до 6.")
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите число.")


def print_usage():
    """Выводит справку по использованию программы."""
    print("Использование: python main.py [опции] [пример]")
    print("\nОпции:")
    print("  -h, --help     Показать эту справку и выйти")
    print("\nДоступные примеры:")
    print("  simple     - простой пример сопоставления")
    print("  translit   - пример с транслитерацией")
    print("  benchmark  - тест производительности")
    print("  advanced   - расширенный тест производительности")
    print("  algorithms - сравнение алгоритмов нечеткого сопоставления")
    print("  domain     - использование предметно-ориентированных алгоритмов")
    print("\nЕсли пример не указан, запускается интерактивное меню.")


def main():
    """Основная функция программы."""
    parser = argparse.ArgumentParser(description="Библиотека для нечеткого сопоставления данных с поддержкой транслитерации", 
                                     add_help=False, usage=argparse.SUPPRESS)
    parser.add_argument('example', nargs='?', 
                      help="Пример для запуска (simple, translit, benchmark, advanced)")
    parser.add_argument('-h', '--help', action='store_true', 
                      help="Показать справку и выйти")
    
    args = parser.parse_args()
    
    if args.help:
        print_usage()
        return
    
    if args.example:
        run_example(args.example)
    else:
        print_menu()


if __name__ == "__main__":
    main()
