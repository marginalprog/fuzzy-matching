# Fuzzy Matching

Библиотека для нечеткого сопоставления данных с поддержкой транслитерации между русским и английским языками.

## Особенности

- Нечеткое сопоставление текстовых данных с использованием алгоритмов из библиотеки RapidFuzz
- Поддержка пяти алгоритмов нечеткого сопоставления: RATIO, PARTIAL_RATIO, TOKEN_SORT, TOKEN_SET, WRatio
- Предметно-ориентированные настройки для разных типов данных (персональные данные, товары, компании)
- Поддержка транслитерации между русским и английским языками
- Несколько стандартов транслитерации (ГОСТ, научный, паспортный)
- Автоматическое определение языка текста
- Настраиваемые веса полей при сопоставлении
- Блокировка данных для повышения производительности
- Возможность консолидации совпадающих записей
- Генерация тестовых данных с контролируемыми искажениями
- Инструменты для анализа и сравнения производительности алгоритмов

## Структура проекта

```
fuzzy_matching/
├── core/               # Основные компоненты библиотеки
│   ├── data_matcher.py     # Класс для сопоставления данных
│   └── match_config_classes.py  # Классы конфигурации и перечисления алгоритмов
│
├── utils/              # Вспомогательные модули
│   ├── transliteration_utils.py  # Утилиты для транслитерации
│   └── data_generator.py  # Генератор тестовых данных
│
├── examples/           # Примеры использования
│   ├── simple_example.py             # Простой пример
│   ├── transliteration_example.py    # Пример с транслитерацией
│   ├── algorithm_comparison_example.py # Сравнение алгоритмов
│   └── domain_specific_example.py    # Предметно-ориентированные алгоритмы
│
├── tests/              # Тесты
│   ├── benchmark_test.py     # Тест производительности
│   └── advanced_benchmark.py  # Расширенный тест
│
├── results/            # Директория для результатов
│   └── reports/        # Отчеты по тестам производительности
│
└── __main__.py         # Точка входа для запуска из командной строки
```

## Установка

```bash
pip install -e .
```

## Быстрый старт

```python
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig,
    FuzzyAlgorithm, DomainSpecificAlgorithm
)

# Создать конфигурацию с транслитерацией
transliteration_config = TransliterationConfig(
    enabled=True,
    standard="Паспортная транслитерация",
    threshold=0.7
)

# Использование предметно-ориентированных алгоритмов
match_config = MatchConfig(
    fields=[
        MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True, field_type='surname'),
        MatchFieldConfig(field='Имя', weight=0.3, transliterate=True, field_type='name'),
        MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True, field_type='patronymic'),
        MatchFieldConfig(field='email', weight=0.1, transliterate=False)
    ],
    threshold=0.7,
    transliteration=transliteration_config,
    domain_algorithm=DomainSpecificAlgorithm.PERSON_DATA
)

# Создать matcher и сопоставить данные
matcher = DataMatcher(config=match_config)
matches, consolidated = matcher.match_and_consolidate(data1, data2)
```

## Выбор алгоритма нечеткого сопоставления

Библиотека поддерживает пять алгоритмов:

- **RATIO** - базовый алгоритм Левенштейна
- **PARTIAL_RATIO** - частичное сопоставление (найдет "Александр" в "Александр Пушкин")
- **TOKEN_SORT** - сортировка токенов (порядок слов не имеет значения)
- **TOKEN_SET** - множественное отношение токенов (лучше для перемешанных слов)
- **WRatio** - взвешенное комбинированное сопоставление (универсальный)

Доступны также предметно-ориентированные наборы алгоритмов:

- **PERSON_DATA** - для персональных данных (ФИО, клиентские базы)
- **PRODUCT_DATA** - для товаров и продуктов
- **COMPANY_DATA** - для организаций и компаний
- **TRANSLITERATION** - для данных с транслитерацией

## Примеры

Запустить пример через командную строку:

```bash
python -m fuzzy_matching simple      # Простой пример
python -m fuzzy_matching translit    # Пример с транслитерацией
python -m fuzzy_matching algorithms  # Сравнение алгоритмов
python -m fuzzy_matching domain      # Предметно-ориентированные алгоритмы
```

## Тестирование производительности

```bash
python -m fuzzy_matching benchmark   # Базовый тест производительности
python -m fuzzy_matching advanced    # Расширенный тест с графиками
python generate_reports.py           # Полный отчет по всем тестам
```

## Результаты тестирования

По результатам тестов можно сделать следующие выводы:

1. Применение предметно-ориентированных алгоритмов повышает точность сопоставления на 10-30% в зависимости от типа данных.
2. Включение транслитерации увеличивает время обработки на 140-280%, но необходимо для многоязычных данных.
3. Блокировка по первой букве критически важна для производительности при работе с большими объемами данных.
4. Алгоритм WRatio является наиболее универсальным, но TOKEN_SET показывает лучшие результаты для названий товаров и компаний. 