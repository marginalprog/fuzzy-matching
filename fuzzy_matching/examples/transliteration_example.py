"""
Пример использования транслитерации для миграции и сопоставления данных 
между русским и английским языками
"""

import json
import pandas as pd

import fuzzy_matching.utils.transliteration.transliteration_utils as translit
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.examples.utils import print_table, print_matches, save_example_results
from fuzzy_matching.examples.data_examples import PERSONAL_DATA_RU, PERSONAL_DATA_EN


def case1_migrate_english_to_russian():
    """
    Кейс 1: Английская компания N хранила данные о работниках на английском языке.
    Её выкупила Российская компания, и теперь эти данные нужно мигрировать с учетом
    российских правил транслитерации.
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
        'email': 'Email'
    }
    
    # Транслитерируем данные на русский
    russian_data = []
    for employee in english_data:
        ru_employee = {
            'ID': employee['id'],
            'Фамилия': translit.transliterate_en_to_ru(employee['Фамилия'], translit.PASSPORT_STANDARD),
            'Имя': translit.transliterate_en_to_ru(employee['Имя'], translit.PASSPORT_STANDARD),
            'Отчество': translit.transliterate_en_to_ru(employee['Отчество'], translit.PASSPORT_STANDARD),
            'Email': employee['email']
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
        standard="Паспортная",
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


def case3_identify_correct_name_variant():
    """
    Кейс 3: При сопоставлении двух вариантов имени нужно выбрать 
    более правильный вариант относительно правил транслитерации.
    """
    print("\n=========== КЕЙС 3: ВЫБОР ПРАВИЛЬНОГО ВАРИАНТА ИМЕНИ ===========\n")
    
    # Создаем примеры разных вариантов написания одного и того же имени
    name_variants = [
        {"id": "1", "Имя": "Александр", "Язык": "Русский", "Примечание": "Оригинальное имя"},
        {"id": "2", "Имя": "Alexander", "Язык": "Английский", "Примечание": "Стандартный английский эквивалент"},
        {"id": "3", "Имя": "Aleksandr", "Язык": "Транслитерация", "Примечание": "Паспортная транслитерация"},
        {"id": "4", "Имя": "Alexandr", "Язык": "Транслитерация", "Примечание": "Научная транслитерация"},
        {"id": "5", "Имя": "Aleksander", "Язык": "Транслитерация", "Примечание": "Альтернативный вариант"},
        {"id": "6", "Имя": "Sasha", "Язык": "Английский", "Примечание": "Уменьшительное имя"}
    ]
    
    print("Варианты написания имени:")
    print_table(name_variants)
    
    print("\nСравнение вариантов с оригиналом (Александр):")
    
    original = "Александр"
    results = []
    
    for variant in name_variants[1:]:  # Пропускаем оригинал
        # Прямое сравнение
        direct_ratio = fuzz.ratio(original, variant["Имя"]) / 100.0
        
        # Сравнение с транслитерацией варианта на русский
        if variant["Язык"] in ["Английский", "Транслитерация"]:
            ru_variant = translit.transliterate_en_to_ru(variant["Имя"], translit.PASSPORT_STANDARD)
            translit_ratio = fuzz.ratio(original, ru_variant) / 100.0
        else:
            ru_variant = variant["Имя"]
            translit_ratio = direct_ratio
        
        # Сравнение с транслитерацией оригинала на английский
        en_original = translit.transliterate_ru_to_en(original, translit.PASSPORT_STANDARD)
        reverse_translit_ratio = fuzz.ratio(en_original, variant["Имя"]) / 100.0
        
        results.append({
            "Вариант": variant["Имя"],
            "Язык": variant["Язык"],
            "Прямое сравнение": f"{direct_ratio:.2f}",
            "Транслит. на русский": f"{translit_ratio:.2f}",
            "Сравнение с англ. оригиналом": f"{reverse_translit_ratio:.2f}",
            "Транслит. вариант": ru_variant if variant["Язык"] != "Русский" else en_original
        })
    
    print_table(results)
    
    print("\nВывод: При сопоставлении имен с разными языками, транслитерация")
    print("значительно повышает точность сопоставления. Наиболее точные результаты")
    print("достигаются при транслитерации вариантов к языку оригинала.")
    
    print("\n==========================================================\n")


def main():
    """
    Основная функция примера.
    """
    import os
    from rapidfuzz import fuzz
    
    # Создаем директорию для результатов
    os.makedirs("results", exist_ok=True)
    
    print("===== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ТРАНСЛИТЕРАЦИИ =====\n")
    
    # Кейс 1: Миграция данных с английского на русский
    case1_migrate_english_to_russian()
    
    # Кейс 2: Сопоставление записей с разными правилами транслитерации
    case2_match_mixed_language_records()
    
    # Кейс 3: Выбор правильного варианта имени
    case3_identify_correct_name_variant()
    
    print("===== ЗАВЕРШЕНИЕ ПРИМЕРОВ ТРАНСЛИТЕРАЦИИ =====")


if __name__ == "__main__":
    main() 