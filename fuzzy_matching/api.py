"""
Программный интерфейс (API) библиотеки fuzzy_matching.

Этот модуль предоставляет удобные функции для использования возможностей библиотеки
в прикладном коде без необходимости работы через CLI.

Пример использования:

    # Импортируем необходимые модули
    from fuzzy_matching.api import (
        create_matcher, match_datasets, transliterate_dataset, 
        generate_test_datasets, save_results
    )
    from fuzzy_matching.core.match_config_classes import (
        MatchConfig, MatchFieldConfig, TransliterationConfig
    )
    
    # Создаем конфигурацию для сопоставления
    config = create_config(
        fields=[
            {"field": "Фамилия", "weight": 0.4, "transliterate": True},
            {"field": "Имя", "weight": 0.3, "transliterate": True},
            {"field": "Отчество", "weight": 0.2, "transliterate": True}
        ],
        threshold=0.7,
        transliteration_enabled=True
    )
    
    # Загружаем данные и выполняем сопоставление
    matches, consolidated = match_datasets(
        dataset1="data_ru.json", 
        dataset2="data_en.json",
        config=config
    )
    
    # Сохраняем результаты
    save_results(matches, consolidated, 
                 matches_file="matches.json", 
                 consolidated_file="consolidated.json")
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Union

# Импортируем только те утилиты, которые не создают циклических импортов
from fuzzy_matching.utils.data_generator import DataGenerator
from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig, 
    FuzzyAlgorithm
)


def create_config(
    fields: List[Dict[str, Any]], 
    threshold: float = 0.7, 
    block_field: Optional[str] = None,
    transliteration_enabled: bool = False,
    transliteration_standard: str = "Passport",
    fuzzy_algorithm: Optional[str] = "TOKEN_SORT"
) -> MatchConfig:
    """
    Создает конфигурацию для сопоставления данных.
    
    :param fields: список словарей с конфигурацией полей. Каждый словарь должен содержать ключи:
                 - "field": имя поля (обязательно)
                 - "weight": вес поля при расчете схожести от 0 до 1 (опционально, по умолчанию 1.0)
                 - "transliterate": включить транслитерацию для этого поля (опционально, по умолчанию False)
                 - "algorithm": алгоритм сопоставления для этого поля (опционально)
    :param threshold: порог схожести для сопоставления (от 0 до 1)
    :param block_field: поле для блокировки (ускоряет сопоставление)
    :param transliteration_enabled: включить/выключить транслитерацию
    :param transliteration_standard: стандарт транслитерации ("ГОСТ 7.79-2000", "Научная" или "Паспортная")
    :param fuzzy_algorithm: основной алгоритм нечеткого сопоставления для полей без указанного алгоритма
    :return: объект MatchConfig
    """
    # Преобразуем словари полей в объекты MatchFieldConfig
    match_fields = []
    for field_dict in fields:
        field_name = field_dict["field"]
        weight = field_dict.get("weight", 1.0)
        transliterate = field_dict.get("transliterate", False)
        
        # Новый параметр - явное указание алгоритма
        algorithm = None
        if "algorithm" in field_dict:
            algorithm_name = field_dict["algorithm"]
            try:
                algorithm = getattr(FuzzyAlgorithm, algorithm_name)
            except (AttributeError, TypeError):
                print(f"Предупреждение: неизвестный алгоритм '{algorithm_name}' для поля '{field_name}'. "
                      f"Будет использован основной алгоритм.")
        
        match_fields.append(MatchFieldConfig(
            field=field_name,
            weight=weight,
            transliterate=transliterate,
            fuzzy_algorithm=algorithm
        ))
    
    # Создаем конфигурацию транслитерации
    transliteration_config = TransliterationConfig(
        enabled=transliteration_enabled,
        standard=transliteration_standard,
        threshold=threshold,
        auto_detect=True,
        normalize_names=True
    )
    
    # Определяем основной алгоритм
    main_algorithm = None
    if fuzzy_algorithm:
        try:
            main_algorithm = getattr(FuzzyAlgorithm, fuzzy_algorithm)
        except (AttributeError, TypeError):
            print(f"Предупреждение: неизвестный основной алгоритм '{fuzzy_algorithm}'. "
                  f"Будет использован алгоритм TOKEN_SORT.")
            main_algorithm = FuzzyAlgorithm.TOKEN_SORT
    
    # Создаем и возвращаем конфигурацию
    return MatchConfig(
        fields=match_fields,
        threshold=threshold,
        block_field=block_field,
        transliteration=transliteration_config,
        fuzzy_algorithm=main_algorithm
    )


def create_matcher(config: Optional[MatchConfig] = None, **kwargs):
    """
    Создает экземпляр DataMatcher с указанной конфигурацией.
    
    :param config: объект MatchConfig (если None, создается с параметрами по умолчанию)
    :param kwargs: параметры для create_config, если config не указан
    :return: экземпляр DataMatcher
    """
    # Импортируем DataMatcher здесь, чтобы избежать циклических импортов
    from fuzzy_matching.core.data_matcher import DataMatcher
    
    if config is None:
        config = create_config(**kwargs)
    
    return DataMatcher(config=config)


def load_dataset(
    file_path: str, 
    file_format: Optional[str] = None, 
    field_mapping: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Загружает набор данных из файла.
    
    :param file_path: путь к файлу
    :param file_format: формат файла ('csv' или 'json'), если None - определяется по расширению
    :param field_mapping: словарь соответствия полей в формате {внешнее_имя: внутреннее_имя}
    :return: список словарей (записей)
    """
    # Импортируем DataMatcher здесь, чтобы избежать циклических импортов
    from fuzzy_matching.core.data_matcher import DataMatcher
    
    # Определяем формат файла по расширению, если не указан явно
    if file_format is None:
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.csv':
            file_format = 'csv'
        elif ext.lower() == '.json':
            file_format = 'json'
        else:
            raise ValueError(f"Неизвестный формат файла: {ext}. Укажите file_format явно.")
    
    matcher = DataMatcher()
    
    if file_format == 'csv':
        return matcher.load_from_csv(file_path, field_mapping)
    elif file_format == 'json':
        return matcher.load_from_json(file_path, field_mapping)
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {file_format}. Используйте 'csv' или 'json'.")


def match_datasets(
    dataset1: Union[str, List[Dict[str, Any]]], 
    dataset2: Union[str, List[Dict[str, Any]]], 
    config: Optional[MatchConfig] = None,
    field_mapping: Optional[Dict[str, str]] = None,
    **kwargs
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Сопоставляет два набора данных и возвращает результаты.
    
    :param dataset1: путь к файлу или список словарей (первый набор данных)
    :param dataset2: путь к файлу или список словарей (второй набор данных)
    :param config: объект MatchConfig (если None, создается с параметрами из kwargs)
    :param field_mapping: словарь соответствия полей для загрузки данных из файлов
    :param kwargs: параметры для create_config, если config не указан
    :return: кортеж (список совпадений, список консолидированных записей)
    """
    # Создаем matcher с указанной конфигурацией
    matcher = create_matcher(config, **kwargs)
    
    # Загружаем данные, если переданы пути к файлам
    data1 = dataset1
    data2 = dataset2
    
    if isinstance(dataset1, str):
        data1 = load_dataset(dataset1, field_mapping=field_mapping)
    
    if isinstance(dataset2, str):
        data2 = load_dataset(dataset2, field_mapping=field_mapping)
    
    # Выполняем сопоставление
    matches, consolidated = matcher.match_and_consolidate(data1, data2)
    
    return matches, consolidated


def transliterate_dataset(
    dataset: Union[str, List[Dict[str, Any]]], 
    target_lang: str = 'en',
    transliteration_standard: str = "Passport",
    fields: Optional[List[str]] = None,
    field_mapping: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Транслитерирует данные из одного языка в другой.
    
    :param dataset: путь к файлу или список словарей с данными
    :param target_lang: целевой язык транслитерации ('ru' или 'en')
    :param transliteration_standard: стандарт транслитерации ("GOST", "Scientific" или "Passport")
    :param fields: список полей для транслитерации (если None, используются все текстовые поля)
    :param field_mapping: словарь соответствия полей для загрузки данных из файла
    :return: список транслитерированных записей
    """
    # Импортируем DataMatcher здесь, чтобы избежать циклических импортов
    from fuzzy_matching.core.data_matcher import DataMatcher
    
    # Настраиваем конфигурацию транслитерации
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard=transliteration_standard,
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    # Создаем экземпляр DataMatcher
    config = MatchConfig(
        fields=[],
        threshold=0.7,
        transliteration=transliteration_config
    )
    matcher = DataMatcher(config=config)
    
    # Загружаем данные, если передан путь к файлу
    data = dataset
    if isinstance(dataset, str):
        data = load_dataset(dataset, field_mapping=field_mapping)
    
    # Транслитерируем данные
    return matcher.transliterate_data(data, target_lang=target_lang, fields=fields)


def generate_test_datasets(
    count: int = 100, 
    double_char_probability: float = 0.1,
    change_char_probability: float = 0.05,
    change_name_probability: float = 0.1,
    change_domain_probability: float = 0.3,
    double_number_probability: float = 0.3,
    suffix_probability: float = 0.1,
    save_to_file: bool = False,
    output_original: Optional[str] = None,
    output_variant: Optional[str] = None,
    output_format: str = 'json'
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Генерирует тестовые наборы данных для отладки и тестирования.
    
    :param count: количество записей для генерации
    :param double_char_probability: вероятность дублирования буквы (от 0 до 1)
    :param change_char_probability: вероятность замены буквы (от 0 до 1)
    :param change_name_probability: вероятность полной замены ФИО (от 0 до 1)
    :param change_domain_probability: вероятность изменения домена в email (от 0 до 1)
    :param double_number_probability: вероятность дублирования цифры в телефоне (от 0 до 1)
    :param suffix_probability: вероятность добавления суффикса к ФИО (от 0 до 1)
    :param save_to_file: сохранять ли результаты в файлы
    :param output_original: путь для сохранения оригинальных данных
    :param output_variant: путь для сохранения искаженных данных
    :param output_format: формат выходных файлов ('json' или 'csv')
    :return: кортеж (список оригинальных записей, список искаженных записей)
    """
    # Определяем вероятности искажений
    probabilities = {
        'double_char_probability': double_char_probability,
        'change_char_probability': change_char_probability,
        'change_name_probability': change_name_probability,
        'change_domain_probability': change_domain_probability,
        'double_number_probability': double_number_probability,
        'suffix_probability': suffix_probability
    }
    
    # Определяем поля для генерации
    default_fields = [
        'id',
        'Фамилия',
        'Имя',
        'Отчество',
        'email',
        'Телефон',
        'Пол'
    ]
    
    if save_to_file:
        # Импортируем эти функции здесь, чтобы избежать циклических импортов
        from fuzzy_matching.utils.cli_utils import generate_and_save_test_data
        
        # Генерируем и сохраняем данные
        return generate_and_save_test_data(
            probabilities=probabilities,
            gen_fields=gen_fields,
            count=count,
            file_format=output_format,
            original_file=output_original,
            variant_file=output_variant
        )
    else:
        # Импортируем эту функцию здесь, чтобы избежать циклических импортов
        from fuzzy_matching.utils.cli_utils import generate_test_data
        
        # Просто генерируем данные без сохранения
        return generate_test_data(probabilities, gen_fields, count)


def save_results(
    matches: List[Dict[str, Any]], 
    consolidated: List[Dict[str, Any]], 
    matches_file: Optional[str] = None, 
    consolidated_file: Optional[str] = None,
    output_format: str = 'json'
) -> None:
    """
    Сохраняет результаты сопоставления и консолидации в файлы.
    
    :param matches: список найденных совпадений
    :param consolidated: список консолидированных записей
    :param matches_file: путь для сохранения совпадений
    :param consolidated_file: путь для сохранения консолидированных данных
    :param output_format: формат выходных файлов ('json' или 'csv')
    """
    # Импортируем DataMatcher здесь, чтобы избежать циклических импортов
    from fuzzy_matching.core.data_matcher import DataMatcher
    
    # Создаем простую конфигурацию
    config = MatchConfig(
        fields=[],
        threshold=0.7
    )
    matcher = DataMatcher(config=config)
    
    # Сохраняем результаты
    if output_format == 'json':
        if matches_file:
            matcher.save_matches_to_json(matches, matches_file)
        if consolidated_file:
            matcher.save_consolidated_to_json(consolidated, consolidated_file)
    elif output_format == 'csv':
        if matches_file:
            matcher.save_matches_to_csv(matches, matches_file)
        if consolidated_file:
            matcher.save_consolidated_to_csv(consolidated, consolidated_file) 