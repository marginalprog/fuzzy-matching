"""
Пример использования транслитерации для миграции и сопоставления данных 
между русским и английским языками
"""

import json
import pandas as pd
from prettytable import PrettyTable

import fuzzy_matching.utils.transliteration_utils as translit
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig


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


def case1_migrate_english_to_russian():
    """
    Кейс 1: Английская компания N хранила данные о работниках на английском языке.
    Её выкупила Российская компания, и теперь эти данные нужно мигрировать с учетом
    российских правил транслитерации.
    """
    print("\n=========== КЕЙС 1: МИГРАЦИЯ ДАННЫХ С АНГЛИЙСКОГО НА РУССКИЙ ===========\n")
    
    # Загружаем данные английской компании
    english_data = [
        {
            'id': 'E001',
            'last_name': 'Ivanov',
            'first_name': 'Alexander',
            'middle_name': 'Sergeevich',
            'position': 'CEO',
            'email': 'aivanov@example.com'
        },
        {
            'id': 'E002',
            'last_name': 'Petrov',
            'first_name': 'Mikhail',
            'middle_name': 'Ivanovich',
            'position': 'CTO',
            'email': 'mpetrov@example.com'
        },
        {
            'id': 'E003',
            'last_name': 'Kuznetsova',
            'first_name': 'Elena',
            'middle_name': 'Alexandrovna',
            'position': 'CFO',
            'email': 'ekuznetsova@example.com'
        },
        {
            'id': 'E004',
            'last_name': 'Smirnov',
            'first_name': 'Dmitry',
            'middle_name': 'Petrovich',
            'position': 'CIO',
            'email': 'dsmirnov@example.com'
        },
        {
            'id': 'E005',
            'last_name': 'Sokolov',
            'first_name': 'Vladimir',
            'middle_name': 'Nikolaevich',
            'position': 'COO',
            'email': 'vsokolov@example.com'
        }
    ]
    
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
            'Фамилия': translit.transliterate_en_to_ru(employee['last_name'], translit.PASSPORT_STANDARD),
            'Имя': translit.transliterate_en_to_ru(employee['first_name'], translit.PASSPORT_STANDARD),
            'Отчество': translit.transliterate_en_to_ru(employee['middle_name'], translit.PASSPORT_STANDARD),
            'Должность': employee['position'],
            'Email': employee['email']
        }
        russian_data.append(ru_employee)
    
    print("\nДанные после транслитерации на русский язык:")
    print_table(russian_data)
    
    # Сохраняем результат в JSON
    with open('russian_employees.json', 'w', encoding='utf-8') as f:
        json.dump(russian_data, f, ensure_ascii=False, indent=4)
    
    print("\nДанные сохранены в russian_employees.json")
    print("\n==========================================================\n")


def case2_match_mixed_language_records():
    """
    Кейс 2: При сопоставлении двух записей нужно учитывать те или иные 
    правила транслитерации для правильного выбора варианта.
    """
    print("\n=========== КЕЙС 2: СОПОСТАВЛЕНИЕ ЗАПИСЕЙ С РАЗНЫМИ ПРАВИЛАМИ ТРАНСЛИТЕРАЦИИ ===========\n")
    
    # Создаем данные для сопоставления - разные варианты написания одних и тех же имен
    russian_records = [
        {
            'id': 'R001',
            'Фамилия': 'Иванов',
            'Имя': 'Александр',
            'Отчество': 'Сергеевич',
            'Email': 'ivanov@company.ru'
        },
        {
            'id': 'R002',
            'Фамилия': 'Петров',
            'Имя': 'Михаил',
            'Отчество': 'Иванович',
            'Email': 'petrov@company.ru'
        },
        {
            'id': 'R003',
            'Фамилия': 'Кузнецова',
            'Имя': 'Елена',
            'Отчество': 'Александровна',
            'Email': 'kuznecova@company.ru'
        }
    ]
    
    english_records = [
        {
            'id': 'E001',
            'Фамилия': 'Ivanov',
            'Имя': 'Alexander',  # Английский вариант имени
            'Отчество': 'Sergeevich',
            'Email': 'aivanov@company.com'
        },
        {
            'id': 'E002',
            'Фамилия': 'Petrov',
            'Имя': 'Michail',  # Научная транслитерация
            'Отчество': 'Ivanovich',
            'Email': 'mpetrov@company.com'
        },
        {
            'id': 'E003',
            'Фамилия': 'Kuznetsova',  # Разные правила транслитерации
            'Имя': 'Elena',
            'Отчество': 'Alexandrovna',
            'Email': 'ekuznetsova@company.com'
        },
        {
            'id': 'E004',
            'Фамилия': 'Sidorov',  # Запись без соответствия
            'Имя': 'Sergey',
            'Отчество': 'Dmitrievich',
            'Email': 'ssidorov@company.com'
        }
    ]
    
    # Показываем исходные данные
    print("Записи на русском языке:")
    print_table(russian_records)
    
    print("\nЗаписи с английской транслитерацией:")
    print_table(english_records)
    
    # Создаем конфигурацию для сопоставления с транслитерацией
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Паспортная транслитерация",
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
    
    table = PrettyTable()
    table.field_names = ["Русская запись", "Английская запись", "Схожесть"]
    
    for match in matches:
        ru = " ".join(match["Запись 1"])
        en = " ".join(match["Запись 2"])
        score = f"{match['Совпадение'][0]:.2f}"
        table.add_row([ru, en, score])
    
    table.align["Русская запись"] = "l"
    table.align["Английская запись"] = "l"
    table.align["Схожесть"] = "r"
    
    print(table)
    
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
    
    print("\n==========================================================\n")


def case3_identify_correct_name_variant():
    """
    Кейс 3: При сопоставлении двух вариантов имени нужно выбрать 
    более правильный вариант относительно правил транслитерации.
    """
    print("\n=========== КЕЙС 3: ВЫБОР ПРАВИЛЬНОГО ВАРИАНТА ИМЕНИ ===========\n")
    
    # Варианты имен для анализа
    examples = [
        ("Александр", ["Alexander", "Aleksandr", "Alexandr"]),
        ("Юлия", ["Julia", "Yulia", "Iuliia"]),
        ("Щербаков", ["Shcherbakov", "Scherbakov", "Scherbakoff"]),
        ("Евгений", ["Evgeny", "Yevgeny", "Eugene", "Eugenii"]),
        ("Ксения", ["Ksenia", "Xenia", "Kseniya"])
    ]
    
    # Создаем конфигурацию для анализа транслитерации
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Паспортная транслитерация",
        normalize_names=True
    )
    
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='name', weight=1.0, transliterate=True)
        ],
        transliteration=transliteration_config
    )
    
    matcher = DataMatcher(config=match_config)
    
    # Анализируем каждый пример
    table = PrettyTable()
    table.field_names = ["Русское имя", "Варианты на английском", "Наилучший вариант", "Схожесть"]
    
    for ru_name, en_variants in examples:
        best_variant = matcher.select_best_transliteration_variant(en_variants, target_lang='ru')
        
        # Вычисляем схожесть лучшего варианта с оригиналом
        ru_trans = translit.transliterate_en_to_ru(best_variant, translit.PASSPORT_STANDARD)
        from rapidfuzz import fuzz
        similarity = fuzz.token_sort_ratio(ru_name.lower(), ru_trans.lower()) / 100.0
        
        # Добавляем в таблицу
        table.add_row([ru_name, ", ".join(en_variants), best_variant, f"{similarity:.2f}"])
    
    print("Выбор наилучшего варианта транслитерации для русских имен:")
    print(table)
    
    # Обратное преобразование - с русского на английский
    rev_examples = [
        (["Aleksandr", "Alexander", "Alex"], "Александр"),
        (["Yulia", "Julia", "Yuliya"], "Юлия"),
        (["Sergei", "Sergey", "Serge"], "Сергей"),
        (["Maria", "Mariya", "Mary"], "Мария")
    ]
    
    table = PrettyTable()
    table.field_names = ["Английские варианты", "Русское имя", "Наилучший вариант", "Схожесть"]
    
    for en_variants, ru_name in rev_examples:
        best_variant = matcher.select_best_transliteration_variant(en_variants, target_lang='ru')
        
        # Вычисляем схожесть лучшего варианта с русским оригиналом
        ru_trans = translit.transliterate_en_to_ru(best_variant, translit.PASSPORT_STANDARD)
        from rapidfuzz import fuzz
        similarity = fuzz.token_sort_ratio(ru_name.lower(), ru_trans.lower()) / 100.0
        
        # Добавляем в таблицу
        table.add_row([", ".join(en_variants), ru_name, best_variant, f"{similarity:.2f}"])
    
    print("\nВыбор наилучшего английского варианта для русских имен:")
    print(table)
    
    print("\n==========================================================\n")


def main():
    """Основная функция для демонстрации кейсов использования транслитерации"""
    print("\n===== ДЕМОНСТРАЦИЯ КЕЙСОВ ИСПОЛЬЗОВАНИЯ ТРАНСЛИТЕРАЦИИ =====\n")
    
    # Кейс 1: Миграция данных с английского на русский
    case1_migrate_english_to_russian()
    
    # Кейс 2: Сопоставление записей с разными правилами транслитерации
    case2_match_mixed_language_records()
    
    # Кейс 3: Выбор правильного варианта имени
    case3_identify_correct_name_variant()

    print("\n===== ЗАВЕРШЕНИЕ ДЕМОНСТРАЦИИ =====\n")


if __name__ == "__main__":
    main() 