from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
from enum import Enum, auto


class FuzzyAlgorithm(Enum):
    """
    Алгоритмы нечёткого сопоставления строк.
    """
    RATIO = "ratio"                 # Соотношение схожести (базовый алгоритм Levenshtein)
    PARTIAL_RATIO = "partial_ratio" # Частичное соотношение (находит наилучшее совпадение подстроки)
    TOKEN_SORT = "token_sort_ratio" # Сортировка токенов (учитывает порядок слов)
    TOKEN_SET = "token_set_ratio"   # Множественное отношение токенов (лучше для перемешанных слов)
    WRatio = "wratio"               # Взвешенное соотношение (комбинированный результат)


class DomainSpecificAlgorithm(Enum):
    """
    Предопределенные комбинации алгоритмов для конкретных предметных областей.
    Каждый элемент содержит словарь с алгоритмами для разных типов полей.
    """
    PERSON_DATA = {  # Для персональных данных (ФИО, клиентские базы)
        'name': FuzzyAlgorithm.PARTIAL_RATIO,      # Для имен (учитывает уменьшительные формы)
        'surname': FuzzyAlgorithm.TOKEN_SORT,      # Для фамилий (учитывает двойные фамилии)
        'patronymic': FuzzyAlgorithm.RATIO,        # Для отчеств (обычно точное сопоставление)
        'address': FuzzyAlgorithm.TOKEN_SET,       # Для адресов (порядок слов часто меняется)
        'email': FuzzyAlgorithm.RATIO,             # Для email (нужна точность)
        'phone': FuzzyAlgorithm.RATIO,             # Для телефонов (нужна точность)
        'default': FuzzyAlgorithm.WRatio           # Для всех остальных полей
    }
    
    PRODUCT_DATA = {  # Для товаров и продуктов
        'name': FuzzyAlgorithm.TOKEN_SET,         # Для названий товаров (порядок слов может меняться)
        'description': FuzzyAlgorithm.TOKEN_SET,  # Для описаний (важно содержание, а не порядок)
        'sku': FuzzyAlgorithm.RATIO,              # Для артикулов (нужна точность)
        'brand': FuzzyAlgorithm.PARTIAL_RATIO,    # Для брендов (могут быть написаны по-разному)
        'category': FuzzyAlgorithm.TOKEN_SORT,    # Для категорий (могут меняться слова)
        'default': FuzzyAlgorithm.TOKEN_SET       # Для всех остальных полей
    }
    
    COMPANY_DATA = {  # Для организаций и компаний
        'name': FuzzyAlgorithm.TOKEN_SET,         # Для названий компаний (ООО может быть в начале или в конце)
        'legal_name': FuzzyAlgorithm.TOKEN_SET,   # Для юридических наименований
        'inn': FuzzyAlgorithm.RATIO,              # Для ИНН (нужна точность)
        'address': FuzzyAlgorithm.TOKEN_SET,      # Для адресов
        'phone': FuzzyAlgorithm.RATIO,            # Для телефонов
        'default': FuzzyAlgorithm.TOKEN_SORT      # Для всех остальных полей
    }
    
    TRANSLITERATION = {  # Для данных с транслитерацией
        'name': FuzzyAlgorithm.PARTIAL_RATIO,     # Для имен (частичное сопоставление лучше при транслитерации)
        'surname': FuzzyAlgorithm.TOKEN_SORT,     # Для фамилий
        'patronymic': FuzzyAlgorithm.PARTIAL_RATIO, # Для отчеств
        'address': FuzzyAlgorithm.TOKEN_SET,      # Для адресов
        'default': FuzzyAlgorithm.WRatio          # Для всех остальных полей
    }


@dataclass
class MatchFieldConfig:
    """
    Настройки поля для сопоставления.
    
    :param field: имя поля
    :param weight: вес поля при расчете схожести (0-1)
    :param transliterate: включить транслитерацию для этого поля
    :param fuzzy_algorithm: алгоритм нечёткого сопоставления для данного поля (переопределяет общий)
    :param field_type: тип поля для выбора алгоритма из DomainSpecificAlgorithm (например, 'name', 'address')
    """
    field: str
    weight: float
    transliterate: bool = False
    fuzzy_algorithm: Optional[FuzzyAlgorithm] = None
    field_type: Optional[str] = None


@dataclass
class TransliterationConfig:
    """
    Настройки транслитерации для процесса сопоставления.
    
    :param enabled: включить поддержку транслитерации
    :param standard: название стандарта транслитерации
    :param threshold: порог схожести для транслитерации (0-1)
    :param auto_detect: автоматически определять язык и направление транслитерации
    :param normalize_names: нормализовать имена перед сопоставлением
    """
    enabled: bool = False
    standard: str = "Паспортная"
    threshold: float = 0.8
    auto_detect: bool = True
    normalize_names: bool = True


@dataclass
class MatchConfig:
    """
    Настройки для сопоставления и консолидации данных.
    
    :param fields: список настроек полей для сопоставления
    :param length_weight: вес длины строки при выборе записи для консолидации
    :param threshold: порог схожести для считывания записей совпадающими (0-1)
    :param block_field: поле для блокировки (первый символ)
    :param group_fields: дополнительные поля для группировки
    :param sort_before_match: сортировать записи перед сопоставлением
    :param sort_field: поле для сортировки записей
    :param transliteration: настройки транслитерации
    :param fuzzy_algorithm: основной алгоритм нечёткого сопоставления
    :param domain_algorithm: предопределенный набор алгоритмов для предметной области
    """
    fields: List[MatchFieldConfig]
    length_weight: float = 0.01
    threshold: float = 0.85
    block_field: Optional[str] = None
    group_fields: List[str] = field(default_factory=list)
    sort_before_match: bool = False
    sort_field: Optional[str] = None
    transliteration: TransliterationConfig = field(default_factory=TransliterationConfig)
    fuzzy_algorithm: FuzzyAlgorithm = FuzzyAlgorithm.RATIO
    domain_algorithm: Optional[DomainSpecificAlgorithm] = None

