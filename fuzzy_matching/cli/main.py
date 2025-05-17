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
from fuzzy_matching.utils.transliteration.transliteration_utils import *


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
    
    print("\nТранслитерация по стандарту ГОСТ:")
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
    print("\n=== Демонстрация сопоставления с транслитерацией ===\n")
    
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
    print("  python -m fuzzy_matching.cli.main [пример]")
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