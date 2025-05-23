#!/usr/bin/env python
"""
Демонстрационный скрипт для библиотеки fuzzy_matching.

Этот скрипт показывает основные возможности библиотеки на практических примерах:
1. Генерация тестовых данных
2. Базовое сопоставление данных
3. Сопоставление с транслитерацией
4. Специализированные алгоритмы для разных типов данных
5. Загрузка и сохранение данных из/в CSV/JSON

Запуск:
    python -m fuzzy_matching.examples.demo_usage
"""

import os
import json
import pandas as pd
from prettytable import PrettyTable

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig,
    FuzzyAlgorithm
)
from fuzzy_matching.utils.data_generator import DataGenerator, Language
from fuzzy_matching.examples.utils import print_table, print_matches, save_example_results, generate_example_data
from fuzzy_matching.examples.data_examples import PERSONAL_DATA_RU, PERSONAL_DATA_EN


def demo_generate_data():
    """
    Демонстрирует генерацию тестовых данных с различными настройками.
    """
    print("\n===== ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ =====\n")
    
    # Настройки генератора данных
    probabilities = {
        'double_letter': 0.2,  # Вероятность дублирования буквы
        'change_letter': 0.3,  # Вероятность замены буквы
        'change_name': 0.1,    # Вероятность полной замены имени
        'change_name_domain': 0.2,  # Вероятность замены домена в email
        'double_number': 0.2,  # Вероятность дублирования цифры
        'suffix_addition': 0.1  # Вероятность добавления суффикса
    }
    
    print("1. Генерация русских данных:")
    generator_ru = DataGenerator(language=Language.RUS, probabilities=probabilities)
    fields = ['Фамилия', 'Имя', 'Отчество', 'email', 'Телефон']
    
    # Генерация чистых данных
    clean_data = generator_ru.generate_clean_records_list(10, fields)
    print("\nЧистые данные:")
    print_table(clean_data, 5)
    
    # Генерация пары наборов данных (оригинальный и искаженный)
    original_data, variant_data = generate_example_data(generator_ru, 10, fields)
    print("\nОригинальные данные:")
    print_table(original_data, 3)
    print("\nИскаженные данные:")
    print_table(variant_data, 3)
    
    print("\n2. Генерация английских данных:")
    generator_en = DataGenerator(language=Language.ENG, probabilities=probabilities)
    fields_en = ['Last Name', 'First Name', 'Middle Name', 'email', 'Phone']
    
    # Генерация английских данных с правильными полями
    en_data = generator_en.generate_clean_records_list(5, fields_en)
    
    # Убедимся, что все поля присутствуют в данных
    for record in en_data:
        for field in fields_en:
            if field not in record:
                record[field] = f"Example {field}"
    
    print("\nАнглийские данные:")
    print_table(en_data)
    
    # Использование примеров из data_examples.py
    print("\n3. Примеры русских и английских данных:")
    print("\nРусские данные из примеров:")
    print_table(PERSONAL_DATA_RU)
    
    print("\nАнглийские данные из примеров:")
    print_table(PERSONAL_DATA_EN)
    
    # Сохранение данных в файлы
    if not os.path.exists('demo_data'):
        os.makedirs('demo_data')
    
    generator_ru.save_to_json(original_data, 'demo_data/original_ru.json')
    generator_ru.save_to_json(variant_data, 'demo_data/variant_ru.json')
    generator_ru.save_to_csv(original_data, 'demo_data/original_ru.csv')
    generator_ru.save_to_csv(variant_data, 'demo_data/variant_ru.csv')
    
    print("\nДанные сохранены в директорию 'demo_data'")
    
    return original_data, variant_data


def demo_basic_matching(original_data, variant_data):
    """
    Демонстрирует базовое сопоставление данных.
    
    :param original_data: оригинальный набор данных
    :param variant_data: искаженный набор данных
    """
    print("\n===== БАЗОВОЕ СОПОСТАВЛЕНИЕ ДАННЫХ =====\n")
    
    # Создаем конфигурацию для сопоставления
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4),
            MatchFieldConfig(field='Имя', weight=0.3),
            MatchFieldConfig(field='Отчество', weight=0.2),
            MatchFieldConfig(field='email', weight=0.1)
        ],
        length_weight=0.01,  # Вес разницы в длине строк
        threshold=0.7,       # Порог схожести для сопоставления
        block_field='Фамилия',  # Поле для блокировки (ускорение)
        sort_before_match=True  # Сортировка данных перед сопоставлением
    )
    
    # Создаем экземпляр DataMatcher
    matcher = DataMatcher(config=match_config)
    
    # Выполняем сопоставление
    matches, consolidated = matcher.match_and_consolidate(original_data, variant_data)
    
    # Выводим результаты
    print_matches(matches)
    
    print("\nКонсолидированные данные:")
    print_table(consolidated)
    
    # Сохраняем результаты
    matcher.save_matches_to_json(matches, 'demo_data/basic_matches.json')
    matcher.save_consolidated_to_json(consolidated, 'demo_data/basic_consolidated.json')
    
    print("\nРезультаты сохранены в директорию 'demo_data'")
    
    return matcher, matches, consolidated


def demo_transliteration():
    """
    Демонстрирует сопоставление данных с транслитерацией.
    """
    print("\n===== СОПОСТАВЛЕНИЕ С ТРАНСЛИТЕРАЦИЕЙ =====\n")
    
    # Используем данные из модуля data_examples
    russian_data = PERSONAL_DATA_RU[:3]
    english_data = PERSONAL_DATA_EN[:3]
    
    print("Данные на русском:")
    print_table(russian_data)
    
    print("\nДанные на английском:")
    print_table(english_data)
    
    # Настройка конфигурации с транслитерацией
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Passport",  # Стандарт транслитерации
        threshold=0.7,          # Порог схожести для транслитерации
        auto_detect=True,       # Автоопределение языка
        normalize_names=True    # Нормализация имен
    )
    
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False)
        ],
        threshold=0.7,
        transliteration=transliteration_config
    )
    
    # Выполняем сопоставление
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(russian_data, english_data)
    
    # Выводим результаты
    print("\nРезультаты сопоставления с транслитерацией:")
    print_matches(matches)
    
    print("\nКонсолидированные данные:")
    print_table(consolidated)
    
    # Демонстрация транслитерации данных
    print("\nТранслитерация русских данных на английский:")
    transliterated_en = matcher.transliterate_data(russian_data, target_lang='en')
    print_table(transliterated_en)
    
    print("\nТранслитерация английских данных на русский:")
    transliterated_ru = matcher.transliterate_data(english_data, target_lang='ru')
    print_table(transliterated_ru)
    
    return matcher, matches, consolidated


def demo_domain_specific():
    """
    Демонстрирует использование специализированных алгоритмов для различных типов данных.
    """
    print("\n===== СПЕЦИАЛИЗИРОВАННЫЕ АЛГОРИТМЫ ДЛЯ РАЗНЫХ ТИПОВ ДАННЫХ =====\n")
    
    # Данные о людях
    person_data1 = [
        {'id': 1, 'Фамилия': 'Иванов', 'Имя': 'Иван', 'Отчество': 'Иванович', 'email': 'ivanov@example.com'},
        {'id': 2, 'Фамилия': 'Петров', 'Имя': 'Петр', 'Отчество': 'Петрович', 'email': 'petrov@example.com'}
    ]
    
    person_data2 = [
        {'id': 'a', 'Фамилия': 'Иванов', 'Имя': 'Иван', 'Отчество': 'Иваныч', 'email': 'i.ivanov@example.com'},
        {'id': 'b', 'Фамилия': 'Петров', 'Имя': 'Петр', 'Отчество': 'Петровичь', 'email': 'p.petrov@example.com'}
    ]
    
    # Данные о товарах
    product_data1 = [
        {'id': 1, 'Название': 'Смартфон Samsung Galaxy S21', 'Категория': 'Электроника', 'Цена': 59999},
        {'id': 2, 'Название': 'Ноутбук Apple MacBook Pro 13"', 'Категория': 'Компьютеры', 'Цена': 129999}
    ]
    
    product_data2 = [
        {'id': 'a', 'Название': 'Samsung Galaxy S21 5G', 'Категория': 'Смартфоны', 'Цена': 61999},
        {'id': 'b', 'Название': 'MacBook Pro 13 2020', 'Категория': 'Ноутбуки', 'Цена': 128999}
    ]
    
    # Данные о компаниях
    company_data1 = [
        {'id': 1, 'Название': 'ООО "Инновационные технологии"', 'Адрес': 'г. Москва, ул. Ленина, 10', 'ИНН': '7701123456'},
        {'id': 2, 'Название': 'АО "ТехноСервис"', 'Адрес': 'г. Санкт-Петербург, пр. Невский, 100', 'ИНН': '7801234567'}
    ]
    
    company_data2 = [
        {'id': 'a', 'Название': 'Инновационные технологии ООО', 'Адрес': 'Москва, Ленина 10', 'ИНН': '7701123456'},
        {'id': 'b', 'Название': 'ТехноСервис', 'Адрес': 'СПб, Невский проспект, 100', 'ИНН': '7801234567'}
    ]
    
    # Демонстрация для персональных данных
    print("1. Сопоставление персональных данных:")
    person_fields = [
        MatchFieldConfig(field='Фамилия', weight=0.4, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SORT),
        MatchFieldConfig(field='Имя', weight=0.3, fuzzy_algorithm=FuzzyAlgorithm.PARTIAL_RATIO),
        MatchFieldConfig(field='Отчество', weight=0.2, fuzzy_algorithm=FuzzyAlgorithm.RATIO),
        MatchFieldConfig(field='email', weight=0.1, fuzzy_algorithm=FuzzyAlgorithm.RATIO)
    ]
    
    person_config = MatchConfig(
        fields=person_fields,
        threshold=0.7,
        fuzzy_algorithm=FuzzyAlgorithm.PARTIAL_RATIO  # Базовый алгоритм, если для поля не указан
    )
    
    person_matcher = DataMatcher(config=person_config)
    person_matches, _ = person_matcher.match_and_consolidate(person_data1, person_data2)
    print_matches(person_matches)
    
    # Демонстрация для товаров
    print("\n2. Сопоставление данных о товарах:")
    product_fields = [
        MatchFieldConfig(field='Название', weight=0.8, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET),
        MatchFieldConfig(field='Категория', weight=0.2, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET)
    ]
    
    product_config = MatchConfig(
        fields=product_fields,
        threshold=0.7,
        fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET
    )
    
    product_matcher = DataMatcher(config=product_config)
    product_matches, _ = product_matcher.match_and_consolidate(product_data1, product_data2)
    print_matches(product_matches)
    
    # Демонстрация для компаний
    print("\n3. Сопоставление данных о компаниях:")
    company_fields = [
        MatchFieldConfig(field='Название', weight=0.6, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET),
        MatchFieldConfig(field='Адрес', weight=0.2, fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SORT),
        MatchFieldConfig(field='ИНН', weight=0.2, fuzzy_algorithm=FuzzyAlgorithm.RATIO)
    ]
    
    company_config = MatchConfig(
        fields=company_fields,
        threshold=0.7,
        fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SET
    )
    
    company_matcher = DataMatcher(config=company_config)
    company_matches, _ = company_matcher.match_and_consolidate(company_data1, company_data2)
    print_matches(company_matches)
    
    print("\nСравнение подходов:")
    print("- Для персональных данных: TOKEN_SORT для фамилий, PARTIAL_RATIO для имен")
    print("- Для товаров: TOKEN_SET для всех полей (учитывает перемешанные слова)")
    print("- Для компаний: TOKEN_SET для названий, TOKEN_SORT для адресов")


def demo_file_operations():
    """
    Демонстрирует операции с файлами (загрузка, сохранение).
    """
    print("\n===== ОПЕРАЦИИ С ФАЙЛАМИ =====\n")
    
    # Создаем тестовые данные
    data = [
        {
            'id': 1,
            'Фамилия': 'Иванов',
            'Имя': 'Иван',
            'Отчество': 'Иванович',
            'email': 'ivanov@example.com',
            'Телефон': '+7 (999) 123-45-67'
        },
        {
            'id': 2,
            'Фамилия': 'Петров',
            'Имя': 'Петр',
            'Отчество': 'Петрович',
            'email': 'petrov@example.com',
            'Телефон': '+7 (999) 765-43-21'
        },
        {
            'id': 3,
            'Фамилия': 'Сидорова',
            'Имя': 'Елена',
            'Отчество': 'Александровна',
            'email': 'sidorova@example.com',
            'Телефон': '+7 (999) 111-22-33'
        }
    ]
    
    # Создаем директорию для файлов, если её нет
    if not os.path.exists('demo_data'):
        os.makedirs('demo_data')
    
    # Сохраняем данные в JSON
    json_path = 'demo_data/test_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Данные сохранены в JSON: {json_path}")
    
    # Сохраняем данные в CSV
    csv_path = 'demo_data/test_data.csv'
    pd.DataFrame(data).to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Данные сохранены в CSV: {csv_path}")
    
    # Создаем экземпляр DataMatcher с пустой конфигурацией
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4),
            MatchFieldConfig(field='Имя', weight=0.3),
            MatchFieldConfig(field='Отчество', weight=0.2),
            MatchFieldConfig(field='email', weight=0.1)
        ],
        threshold=0.7
    )
    matcher = DataMatcher(config=match_config)
    
    # Определяем соответствие полей
    name_fields = {
        'Фамилия': 'Фамилия',
        'Имя': 'Имя',
        'Отчество': 'Отчество',
        'email': 'email',
        'Телефон': 'Телефон',
        'id': 'id'
    }
    
    # Загружаем данные из JSON
    json_data = matcher.load_from_json(json_path, name_fields)
    print("\nДанные, загруженные из JSON:")
    print_table(json_data)
    
    # Загружаем данные из CSV
    csv_data = matcher.load_from_csv(csv_path, name_fields)
    print("\nДанные, загруженные из CSV:")
    print_table(csv_data)
    
    # Демонстрация сопоставления полей при загрузке
    print("\nЗагрузка с сопоставлением полей:")
    field_mapping = {
        'id': 'ID',
        'Фамилия': 'LastName',
        'Имя': 'FirstName',
        'Отчество': 'MiddleName',
        'email': 'email',
        'Телефон': 'Phone'
    }
    
    mapped_data = matcher.load_from_json(json_path, field_mapping)
    print("\nДанные с переименованными полями:")
    print_table(mapped_data)


def main():
    print("===== ДЕМОНСТРАЦИЯ БИБЛИОТЕКИ FUZZY MATCHING =====\n")
    
    # Генерация тестовых данных
    original_data, variant_data = demo_generate_data()
    
    # Базовое сопоставление
    demo_basic_matching(original_data, variant_data)
    
    # Сопоставление с транслитерацией
    demo_transliteration()
    
    # Специализированные алгоритмы для различных типов данных
    demo_domain_specific()
    
    # Операции с файлами
    demo_file_operations()
    
    print("\n===== ЗАВЕРШЕНИЕ ДЕМОНСТРАЦИИ =====")
    print("\nВсе результаты сохранены в директории 'demo_data'")


if __name__ == "__main__":
    main() 