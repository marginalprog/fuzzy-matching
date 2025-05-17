# Fuzzy Matching

Библиотека для нечеткого сопоставления данных с поддержкой транслитерации между русским и английским языками.

## Особенности

- Нечеткое сопоставление строк с использованием различных алгоритмов
- Поддержка транслитерации между русским и английским языками
- Несколько стандартов транслитерации (ГОСТ, научная, паспортная)
- Предметно-ориентированные алгоритмы для разных типов данных
- Блокировка для ускорения сопоставления больших наборов данных
- Консолидация данных из разных источников

## Установка

```bash
pip install -e .
```

## Структура проекта

```
fuzzy_matching/
├── __init__.py
├── __main__.py
├── cli/
│   ├── __init__.py
│   ├── main.py
│   └── process_data.py
├── core/
│   ├── __init__.py
│   ├── data_matcher.py
│   └── match_config_classes.py
├── utils/
│   ├── __init__.py
│   ├── data_generator.py
│   └── transliteration/
│       ├── __init__.py
│       └── transliteration_utils.py
├── examples/
│   ├── __init__.py
│   ├── algorithm_comparison_example.py
│   ├── domain_specific_example.py
│   ├── simple_example.py
│   └── transliteration_example.py
├── tests/
│   ├── __init__.py
│   ├── test_data_matcher.py
│   └── test_transliteration.py
└── results/
    ├── reports/
    ├── анализ_результатов.md
    └── *.png
```

## Использование

### Командная строка

```bash
# Запуск интерактивного меню
python -m fuzzy_matching

# Запуск конкретного примера
python -m fuzzy_matching transliteration
python -m fuzzy_matching transliteration_matching
```

### Сопоставление данных из файлов

```bash
python -m fuzzy_matching.cli.process_data --mode match \
    --input1 dataset1.csv --format1 csv \
    --input2 dataset2.csv --format2 csv \
    --output-matches matches.json \
    --output-consolidated consolidated.json \
    --threshold 0.8 \
    --block-field Фамилия \
    --domain person
```

### Транслитерация данных из файла

```bash
python -m fuzzy_matching.cli.process_data --mode transliterate \
    --input1 russian_names.json --format1 json \
    --target-lang en \
    --output-consolidated english_names.json
```

## Примеры кода

### Простое сопоставление

```python
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig

# Создаем конфигурацию
config = MatchConfig(
    fields=[
        MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True),
        MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
        MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True),
        MatchFieldConfig(field='email', weight=0.1, transliterate=False)
    ],
    threshold=0.7
)

# Создаем экземпляр DataMatcher
matcher = DataMatcher(config=config)

# Данные для сопоставления
data1 = [
    {'Фамилия': 'Иванов', 'Имя': 'Александр', 'Отчество': 'Сергеевич', 'email': 'ivanov@example.ru'},
    {'Фамилия': 'Петров', 'Имя': 'Иван', 'Отчество': 'Петрович', 'email': 'petrov@example.ru'}
]

data2 = [
    {'Фамилия': 'Иванов', 'Имя': 'Александр', 'Отчество': 'Сергеевич', 'email': 'ivanov@example.com'},
    {'Фамилия': 'Петров', 'Имя': 'Иван', 'Отчество': 'Петрович', 'email': 'petrov@example.com'}
]

# Выполняем сопоставление
matches, consolidated = matcher.match_and_consolidate(data1, data2)

# Выводим результаты
print(f"Найдено {len(matches)} совпадений")
print(f"Консолидировано {len(consolidated)} записей")
```

### Транслитерация

```python
from fuzzy_matching.utils.transliteration.transliteration_utils import transliterate_ru_to_en, PASSPORT_STANDARD

# Транслитерация с русского на английский
ru_name = "Иванов Александр Сергеевич"
en_name = transliterate_ru_to_en(ru_name, PASSPORT_STANDARD)
print(f"{ru_name} -> {en_name}")  # Иванов Александр Сергеевич -> ivanov aleksandr sergeevich
```

## Лицензия

MIT 