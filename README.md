# Fuzzy Matching

Библиотека для нечеткого сопоставления данных с поддержкой транслитерации между русским и английским языками.

## Особенности

- Нечеткое сопоставление строк с использованием различных алгоритмов
- Поддержка транслитерации между русским и английским языками
- Несколько стандартов транслитерации (ГОСТ, научная, паспортная)
- Гибкая настройка алгоритмов сопоставления для разных типов полей
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
├── api.py               # Программный интерфейс (API) библиотеки
├── cli/
│   ├── __init__.py
│   ├── demo.py          # Демонстрационное меню с примерами
│   ├── process_data.py  # Основной CLI-интерфейс
│   └── generate_test_data.py  # Утилита для генерации тестовых данных
├── core/
│   ├── __init__.py
│   ├── data_matcher.py  # Основная логика сопоставления
│   └── match_config_classes.py  # Классы конфигурации
├── utils/
│   ├── __init__.py
│   ├── cli_utils.py     # Утилиты для CLI
│   ├── data_generator.py  # Генератор тестовых данных
│   └── transliteration/  # Модуль транслитерации
│       ├── __init__.py
│       └── transliteration_utils.py
├── examples/            # Примеры использования
│   ├── __init__.py
│   ├── api_example.py
│   └── domain_specific_example.py
└── tests/               # Тесты
    ├── __init__.py
    └── test_transliteration.py
```

### Структура директорий данных

Данные хранятся в стандартизированной структуре каталогов:

```
data/
├── input/    # Входные данные (оригинальные и вариантные наборы)
└── output/   # Результаты обработки (совпадения и консолидированные данные)
```

При использовании CLI или API, файлы будут автоматически сохраняться в соответствующие каталоги.

## Использование

### Через командную строку (CLI)

#### Сопоставление данных

```bash
python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.json --format1 json --input2 data/input/variant.json --format2 json --match-fields "Фамилия:0.4:true:TOKEN_SORT,Имя:0.3:true:PARTIAL_RATIO,Отчество:0.2:true:RATIO,Email:0.1:false:RATIO" --threshold 0.7 --output-matches data/output/matches.json --output-consolidated data/output/consolidated.json --verbose
```

#### Транслитерация данных

```bash
python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/russian_data.json --format1 json --target-lang en --transliterate-fields "Фамилия,Имя,Отчество" --output-consolidated data/output/transliterated.json --verbose
```

#### Генерация тестовых данных

```bash
python -m fuzzy_matching.cli.process_data --mode generate --record-count 100 --typo-probability 0.1 --character-probability 0.05 --generate-fields "id,Фамилия,Имя,Отчество,Email" --output-original data/input/test_original.json --output-variant data/input/test_variant.json --verbose
```

Вы можете контролировать, какие поля генерировать, с помощью параметра `--generate-fields`. Доступные поля:
- `id` - уникальный идентификатор (всегда генерируется)
- `Фамилия` - фамилия
- `Имя` - имя
- `Отчество` - отчество
- `Email` - адрес электронной почты 
- `Телефон` - номер телефона
- `Пол` - пол (м/ж)

**Важно:** Генератор поддерживает только перечисленные выше поля с точно такими же наименованиями. При сопоставлении данных из внешних источников убедитесь, что имена полей соответствуют ожидаемым или используйте маппинг полей через параметр `--name-fields`.

### Работа с CSV-файлами

При использовании CSV-файлов вместо JSON, указывайте соответствующий формат с помощью параметров `--format1 csv` и `--format2 csv`. Для корректной работы с CSV-файлами важно, чтобы:

1. Заголовки столбцов соответствовали ожидаемым именам полей (`id`, `Фамилия`, `Имя`, `Отчество`, `Email`, `Телефон`, `Пол`)
2. Файл был в кодировке UTF-8
3. При необходимости использовался маппинг полей через параметр `--name-fields`

Обратите внимание, что регистр и точное написание имен полей имеют значение. Например, поле должно называться `Фамилия`, а не `фамилия` или `ФАМИЛИЯ`.

Пример использования с CSV:

```bash
python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.csv --format1 csv --input2 data/input/variant.csv --format2 csv --match-fields "Фамилия:0.4:false:TOKEN_SORT,Имя:0.3:false:PARTIAL_RATIO,Отчество:0.2:false:RATIO,Email:0.1:false:RATIO" --threshold 0.7 --output-matches data/output/matches.json --output-consolidated data/output/consolidated.csv --output-format csv --verbose
```

Если ваши CSV-файлы имеют другие имена столбцов, используйте параметр `--name-fields` для маппинга:

```bash
python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.csv --format1 csv --input2 data/input/variant.csv --format2 csv --name-fields "surname:Фамилия,name:Имя,patronymic:Отчество,mail:Email" --match-fields "Фамилия:0.4:false:TOKEN_SORT,Имя:0.3:false:PARTIAL_RATIO,Отчество:0.2:false:RATIO,Email:0.1:false:RATIO" --threshold 0.7 --output-consolidated data/output/consolidated.csv --output-format csv
```

### Через API

```python
from fuzzy_matching.api import create_config, match_datasets, transliterate_dataset, generate_test_datasets

# Создаем конфигурацию
config = create_config(
    fields=[
        {"field": "Фамилия", "weight": 0.6, "transliterate": True, "algorithm": "TOKEN_SORT"},
        {"field": "Имя", "weight": 0.3, "transliterate": True, "algorithm": "PARTIAL_RATIO"},
        {"field": "Отчество", "weight": 0.1, "transliterate": True, "algorithm": "RATIO"}
    ],
    threshold=0.7,
    transliteration_enabled=True
)

# Сопоставляем наборы данных
matches, consolidated = match_datasets(
    dataset1="data/file1.json", 
    dataset2="data/file2.json",
    config=config
)

# Сохраняем результаты
from fuzzy_matching.api import save_results
save_results(matches, consolidated, "matches.json", "consolidated.json")
```

## Алгоритмы нечеткого сопоставления

В библиотеке доступны следующие алгоритмы нечеткого сопоставления:

- **RATIO**: Базовый алгоритм Левенштейна (хорош для коротких строк и точных совпадений)
- **PARTIAL_RATIO**: Находит наилучшее совпадение подстроки (подходит для имен: Иван/Ваня)
- **TOKEN_SORT**: Сортирует слова перед сравнением (хорош для адресов, двойных фамилий)
- **TOKEN_SET**: Сравнивает множества слов (лучший для перемешанных слов и порядка)
- **WRatio**: Взвешенный комбинированный результат (универсальный алгоритм)

### Рекомендации по выбору алгоритмов

#### Для персональных данных
- **Имена**: `PARTIAL_RATIO` (учитывает уменьшительные формы, вариации написания)
- **Фамилии**: `TOKEN_SORT` (хорошо работает с составными фамилиями)
- **Отчества**: `RATIO` (обычно требуется точное совпадение)
- **Адреса**: `TOKEN_SET` (учитывает перестановку слов, разный порядок компонентов)
- **Email/телефоны**: `RATIO` (требуется высокая точность)

#### Для бизнес-данных
- **Названия компаний**: `TOKEN_SET` (порядок слов часто меняется, например "ООО Ромашка" и "Ромашка ООО")
- **Юридические названия**: `TOKEN_SORT` (важен порядок слов, но могут быть сокращения)
- **ИНН/КПП/ОГРН**: `RATIO` (требуется точное совпадение)
- **Товарные позиции**: `TOKEN_SET` (описания могут иметь разный порядок характеристик)

#### Для технических данных
- **Серийные номера**: `RATIO` (требуется точность, допустимы небольшие опечатки)
- **Артикулы товаров**: `RATIO` (требуется точность)
- **Технические описания**: `TOKEN_SET` (порядок элементов может варьироваться)
- **Коды ошибок**: `RATIO` (точное сопоставление)
- **URL-адреса**: `PARTIAL_RATIO` (учитывает общую часть URL)
- **Логи и трассировки**: `TOKEN_SORT` (сортировка помогает при разном порядке элементов)

#### Для научных данных
- **Химические формулы**: `TOKEN_SORT` (порядок элементов может меняться, но важен состав)
- **Научные термины**: `PARTIAL_RATIO` (может иметь вариации написания)
- **Библиографические ссылки**: `TOKEN_SET` (порядок авторов и элементов может варьироваться)
- **Классификационные коды**: `RATIO` (требуется точное совпадение)

#### Для многоязычных данных
- **Транслитерированные имена**: `PARTIAL_RATIO` (с transliterate=True)
- **Переведенные названия**: `TOKEN_SET` (порядок слов часто меняется при переводе)
- **Смешанные тексты**: `WRatio` (универсальный алгоритм с весовыми коэффициентами)

#### Общие рекомендации
- Для полей с короткими значениями (до 5 символов): `RATIO`
- Для полей с полными предложениями: `TOKEN_SET`
- Для полей, где важен порядок слов: `TOKEN_SORT`
- Для полей, где важна только общая часть: `PARTIAL_RATIO`
- Если не уверены, какой алгоритм выбрать: `WRatio` (комбинированный алгоритм)

## Интерактивное демо

Для запуска интерактивного меню с примерами:

```bash
python -m fuzzy_matching.cli.demo
# или
python -m fuzzy_matching
```

## Дополнительная документация

Полная документация доступна в коде каждого модуля и класса. 