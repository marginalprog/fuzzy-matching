#!/usr/bin/env python
"""
Тестовый скрипт для отладки сопоставления данных.
"""

import json
import os
from pprint import pprint

from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.core.data_matcher import DataMatcher

# Загружаем данные
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
original_file = os.path.join(data_dir, 'simple_original.json')
variant_file = os.path.join(data_dir, 'simple_variant.json')

with open(original_file, 'r', encoding='utf-8') as f:
    original_data = json.load(f)

with open(variant_file, 'r', encoding='utf-8') as f:
    variant_data = json.load(f)

# Создаем конфигурацию для сопоставления
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
    MatchFieldConfig(field='Отчество', weight=0.3, transliterate=True)
]

config = MatchConfig(
    fields=match_fields,
    threshold=0.5,
    transliteration=transliteration_config
)

# Создаем matcher и выполняем сопоставление
matcher = DataMatcher(config=config)

print("Оригинальные данные:")
pprint(original_data[0])
print("\nИскаженные данные:")
pprint(variant_data[0])

print("\nВыполняем сопоставление...")
for record1 in original_data[:1]:
    for record2 in variant_data[:1]:
        similarity = matcher._weighted_average_similarity(record1, record2)
        print(f"Совпадение между {record1['id']} и {record2['id']}: {similarity[0]:.2f}")
        
        # Выводим детали совпадения
        print("Детали совпадения:")
        for field_sim in similarity[1]:
            field_name, val1, val2, sim = field_sim
            print(f"  {field_name}: '{val1}' <-> '{val2}' = {sim:.2f}")

print("\nВыполняем полное сопоставление...")
matches, consolidated = matcher.match_and_consolidate(original_data, variant_data)

print(f"Найдено {len(matches)} совпадений")
if matches:
    print("Первое совпадение:")
    pprint(matches[0])
else:
    print("Совпадений не найдено")
    
    # Проверяем первую запись подробнее
    record1 = original_data[0]
    record2 = variant_data[0]
    
    print("\nПроверяем первую запись подробнее:")
    for field in ['Фамилия', 'Имя', 'Отчество']:
        value1 = record1.get(field, '')
        value2 = record2.get(field, '')
        
        # Пробуем сопоставить по каждому полю отдельно
        result = matcher._process_transliteration(value1, value2, field)
        print(f"Поле '{field}': '{value1}' <-> '{value2}' = {result[2]:.2f}")

print("\nКонсолидировано записей:", len(consolidated)) 