#!/usr/bin/env python
"""
Пример использования API модуля fuzzy_matching.
Демонстрирует основные возможности библиотеки через простой программный интерфейс.
"""

import os
from pprint import pprint

from fuzzy_matching.api import (
    create_config, 
    match_datasets, 
    transliterate_dataset, 
    generate_test_datasets, 
    save_results
)
from fuzzy_matching.examples.utils import print_table, save_example_results


def demo_generate_data():
    """
    Демонстрирует генерацию тестовых данных.
    """
    print("\n=== Пример 1: Генерация тестовых данных ===")
    
    # Создаем директорию для результатов, если ее нет
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Генерируем тестовые данные
    original_data, variant_data = generate_test_datasets(
        count=100,
        double_char_probability=0.2,
        change_char_probability=0.1,
        change_name_probability=0.1,
        change_domain_probability=0.3,
        double_number_probability=0.3,
        suffix_probability=0.1,
        save_to_file=True,
        output_original=os.path.join(results_dir, 'api_original.json'),
        output_variant=os.path.join(results_dir, 'api_variant.json')
    )
    
    print(f"Сгенерировано {len(original_data)} оригинальных и {len(variant_data)} искаженных записей")
    print("\nПример оригинальной записи:")
    pprint(original_data[0])
    print("\nПример искаженной записи:")
    pprint(variant_data[0])
    
    return original_data, variant_data


def demo_transliteration(original_data):
    """
    Демонстрирует транслитерацию данных.
    
    :param original_data: исходные данные для транслитерации
    """
    print("\n\n=== Пример 2: Транслитерация данных ===")
    
    # Используем сгенерированные данные для транслитерации
    transliterated_data = transliterate_dataset(
        dataset=original_data,
        target_lang='en',
        fields=['Фамилия', 'Имя', 'Отчество']
    )
    
    print(f"Транслитерировано {len(transliterated_data)} записей")
    print("\nПример записи до транслитерации:")
    pprint(original_data[0])
    print("\nПример транслитерированной записи:")
    pprint(transliterated_data[0])
    
    # Сохраняем транслитерированные данные в директорию results
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    with open(os.path.join(results_dir, 'api_transliterated.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(transliterated_data, f, ensure_ascii=False, indent=2)
    
    return transliterated_data


def demo_matching(original_data, transliterated_data):
    """
    Демонстрирует сопоставление наборов данных.
    
    :param original_data: первый набор данных
    :param transliterated_data: второй набор данных
    """
    print("\n\n=== Пример 3: Сопоставление наборов данных ===")
    
    # Создаем конфигурацию с включенной транслитерацией
    config = create_config(
        fields=[
            {"field": "Фамилия", "weight": 0.5, "transliterate": True, "algorithm": "TOKEN_SORT"},
            {"field": "Имя", "weight": 0.3, "transliterate": True, "algorithm": "PARTIAL_RATIO"},
            {"field": "Отчество", "weight": 0.2, "transliterate": True, "algorithm": "RATIO"}
        ],
        threshold=0.7,
        transliteration_enabled=True,
        fuzzy_algorithm="WRatio"  # Алгоритм по умолчанию для полей без явного указания
    )
    
    # Сопоставляем исходные данные с транслитерированными
    matches, consolidated = match_datasets(
        dataset1=original_data,
        dataset2=transliterated_data,
        config=config
    )
    
    print(f"Найдено {len(matches)} совпадений")
    print(f"Консолидировано {len(consolidated)} записей")
    
    if matches:
        print("\nПример найденного совпадения:")
        pprint(matches[0])
    else:
        print("\nСовпадений не найдено")
    
    if consolidated:
        print("\nПример консолидированной записи:")
        pprint(consolidated[0])
    
    # Сохраняем результаты
    save_example_results(matches, consolidated, prefix="api", results_dir="results")


def main():
    """
    Основная функция примера.
    """
    print("===== ПРИМЕР ИСПОЛЬЗОВАНИЯ API FUZZY MATCHING =====")
    
    # Демонстрация генерации данных
    original_data, variant_data = demo_generate_data()
    
    # Демонстрация транслитерации
    transliterated_data = demo_transliteration(original_data)
    
    # Демонстрация сопоставления
    demo_matching(original_data, transliterated_data)
    
    print("\nПример успешно завершен!")
    print("===== ЗАВЕРШЕНИЕ ПРИМЕРА =====")


if __name__ == "__main__":
    print("Запустите этот пример с помощью команды:")
    print("python -m fuzzy_matching.examples.api_example")
    main() 