"""
Утилитарные функции для работы с данными через CLI.
"""

import pandas as pd
from prettytable import PrettyTable
from fuzzy_matching.utils.data_generator import DataGenerator, Language


def generate_test_data(probabilities, gen_fields, count=100, language='ru', field_names_format=None):
    """
    Генерирует тестовые данные: оригинальный и искаженный списки.
    
    :param probabilities: словарь вероятностей различных искажений
        - double_char_probability: вероятность дублирования буквы (0.0-1.0)
        - change_char_probability: вероятность замены буквы (0.0-1.0)
        - change_name_probability: вероятность полной замены ФИО (0.0-1.0)
        - change_domain_probability: вероятность изменения домена в email (0.0-1.0)
        - double_number_probability: вероятность дублирования цифры в телефоне (0.0-1.0)
        - suffix_probability: вероятность добавления суффикса к ФИО (0.0-1.0)
    :param gen_fields: список полей для генерации в формате ['last_name', 'first_name', ...]
    :param count: количество записей для генерации (по умолчанию 100)
    :param language: язык генерируемых данных ('ru' или 'en')
        - ru: русский язык (имена, фамилии и отчества на русском)
        - en: английский язык (имена, фамилии и middle names на английском)
    :param field_names_format: формат названий полей ('ru' или 'en', если None - соответствует языку)
        - ru: русские названия полей (Фамилия, Имя, Отчество и т.д.)
        - en: английские названия полей (LastName, FirstName, MiddleName и т.д.)
    :return: кортеж (список оригинальных записей, список искаженных записей)
    """
    # Выбираем язык для генератора
    lang = Language.RUS if language.lower() == 'ru' else Language.ENG
    
    # Если формат названий полей не указан, используем язык
    field_names_format = field_names_format or language
    
    # Создаем генератор с указанными параметрами
    dg = DataGenerator(language=lang, probabilities=probabilities)
    
    # Устанавливаем формат названий полей
    if field_names_format.lower() == 'ru':
        dg.FIELD_NAMES = dg.FIELD_NAMES_RU
    else:
        dg.FIELD_NAMES = dg.FIELD_NAMES_EN
    
    # Преобразуем поля из формата ['last_name', 'first_name', ...] 
    # в формат ['Фамилия', 'Имя', ...]
    field_names = []
    for field in gen_fields:
        if field == 'id':
            field_names.append('id')
        else:
            field_name = dg.FIELD_NAMES.get(field, field)
            if field_name:
                field_names.append(field_name)
    
    original_list, variant_list = dg.generate_records_pair(count, fields=field_names)
    return original_list, variant_list


def generate_and_save_test_data(probabilities, gen_fields, count=100, file_format='json', original_file=None, variant_file=None, language='ru', field_names_format=None, verbose=False):
    """
    Генерирует тестовые данные и сохраняет их в файлы.
    
    :param probabilities: словарь вероятностей различных искажений
        - double_char_probability: вероятность дублирования буквы (0.0-1.0)
        - change_char_probability: вероятность замены буквы (0.0-1.0)
        - change_name_probability: вероятность полной замены ФИО (0.0-1.0)
        - change_domain_probability: вероятность изменения домена в email (0.0-1.0)
        - double_number_probability: вероятность дублирования цифры в телефоне (0.0-1.0)
        - suffix_probability: вероятность добавления суффикса к ФИО (0.0-1.0)
    :param gen_fields: список полей для генерации в формате ['last_name', 'first_name', ...]
    :param count: количество записей для генерации (по умолчанию 100)
    :param file_format: формат файлов для сохранения ('json' или 'csv')
    :param original_file: путь для сохранения оригинальных данных
    :param variant_file: путь для сохранения искаженных данных
    :param language: язык генерируемых данных ('ru' или 'en')
        - ru: русский язык (имена, фамилии и отчества на русском)
        - en: английский язык (имена, фамилии и middle names на английском)
    :param field_names_format: формат названий полей ('ru' или 'en', если None - соответствует языку)
        - ru: русские названия полей (Фамилия, Имя, Отчество и т.д.)
        - en: английские названия полей (LastName, FirstName, MiddleName и т.д.)
    :param verbose: если True, выводить подробную информацию
    :return: кортеж (список оригинальных записей, список искаженных записей)
    """
    # Выбираем язык для генератора
    lang = Language.RUS if language.lower() == 'ru' else Language.ENG
    
    # Если формат названий полей не указан, используем язык
    field_names_format = field_names_format or language
    
    # Создаем генератор с указанными параметрами
    dg = DataGenerator(language=lang, probabilities=probabilities)
    
    # Устанавливаем формат названий полей
    if field_names_format.lower() == 'ru':
        dg.FIELD_NAMES = dg.FIELD_NAMES_RU
    else:
        dg.FIELD_NAMES = dg.FIELD_NAMES_EN
    
    # Преобразуем поля из формата ['last_name', 'first_name', ...] 
    # в формат ['Фамилия', 'Имя', ...]
    field_names = []
    for field in gen_fields:
        if field == 'id':
            field_names.append('id')
        else:
            field_name = dg.FIELD_NAMES.get(field, field)
            if field_name:
                field_names.append(field_name)
    
    if verbose:
        print(f"Запрошенные поля: {gen_fields}")
        print(f"Поля для генерации: {field_names}")
    
    original_list, variant_list = dg.generate_records_pair(count, fields=field_names)

    # Сохраняем результаты
    if file_format == 'json':
        if original_file:
            dg.save_to_json(original_list, original_file)
        if variant_file:
            dg.save_to_json(variant_list, variant_file)
    elif file_format == 'csv':
        if original_file:
            dg.save_to_csv(original_list, original_file)
        if variant_file:
            dg.save_to_csv(variant_list, variant_file)
    else:
        raise ValueError("Неверный формат файла. Выберите '.json' или '.csv'.")

    return original_list, variant_list


def run_matching(original_list, variant_list, config):
    """
    Запускает процесс сопоставления и консолидации данных.
    
    :param original_list: список оригинальных записей
    :param variant_list: список искаженных записей
    :param config: конфигурация для сопоставления (экземпляр MatchConfig)
    :return: кортеж (экземпляр DataMatcher, список совпадений, список консолидированных записей)
    """
    # Импортируем здесь, чтобы избежать циклических импортов
    from fuzzy_matching.core.data_matcher import DataMatcher
    
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
    table.field_names = ["Запись 1", "Запись 2", "Совпадение"]

    # Добавляем строки в таблицу
    for match in matches[:limit]:
        rec1 = " ".join(match["Запись 1"])
        rec2 = " ".join(match["Запись 2"])
        score = f"{match['Совпадение'][0]:.2f}"
        table.add_row([rec1, rec2, score])

    # Опции выравнивания
    table.align["Запись 1"] = "l"
    table.align["Запись 2"] = "l"
    table.align["Совпадение"] = "r"

    # Вывод
    print(f"\nОтобрано: {len(matches)} записей\n")
    print(table)


def display_consolidated(consolidated, sort_field="Фамилия", limit=5):
    """
    Выводит консолидированные записи в виде DataFrame pandas.
    
    :param consolidated: список консолидированных записей
    :param sort_field: поле для сортировки результатов
    :param limit: максимальное количество строк для отображения (по умолчанию 5)
    """
    df_consolidated = pd.DataFrame(consolidated)
    if sort_field in df_consolidated.columns:
        df_consolidated = df_consolidated.sort_values(by=sort_field, ascending=True)
    else:
        print(f'Столбец {sort_field} отсутствует в данных.')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('display.max_rows', limit)
    print(f"\nКонсолидировано: {len(consolidated)} записей\n")
    print(df_consolidated)


def print_table(data):
    """
    Выводит данные в виде форматированной таблицы.
    
    :param data: список словарей (записей) для отображения
    """
    if not data:
        print("Нет данных для отображения")
        return

    table = PrettyTable()
    table.field_names = data[0].keys()
    for row in data:
        table.add_row(row.values())

    table.align = 'l'
    print(table)


def save_results(matcher, matches, consolidated, output_matches=None, output_consolidated=None, file_format='json'):
    """
    Сохраняет результаты сопоставления и консолидации в файлы.
    
    :param matcher: экземпляр DataMatcher
    :param matches: список найденных совпадений
    :param consolidated: список консолидированных записей
    :param output_matches: путь для сохранения совпадений (если None, используется 'matches.{extension}')
    :param output_consolidated: путь для сохранения консолидированных данных (если None, используется 'consolidated.{extension}')
    :param file_format: формат файлов для сохранения ('json' или 'csv')
    """
    if file_format == 'json':
        if output_matches:
            matcher.save_matches_to_json(matches, output_matches)
        else:
            matcher.save_matches_to_json(matches, 'matches.json')
            
        if output_consolidated:
            matcher.save_consolidated_to_json(consolidated, output_consolidated)
        else:
            matcher.save_consolidated_to_json(consolidated, 'consolidated.json')
    elif file_format == 'csv':
        if output_matches:
            matcher.save_matches_to_csv(matches, output_matches)
        else:
            matcher.save_matches_to_csv(matches, 'matches.csv')
            
        if output_consolidated:
            matcher.save_consolidated_to_csv(consolidated, output_consolidated)
        else:
            matcher.save_consolidated_to_csv(consolidated, 'consolidated.csv')
    else:
        raise ValueError("Неверный формат вывода файла. Выберите '.json' или '.csv'.") 