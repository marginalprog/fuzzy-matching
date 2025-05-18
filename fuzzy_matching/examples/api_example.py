#!/usr/bin/env python
"""
Пример использования API модуля fuzzy_matching.
Демонстрирует основные возможности библиотеки через простой программный интерфейс.
"""

import os
import json
from pprint import pprint

from fuzzy_matching.api import (
    create_config, 
    match_datasets, 
    transliterate_dataset, 
    generate_test_datasets, 
    save_results
)

# Создаем директорию для результатов, если ее нет
results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
os.makedirs(results_dir, exist_ok=True)

# Пример 1: Генерация тестовых данных
print("\n=== Пример 1: Генерация тестовых данных ===")
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

# Пример 2: Транслитерация данных
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

# Сохраняем транслитерированные данные
with open(os.path.join(results_dir, 'api_transliterated.json'), 'w', encoding='utf-8') as f:
    json.dump(transliterated_data, f, ensure_ascii=False, indent=2)

# Пример 3: Сопоставление наборов данных
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
save_results(
    matches=matches,
    consolidated=consolidated,
    matches_file=os.path.join(results_dir, 'api_matches.json'),
    consolidated_file=os.path.join(results_dir, 'api_consolidated.json')
)

print(f"\nРезультаты сохранены в директории {results_dir}")
print("Пример успешно завершен!")


if __name__ == "__main__":
    print("Запустите этот пример с помощью команды:")
    print("python -m fuzzy_matching.examples.api_example") 