# Fuzzy Matching

Библиотека для нечеткого сопоставления данных с поддержкой транслитерации между русским и английским языками.

## Особенности

- Нечеткое сопоставление текстовых данных с использованием алгоритмов из библиотеки RapidFuzz
- Поддержка транслитерации между русским и английским языками
- Несколько стандартов транслитерации (ГОСТ, научный, паспортный)
- Автоматическое определение языка текста
- Настраиваемые веса полей при сопоставлении
- Блокировка данных для повышения производительности
- Возможность консолидации совпадающих записей
- Генерация тестовых данных с контролируемыми искажениями

## Структура проекта

```
fuzzy_matching/
├── core/               # Основные компоненты библиотеки
│   ├── data_matcher.py     # Класс для сопоставления данных
│   └── match_config_classes.py  # Классы конфигурации
│
├── utils/              # Вспомогательные модули
│   ├── transliteration_utils.py  # Утилиты для транслитерации
│   └── data_generator.py  # Генератор тестовых данных
│
├── examples/           # Примеры использования
│   ├── simple_example.py     # Простой пример
│   └── transliteration_example.py  # Пример с транслитерацией
│
├── tests/              # Тесты
│   ├── benchmark_test.py     # Тест производительности
│   └── advanced_benchmark.py  # Расширенный тест
│
└── results/            # Директория для результатов
```

## Установка

```bash
pip install -e .
```

## Быстрый старт

```python
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig

# Создать конфигурацию с транслитерацией
transliteration_config = TransliterationConfig(
    enabled=True,
    standard="Паспортная транслитерация",
    threshold=0.7
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

# Создать matcher и сопоставить данные
matcher = DataMatcher(config=match_config)
matches, consolidated = matcher.match_and_consolidate(data1, data2)
```

## Примеры

Запустить простой пример:

```bash
python -m fuzzy_matching.examples.simple_example
```

Запустить пример с транслитерацией:

```bash
python -m fuzzy_matching.examples.transliteration_example
```

## Тестирование производительности

```bash
python -m fuzzy_matching.tests.benchmark_test
python -m fuzzy_matching.tests.advanced_benchmark
``` 