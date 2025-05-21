"""
Пример использования транслитерации для миграции и сопоставления данных 
между русским и английским языками
"""

import json
import os
import pandas as pd
from rapidfuzz import fuzz

import fuzzy_matching.utils.transliteration.transliteration_utils as translit
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.examples.utils import print_table, print_matches, save_example_results
from fuzzy_matching.examples.data_examples import PERSONAL_DATA_RU, PERSONAL_DATA_EN


def case1_migrate_english_to_russian():
    """
    Кейс 1: Английская компания N хранила данные о работниках на английском языке.
    Её выкупила Российская компания, и теперь эти данные нужно перевести на русский язык
    с использованием правил транслитерации для корректного отображения имен на русском.
    """
    print("\n=========== КЕЙС 1: МИГРАЦИЯ ДАННЫХ С АНГЛИЙСКОГО НА РУССКИЙ ===========\n")
    
    # Загружаем данные английской компании
    english_data = PERSONAL_DATA_EN
    
    print("Исходные данные английской компании:")
    print_table(english_data)
    
    # Маппинг полей для российской компании
    field_mapping = {
        'last_name': 'Фамилия',
        'first_name': 'Имя',
        'middle_name': 'Отчество',
        'position': 'Должность',
        'email': 'email'
    }
    
    # Транслитерируем данные на русский
    russian_data = []
    for employee in english_data:
        ru_employee = {
            'ID': employee['id'],
            'Фамилия': translit.transliterate_en_to_ru(employee['Фамилия'], translit.PASSPORT_STANDARD),
            'Имя': translit.transliterate_en_to_ru(employee['Имя'], translit.PASSPORT_STANDARD),
            'Отчество': translit.transliterate_en_to_ru(employee['Отчество'], translit.PASSPORT_STANDARD),
            'email': employee['email']
        }
        russian_data.append(ru_employee)
    
    print("\nДанные после транслитерации на русский язык:")
    print_table(russian_data)
    
    # Сохраняем результат в JSON
    with open('results/russian_employees.json', 'w', encoding='utf-8') as f:
        json.dump(russian_data, f, ensure_ascii=False, indent=4)
    
    print("\nДанные сохранены в results/russian_employees.json")
    print("\n==========================================================\n")


def case2_match_mixed_language_records():
    """
    Кейс 2: При сопоставлении двух записей нужно учитывать те или иные 
    правила транслитерации для правильного выбора варианта.
    """
    print("\n=========== КЕЙС 2: СОПОСТАВЛЕНИЕ ЗАПИСЕЙ С РАЗНЫМИ ПРАВИЛАМИ ТРАНСЛИТЕРАЦИИ ===========\n")
    
    # Используем предопределенные данные
    russian_records = PERSONAL_DATA_RU[:3]
    english_records = PERSONAL_DATA_EN[:4]  # Добавляем одну запись без соответствия
    
    # Показываем исходные данные
    print("Записи на русском языке:")
    print_table(russian_records)
    
    print("\nЗаписи с английской транслитерацией:")
    print_table(english_records)
    
    # Создаем конфигурацию для сопоставления с транслитерацией
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Passport",
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.5, transliterate=True),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True)
        ],
        length_weight=0.01,
        threshold=0.8,
        transliteration=transliteration_config
    )
    
    # Выполняем сопоставление с транслитерацией
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(russian_records, english_records)
    
    # Показываем результаты сопоставления
    print("\nРезультаты сопоставления с учетом транслитерации:")
    print_matches(matches)
    
    # Создаем DataFrame для удобного просмотра консолидированных данных
    df_consolidated = pd.DataFrame(consolidated)
    
    print("\nКонсолидированные записи:")
    if not df_consolidated.empty:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.expand_frame_repr', False)
        pd.set_option('display.max_rows', 10)
        print(df_consolidated)
    else:
        print("Консолидированные записи отсутствуют")
    
    # Сохраняем результаты
    save_example_results(matches, consolidated, prefix="translit_mixed", results_dir="results")
    
    print("\n==========================================================\n")


def case3_demonstrate_gost_standard():
    """
    Кейс 3: Демонстрация работы стандарта GOST
    """
    print("\n=========== КЕЙС 3: ДЕМОНСТРАЦИЯ СТАНДАРТА GOST ===========\n")
    
    # Примеры русских имен для транслитерации
    test_names = [
        "Щербаков",
        "Чайковский",
        "Жуков",
        "Шишкин",
        "Эйнштейн"
    ]
    
    print("Примеры транслитерации по стандарту GOST:")
    print_table([{
        "Русское имя": name,
        "Транслитерация": translit.transliterate_ru_to_en(name, translit.GOST_STANDARD)
    } for name in test_names])
    
    # Пример обратной транслитерации
    gost_names = [
        "Ščerbakov",
        "Čajkovskij",
        "Žukov",
        "Šiškin",
        "Èjnštejn"
    ]
    
    print("\nПримеры обратной транслитерации:")
    print_table([{
        "Имя в GOST": name,
        "Обратная транслитерация": translit.transliterate_en_to_ru(name, translit.GOST_STANDARD)
    } for name in gost_names])
    
    print("\nВывод: Стандарт GOST обеспечивает однозначное")
    print("соответствие между русскими и латинскими буквами, что делает")
    print("транслитерацию обратимой и точной.")
    
    print("\n==========================================================\n")


def case4_direct_transliteration_challenges():
    """
    Кейс 4: Демонстрация сложностей прямой транслитерации без промежуточного русского этапа.
    """
    print("\n=========== КЕЙС 4: СЛОЖНОСТИ ПРЯМОЙ ТРАНСЛИТЕРАЦИИ ===========\n")
    
    # Примеры неоднозначных случаев
    ambiguous_cases = [
        {
            "Английский": "Michail",
            "Правильный русский": translit.transliterate_en_to_ru("Michail", translit.PASSPORT_STANDARD),
            "Неправильный русский": "Мичаил",  # Пример неправильной транслитерации
            "Объяснение": "ch -> х, а не ч"
        },
        {
            "Английский": "Shcherbakov",
            "Правильный русский": translit.transliterate_en_to_ru("Shcherbakov", translit.PASSPORT_STANDARD),
            "Неправильный русский": "Шчербаков",  # Пример неправильной транслитерации
            "Объяснение": "shch -> щ, а не ш+ч"
        },
        {
            "Английский": "Yelena",
            "Правильный русский": translit.transliterate_en_to_ru("Yelena", translit.PASSPORT_STANDARD),
            "Неправильный русский": "Йелена",  # Пример неправильной транслитерации
            "Объяснение": "y -> е в начале слова"
        },
        {
            "Английский": "Dmitry",
            "Правильный русский": translit.transliterate_en_to_ru("Dmitry", translit.PASSPORT_STANDARD),
            "Неправильный русский": "Дмитриы",  # Пример неправильной транслитерации
            "Объяснение": "y -> й в конце слова"
        }
    ]
    
    print("Примеры неоднозначных случаев при прямой транслитерации:")
    print_table(ambiguous_cases)
    
    print("\nВывод: Прямая транслитерация без промежуточного русского этапа")
    print("может привести к ошибкам из-за неоднозначности соответствий")
    print("и контекстной зависимости правил транслитерации.")
    
    print("\n==========================================================\n")


def main():
    """
    Основная функция примера.
    """
    # Создаем директорию для результатов
    os.makedirs("results", exist_ok=True)
    
    print("===== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ТРАНСЛИТЕРАЦИИ =====\n")
    
    # Кейс 1: Миграция данных с английского на русский
    case1_migrate_english_to_russian()
    
    # Кейс 2: Сопоставление записей с разными правилами транслитерации
    case2_match_mixed_language_records()
    
    # Кейс 3: Демонстрация стандарта GOST
    case3_demonstrate_gost_standard()
    
    # Кейс 4: Сложности прямой транслитерации
    case4_direct_transliteration_challenges()
    
    print("===== ЗАВЕРШЕНИЕ ПРИМЕРОВ ТРАНСЛИТЕРАЦИИ =====")


if __name__ == "__main__":
    main() 