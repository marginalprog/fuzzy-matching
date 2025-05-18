#!/usr/bin/env python
"""
Пример использования fuzzy_matching для технических данных.
Демонстрирует сопоставление серийных номеров, артикулов и технических описаний.
"""

import os
from pprint import pprint

from fuzzy_matching.api import (
    create_config, 
    match_datasets, 
    save_results
)
from fuzzy_matching.examples.utils import print_table, print_matches, save_example_results
from fuzzy_matching.examples.data_examples import TECH_DATA_ORIGINAL, TECH_DATA_VARIANT


def demo_tech_matching():
    """
    Демонстрирует сопоставление технических данных с оптимальными алгоритмами.
    """
    print("\n=== Пример сопоставления технических данных ===")
    
    # Создаем директорию для результатов, если ее нет
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    tech_data_original = TECH_DATA_ORIGINAL
    tech_data_variant = TECH_DATA_VARIANT
    
    print(f"Подготовлено {len(tech_data_original)} оригинальных и {len(tech_data_variant)} вариантных записей")
    print("\nПример оригинальной записи:")
    pprint(tech_data_original[0])
    print("\nПример вариантной записи с опечатками:")
    pprint(tech_data_variant[0])
    
    # Создаем конфигурацию с оптимальными алгоритмами для технических данных
    tech_config = create_config(
        fields=[
            # Для серийных номеров и артикулов используем RATIO (важна точность)
            {"field": "серийный_номер", "weight": 0.3, "transliterate": False, "algorithm": "RATIO"},
            {"field": "артикул", "weight": 0.3, "transliterate": False, "algorithm": "RATIO"},
            # Для кодов моделей тоже RATIO, но с меньшим весом
            {"field": "код_модели", "weight": 0.2, "transliterate": False, "algorithm": "RATIO"},
            # Для описаний используем TOKEN_SET (учитывает перестановку слов)
            {"field": "описание", "weight": 0.2, "transliterate": False, "algorithm": "TOKEN_SET"}
        ],
        threshold=0.7,  # Порог схожести
        fuzzy_algorithm="RATIO"  # Алгоритм по умолчанию
    )
    
    # Сопоставляем наборы данных
    matches, consolidated = match_datasets(
        dataset1=tech_data_original,
        dataset2=tech_data_variant,
        config=tech_config
    )
    
    print(f"\nНайдено {len(matches)} совпадений")
    print(f"Консолидировано {len(consolidated)} записей")
    
    if matches:
        print("\nПримеры найденных совпадений:")
        for i, match in enumerate(matches[:3]):  # Показываем до 3 совпадений
            print(f"\nСовпадение {i+1}:")
            print(f"  Оригинал: {match['Запись 1'][0]} - {match['Запись 1'][3]}")
            print(f"  Вариант: {match['Запись 2'][0]} - {match['Запись 2'][3]}")
            print(f"  Общая схожесть: {match['Совпадение'][0]:.2f}")
            
            # Показываем схожесть по отдельным полям
            print("  Схожесть по полям:")
            for field_sim in match['Совпадение'][1]:
                if isinstance(field_sim, tuple) and len(field_sim) >= 4:
                    field, val1, val2, sim = field_sim
                    print(f"    - {field}: {sim:.2f}")
    
    # Сохраняем результаты
    save_example_results(matches, consolidated, prefix="tech", results_dir=results_dir)
    
    return matches, consolidated


def demo_serial_number_focus():
    """
    Демонстрирует сопоставление с фокусом только на серийных номерах и артикулах.
    """
    print("\nТеперь попробуем с другой конфигурацией, оптимизированной для серийных номеров")
    
    # Создаем другую конфигурацию, сфокусированную только на серийных номерах и артикулах
    serial_config = create_config(
        fields=[
            # Только серийные номера с высоким весом
            {"field": "серийный_номер", "weight": 0.7, "transliterate": False, "algorithm": "RATIO"},
            {"field": "артикул", "weight": 0.3, "transliterate": False, "algorithm": "RATIO"}
        ],
        threshold=0.8,  # Повышаем порог схожести
        fuzzy_algorithm="RATIO"
    )
    
    # Сопоставляем повторно
    serial_matches, serial_consolidated = match_datasets(
        dataset1=TECH_DATA_ORIGINAL,
        dataset2=TECH_DATA_VARIANT,
        config=serial_config
    )
    
    print(f"\nПри фокусе только на серийных номерах и артикулах:")
    print(f"Найдено {len(serial_matches)} совпадений")
    
    # Сохраняем результаты
    save_example_results(serial_matches, serial_consolidated, prefix="tech_serial", results_dir="results")
    
    return serial_matches, serial_consolidated


def print_tech_data_comparison():
    """
    Выводит пример сопоставления технических данных в виде таблицы.
    """
    # Создаем таблицу
    from prettytable import PrettyTable
    table = PrettyTable()
    table.field_names = ["Поле", "Оригинал", "Вариант с искажениями", "Алгоритм", "Схожесть"]
    
    # Добавляем строки
    table.add_row(["Серийный номер", "SN20220501-001", "SN20220501-O01", "RATIO", "0.92"])
    table.add_row(["Артикул", "ABC-123456", "ABC123456", "RATIO", "0.89"])
    table.add_row(["Код модели", "INTCPU12700K", "INTCPU12700k", "RATIO", "0.95"])
    table.add_row(["Описание", "Процессор Intel Core i7-12700K 3.6 ГГц 12 ядер Socket 1700", 
                  "Intel Core i7-12700K процессор Socket 1700 3.6 ГГц 12 ядер", "TOKEN_SET", "0.98"])
    
    # Настраиваем таблицу
    table.align = "l"
    table.max_width["Описание"] = 50
    
    # Выводим таблицу
    print("\n=== Пример сопоставления технических данных ===\n")
    print(table)
    
    # Выводим рекомендации
    print("\n=== Результаты анализа эффективности алгоритмов ===\n")
    print("1. Для серийных номеров и артикулов:")
    print("   - Оптимальный алгоритм: RATIO")
    print("   - Причина: Для точных технических идентификаторов важно точное совпадение символов")
    print("\n2. Для технических описаний:")
    print("   - Оптимальный алгоритм: TOKEN_SET")
    print("   - Причина: Порядок слов в описаниях часто меняется, но набор ключевых характеристик остается тем же")


def main():
    """
    Основная функция примера.
    """
    print("===== ПРИМЕР СОПОСТАВЛЕНИЯ ТЕХНИЧЕСКИХ ДАННЫХ =====\n")
    
    # Демонстрация сопоставления технических данных
    demo_tech_matching()
    
    # Демонстрация сопоставления с фокусом на серийных номерах
    demo_serial_number_focus()
    
    # Вывод сравнительной таблицы
    print_tech_data_comparison()
    
    # Вывод рекомендаций
    print("\nВывод: правильный выбор алгоритмов и весов полей существенно влияет на результат сопоставления.")
    print("Для технических данных рекомендуется использовать:")
    print("- RATIO для серийных номеров, артикулов и кодов (когда важна точность)")
    print("- TOKEN_SET для технических описаний (когда порядок слов может меняться)")
    
    print("\n===== ЗАВЕРШЕНИЕ ПРИМЕРА =====")


if __name__ == "__main__":
    main() 