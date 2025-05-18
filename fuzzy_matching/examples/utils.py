"""
Общие утилиты для примеров использования библиотеки fuzzy_matching.

Этот модуль содержит вспомогательные функции, используемые в различных примерах.
"""

import os
import json
from prettytable import PrettyTable


def print_table(data, limit=None):
    """
    Выводит данные в виде форматированной таблицы.
    
    :param data: список словарей с данными
    :param limit: максимальное количество строк для отображения
    """
    if not data:
        print("Нет данных для отображения")
        return

    table = PrettyTable()
    table.field_names = data[0].keys()
    
    # Если указан лимит, ограничиваем количество строк
    rows_to_display = data[:limit] if limit is not None else data
    
    for row in rows_to_display:
        table.add_row(row.values())

    table.align = 'l'
    print(table)


def print_matches(matches, limit=5):
    """
    Выводит результаты совпадений в виде таблицы.
    
    :param matches: список найденных совпадений
    :param limit: максимальное количество строк для отображения
    """
    if not matches:
        print("Совпадений не найдено")
        return
        
    table = PrettyTable()
    table.field_names = ["Запись 1", "Запись 2", "Совпадение"]
    
    # Если указан лимит, ограничиваем количество строк
    matches_to_display = matches[:limit] if limit is not None else matches
    
    for match in matches_to_display:
        rec1 = " ".join(match["Запись 1"])
        rec2 = " ".join(match["Запись 2"])
        score = f"{match['Совпадение'][0]:.2f}"
        table.add_row([rec1, rec2, score])
    
    table.align["Запись 1"] = "l"
    table.align["Запись 2"] = "l"
    table.align["Совпадение"] = "r"
    
    print(f"\nНайдено совпадений: {len(matches)}")
    print(table)


def save_example_results(matches, consolidated, prefix="example", results_dir="results"):
    """
    Сохраняет результаты сопоставления в файлы.
    
    :param matches: список найденных совпадений
    :param consolidated: список консолидированных записей
    :param prefix: префикс для имен файлов
    :param results_dir: директория для сохранения результатов
    """
    # Создаем директорию для результатов, если ее нет
    os.makedirs(results_dir, exist_ok=True)
    
    # Сохраняем совпадения
    matches_file = os.path.join(results_dir, f"{prefix}_matches.json")
    with open(matches_file, 'w', encoding='utf-8') as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    
    # Сохраняем консолидированные данные
    consolidated_file = os.path.join(results_dir, f"{prefix}_consolidated.json")
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)
    
    print(f"\nРезультаты сохранены в директории {results_dir}:")
    print(f"- Совпадения: {matches_file}")
    print(f"- Консолидированные данные: {consolidated_file}")


def generate_example_data(generator, count=10, fields=None):
    """
    Генерирует примеры данных для демонстрации.
    
    :param generator: экземпляр DataGenerator
    :param count: количество записей для генерации
    :param fields: список полей для генерации
    :return: кортеж (оригинальные данные, вариантные данные)
    """
    if fields is None:
        fields = ['Фамилия', 'Имя', 'Отчество', 'email']
        
    # Генерируем пару наборов данных
    original_data, variant_data = generator.generate_records_pair(count, fields)
    
    return original_data, variant_data 