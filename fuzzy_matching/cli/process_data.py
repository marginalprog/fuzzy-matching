#!/usr/bin/env python
"""
Скрипт для сопоставления или транслитерации данных из CSV/JSON файлов.
Запускается только через командную строку.

Структура проекта:
/fuzzy_matching/     # Корневая директория проекта
    /data/          # Директория для данных
        /input/     # Входящие файлы
        /output/    # Результаты обработки

Примеры использования:

1. Сопоставление данных и поиск похожих записей:
```
python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/test_ru_ru_original.json --format1 json --input2 data/input/test_ru_ru_variant.json --format2 json --output-matches data/output/matches.json --output-path data/output/consolidated.json --threshold 0.7 --match-fields "Фамилия:0.4:true:TOKEN_SORT,Имя:0.3:true:PARTIAL_RATIO,Отчество:0.2:true:RATIO,email:0.1:false:RATIO" --transliteration-standard "Passport" --verbose
```

2. Транслитерация данных между русским и английским языками:
```
python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_ru_ru_original.json --format1 json --target-lang en --output-path data/output/transliterated_en.json --transliterate-fields "Фамилия,Имя,Отчество" --transliteration-standard "Passport" --verbose
```

3. Генерация тестовых данных на русском языке с русскими названиями полей:
```
python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --generate-fields "id,Фамилия,Имя,Отчество,email" --language ru --field-names-format ru --verbose
```
# Результат: data/input/test_ru_ru_original.json и data/input/test_ru_ru_variant.json

4. Генерация тестовых данных на русском языке с английскими названиями полей:
```
python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --generate-fields "id,LastName,FirstName,MiddleName,email" --language ru --field-names-format en --verbose
```
# Результат: data/input/test_en_ru_original.json и data/input/test_en_ru_variant.json

5. Генерация тестовых данных на английском языке с английскими названиями полей:
```
python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --generate-fields "id,LastName,FirstName,MiddleName,email" --language en --field-names-format en --verbose
```
# Результат: data/input/test_en_en_original.json и data/input/test_en_en_variant.json

Описание основных параметров:
  --mode: режим работы (match, transliterate или generate)
  --input1, --input2: пути к входным файлам (относительно корня проекта, например data/input/file.json)
  --format1, --format2: форматы входных файлов (csv или json)
  --output-matches: путь для сохранения найденных совпадений (относительно корня проекта)
  --output-path: путь для сохранения результатов (транслитерированных или консолидированных данных)
  --output-original: путь для сохранения оригинальных сгенерированных данных
  --output-variant: путь для сохранения искаженных сгенерированных данных
  --threshold: порог схожести (от 0 до 1)
  --match-fields: конфигурация полей для сопоставления
  --target-lang: целевой язык для транслитерации (ru или en)
  --transliteration-standard: стандарт транслитерации ("GOST", "Scientific" или "Passport")
  --generate-fields: список полей для генерации в режиме generate
  --language: язык генерируемых данных (ru или en)
  --field-names-format: формат названий полей (ru или en)
  --double-char-probability: вероятность дублирования буквы (от 0 до 1)
  --change-char-probability: вероятность замены буквы (от 0 до 1)
  --change-name-probability: вероятность полной замены ФИО (от 0 до 1)
  --change-domain-probability: вероятность изменения домена в email (от 0 до 1)
  --double-number-probability: вероятность дублирования цифры в телефоне (от 0 до 1)
  --suffix-probability: вероятность добавления суффикса к ФИО (от 0 до 1)
  --swap-char-probability: вероятность перестановки символов (от 0 до 1, по умолчанию 0.1)

Примечание:
- Все пути к файлам указываются относительно корня проекта
- Входные файлы должны находиться в директории data/input
- Результаты сохраняются в директорию data/output
- При генерации тестовых данных файлы именуются по шаблону: test_[формат_полей]_[язык]_[тип].json
"""

import argparse
import sys
import os
import json
import csv
from prettytable import PrettyTable

# Классы для цветного вывода в терминале
class Colors:
    """Класс с ANSI-кодами цветов для терминала"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig, 
    FuzzyAlgorithm
)
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.utils.cli_utils import generate_and_save_test_data
from fuzzy_matching.utils.data_generator import DataGenerator, Language

# Определение путей по умолчанию для файлов данных и результатов
# Находим корневую директорию проекта (где находится setup.py или pyproject.toml)
def find_project_root():
    """
    Находит корневую директорию проекта, поднимаясь вверх по дереву директорий,
    пока не найдет setup.py или pyproject.toml
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != '/':
        if os.path.exists(os.path.join(current_dir, 'setup.py')) or \
           os.path.exists(os.path.join(current_dir, 'pyproject.toml')):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = find_project_root()

# Меняем текущую рабочую директорию на корневую директорию проекта
os.chdir(PROJECT_ROOT)

# Определяем пути относительно корня проекта
DATA_INPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'input')
DATA_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'output')

# Создаем директории, если они еще не существуют
os.makedirs(DATA_INPUT_DIR, exist_ok=True)
os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)

# Создаем скрытый файл в директории, чтобы git не игнорировал пустую директорию
if not os.listdir(DATA_INPUT_DIR):
    with open(os.path.join(DATA_INPUT_DIR, '.gitkeep'), 'w') as f:
        f.write('# Эта директория используется для хранения входных данных\n')

if not os.listdir(DATA_OUTPUT_DIR):
    with open(os.path.join(DATA_OUTPUT_DIR, '.gitkeep'), 'w') as f:
        f.write('# Эта директория используется для хранения результатов обработки\n')

def parse_name_fields(fields_str, match_fields=None):
    """
    Парсит строку с соответствием полей в формате 'source1:target1,source2:target2'
    и возвращает словарь соответствий.
    
    :param fields_str: строка с соответствием полей
    :param match_fields: список MatchFieldConfig для определения имен полей
    :return: словарь соответствий полей
    """
    if not fields_str:
        # Если есть match_fields, используем их имена полей
        if match_fields:
            return {field.field: field.field for field in match_fields}
        
        # Определяем язык на основе наличия файлов
        if os.path.exists(os.path.join(DATA_INPUT_DIR, 'test_en_en_original.json')):
            return {
                'id': 'id',
                'LastName': 'LastName',
                'FirstName': 'FirstName',
                'MiddleName': 'MiddleName',
                'email': 'email'
            }
        return {
            'id': 'id',
            'Фамилия': 'Фамилия',
            'Имя': 'Имя',
            'Отчество': 'Отчество',
            'email': 'email',
            'Телефон': 'Телефон'
        }
    
    name_fields = {}
    pairs = fields_str.split(',')
    for pair in pairs:
        source, target = pair.split(':')
        name_fields[source.strip()] = target.strip()
    
    return name_fields


def parse_match_fields(fields_str):
    """
    Парсит строку с конфигурацией полей для сопоставления в формате
    'field1:weight1:transliterate1[:algorithm1],field2:weight2:transliterate2[:algorithm2]'
    где algorithm - опциональное название алгоритма из FuzzyAlgorithm (RATIO, PARTIAL_RATIO, TOKEN_SORT, TOKEN_SET, WRatio)
    
    :param fields_str: строка конфигурации полей
    :return: список объектов MatchFieldConfig
    """
    if not fields_str:
        # Используем базовый набор полей по умолчанию
        return [
            MatchFieldConfig(field='id', weight=0.0, transliterate=False),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False)
        ]
    
    match_fields = []
    pairs = fields_str.split(',')
    for pair in pairs:
        parts = pair.split(':')
        field = parts[0].strip()
        weight = float(parts[1]) if len(parts) > 1 else 1.0
        transliterate = parts[2].lower() == 'true' if len(parts) > 2 else False
        
        # Проверяем, указан ли алгоритм
        algorithm = None
        if len(parts) > 3 and parts[3].strip():
            algorithm_name = parts[3].strip()
            try:
                algorithm = getattr(FuzzyAlgorithm, algorithm_name)
            except AttributeError:
                print(f"{Colors.YELLOW}Предупреждение: неизвестный алгоритм '{algorithm_name}' для поля '{field}'. "
                      f"Будет использован алгоритм по умолчанию.{Colors.ENDC}")
        
        match_fields.append(MatchFieldConfig(
            field=field,
            weight=weight,
            transliterate=transliterate,
            fuzzy_algorithm=algorithm
        ))
    
    return match_fields


def main():
    # Выводим информацию о путях в начале выполнения
    # print(f"\nТекущая рабочая директория: {os.getcwd()}")
    # print(f"Корневая директория проекта: {PROJECT_ROOT}")
    # print(f"Директория для входных данных: {DATA_INPUT_DIR}")
    # print(f"Директория для результатов: {DATA_OUTPUT_DIR}\n")

    parser = argparse.ArgumentParser(description="Сопоставление или транслитерация данных из файлов")
    
    # Общие параметры
    parser.add_argument('--mode', choices=['match', 'transliterate', 'generate'], required=True,
                      help="Режим работы: match (сопоставление), transliterate (транслитерация) или generate (генерация тестовых данных)")
    
    # Параметры для входных данных
    parser.add_argument('--input1',
                      help="Путь к первому входному файлу (CSV или JSON)")
    parser.add_argument('--format1', choices=['csv', 'json'],
                      help="Формат первого входного файла")
    
    # Параметры для режима сопоставления
    parser.add_argument('--input2',
                      help="Путь ко второму входному файлу (для режима сопоставления)")
    parser.add_argument('--format2', choices=['csv', 'json'],
                      help="Формат второго входного файла")
    
    # Параметры для транслитерации
    parser.add_argument('--target-lang', choices=['ru', 'en'],
                      help="Целевой язык для транслитерации (ru или en)")
    parser.add_argument('--transliteration-standard', choices=['GOST', 'Scientific', 'Passport'], 
                      default='Passport',
                      help="Стандарт транслитерации (по умолчанию Passport)")
    
    # Параметры для вывода
    parser.add_argument('--output-matches',
                      help=f"Путь для сохранения результатов сопоставления (по умолчанию {os.path.join(DATA_OUTPUT_DIR, 'matches.json')})")
    parser.add_argument('--output-path',
                      help=f"Путь для сохранения результатов (транслитерированных или консолидированных данных) (по умолчанию {os.path.join(DATA_OUTPUT_DIR, 'output.json')})")
    parser.add_argument('--output-format', choices=['csv', 'json'], default='json',
                      help="Формат выходных файлов (по умолчанию json)")
    parser.add_argument('--verbose', action='store_true',
                      help="Подробный вывод информации о процессе")
    
    # Параметры для генерации тестовых данных
    parser.add_argument('--output-original',
                      help=f"Путь для сохранения оригинальных данных (по умолчанию {os.path.join(DATA_INPUT_DIR, 'original.json')})")
    parser.add_argument('--output-variant',
                      help=f"Путь для сохранения искаженных данных (по умолчанию {os.path.join(DATA_INPUT_DIR, 'variant.json')})")
    parser.add_argument('--record-count', type=int, default=100,
                      help="Количество записей для генерации (по умолчанию 100)")
    parser.add_argument('--double-char-probability', type=float, default=0.1,
                      help="Вероятность дублирования буквы (от 0 до 1, по умолчанию 0.1)")
    parser.add_argument('--change-char-probability', type=float, default=0.05,
                      help="Вероятность замены буквы (от 0 до 1, по умолчанию 0.05)")
    parser.add_argument('--change-name-probability', type=float, default=0.1,
                      help="Вероятность полной замены ФИО (от 0 до 1, по умолчанию 0.1)")
    parser.add_argument('--change-domain-probability', type=float, default=0.3,
                      help="Вероятность изменения домена в email (от 0 до 1, по умолчанию 0.3)")
    parser.add_argument('--double-number-probability', type=float, default=0.3,
                      help="Вероятность дублирования цифры в телефоне (от 0 до 1, по умолчанию 0.3)")
    parser.add_argument('--suffix-probability', type=float, default=0.1,
                      help="Вероятность добавления суффикса к ФИО (от 0 до 1, по умолчанию 0.1)")
    parser.add_argument('--generate-fields',
                      help="Список полей для генерации, разделенных запятыми (например: id,Фамилия,Имя,Отчество,email для русского или id,LastName,FirstName,MiddleName,email для английского)")
    parser.add_argument('--language', choices=['ru', 'en'], default='ru',
                      help="Язык генерируемых данных (ru - русский, en - английский, по умолчанию ru)")
    parser.add_argument('--field-names-format', choices=['ru', 'en'], default=None,
                      help="Формат названий полей (ru - русские названия, en - английские названия, по умолчанию соответствует языку)")
    
    # Параметры конфигурации
    parser.add_argument('--threshold', type=float, default=0.7,
                      help="Порог схожести для сопоставления (от 0 до 1)")
    parser.add_argument('--block-field',
                      help="Поле для блокировки (ускоряет сопоставление)")
    parser.add_argument('--name-fields',
                      help="Соответствие полей в формате 'source1:target1,source2:target2'")
    parser.add_argument('--match-fields',
                      help="""Конфигурация полей для сопоставления в формате 'field1:weight1:transliterate1[:algorithm1],field2:weight2:transliterate2[:algorithm2]'
Доступные алгоритмы сопоставления:
- RATIO: Базовый алгоритм Левенштейна (хорош для коротких строк и точных совпадений)
- PARTIAL_RATIO: Находит наилучшее совпадение подстроки (подходит для имен: Иван/Ваня)
- TOKEN_SORT: Сортирует слова перед сравнением (хорош для адресов, двойных фамилий)
- TOKEN_SET: Сравнивает множества слов (лучший для перемешанных слов и порядка)
- WRatio: Взвешенный комбинированный результат (универсальный алгоритм)

Рекомендации по выбору алгоритмов:
Персональные данные:
- Имена: PARTIAL_RATIO
- Фамилии: TOKEN_SORT
- Адреса: TOKEN_SET
- email/телефоны: RATIO

Бизнес-данные:
- Названия компаний: TOKEN_SET
- Юридические названия: TOKEN_SORT
- ИНН/КПП/ОГРН: RATIO
- Товарные позиции: TOKEN_SET

Технические данные:
- Серийные номера: RATIO
- Артикулы товаров: RATIO
- Технические описания: TOKEN_SET
- URL-адреса: PARTIAL_RATIO

Общие рекомендации:
- Для коротких значений: RATIO
- Для полных предложений: TOKEN_SET
- Где важен порядок слов: TOKEN_SORT
- Если не уверены: WRatio""")
    parser.add_argument('--transliterate-fields',
                      help="Поля для транслитерации, разделенные запятыми")
    parser.add_argument('--fuzzy-algorithm', choices=['RATIO', 'PARTIAL_RATIO', 'TOKEN_SORT', 'TOKEN_SET', 'WRatio'], 
                      default='RATIO',
                      help="Основной алгоритм нечеткого сопоставления (для полей без явно указанного алгоритма)")
    parser.add_argument('--swap-char-probability', type=float, default=0.1,
                      help="Вероятность перестановки символов (от 0 до 1, по умолчанию 0.1)")
    
    args = parser.parse_args()

    # Создаем директории для данных, если они не существуют
    os.makedirs(DATA_INPUT_DIR, exist_ok=True)
    os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)

    # Создаем скрытые файлы в директориях, чтобы git не игнорировал пустые директории
    if not os.listdir(DATA_INPUT_DIR):
        with open(os.path.join(DATA_INPUT_DIR, '.gitkeep'), 'w') as f:
            f.write('# Эта директория используется для хранения входных данных\n')

    if not os.listdir(DATA_OUTPUT_DIR):
        with open(os.path.join(DATA_OUTPUT_DIR, '.gitkeep'), 'w') as f:
            f.write('# Эта директория используется для хранения результатов обработки\n')

    # Если указаны пути для сохранения результатов, создаем директории
    if args.output_matches:
        os.makedirs(os.path.dirname(args.output_matches), exist_ok=True)
    if args.output_path:
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    if args.output_original:
        os.makedirs(os.path.dirname(args.output_original), exist_ok=True)
    if args.output_variant:
        os.makedirs(os.path.dirname(args.output_variant), exist_ok=True)

    # Режим генерации тестовых данных
    if args.mode == 'generate':
        if args.verbose:
            print(f"\n{Colors.BOLD}{Colors.GREEN}Генерация тестовых данных...{Colors.ENDC}")
        
        # Определяем вероятности искажений
        probabilities = {
            'double_char_probability': args.double_char_probability,
            'change_char_probability': args.change_char_probability,
            'swap_char_probability': args.swap_char_probability,
            'change_name_probability': args.change_name_probability,
            'change_domain_probability': args.change_domain_probability,
            'double_number_probability': args.double_number_probability,
            'suffix_probability': args.suffix_probability
        }
        
        # Создаем генератор с указанными параметрами
        lang = Language.RUS if args.language.lower() == 'ru' else Language.ENG
        dg = DataGenerator(language=lang, probabilities=probabilities)
        
        # Если формат названий полей не указан, используем язык
        field_names_format = args.field_names_format or args.language
        
        # Устанавливаем формат названий полей
        if field_names_format.lower() == 'ru':
            dg.FIELD_NAMES = dg.FIELD_NAMES_RU
        else:
            dg.FIELD_NAMES = dg.FIELD_NAMES_EN
        
        # Определяем поля для генерации
        default_fields = [
            'id',
            'last_name',
            'first_name',
            'middle_name',
            'email',
            'phone',
            'gender'
        ]
        
        # Если указаны конкретные поля, используем их
        gen_fields = default_fields
        if args.generate_fields:
            selected_fields = [field.strip() for field in args.generate_fields.split(',')]
            
            # Добавляем id, если его нет, так как он необходим для работы
            if 'id' not in selected_fields:
                selected_fields.insert(0, 'id')
            
            # Преобразуем названия полей в их типы
            field_types = []
            for field in selected_fields:
                if field == 'id':
                    field_types.append('id')
                elif field == 'email':
                    field_types.append('email')
                else:
                    # Ищем тип поля в словарях FIELD_NAMES
                    field_type = None
                    if field_names_format.lower() == 'ru':
                        for key, value in dg.FIELD_NAMES_RU.items():
                            if value == field:
                                field_type = key
                                break
                    else:
                        for key, value in dg.FIELD_NAMES_EN.items():
                            if value == field:
                                field_type = key
                                break
                    if field_type:
                        field_types.append(field_type)
            
            gen_fields = field_types
            
            if args.verbose:
                print(f"{Colors.GREEN}Генерация полей: {', '.join(selected_fields)}{Colors.ENDC}")
        
        # Определяем пути по умолчанию, если пути не указаны
        field_format = field_names_format.lower()
        data_lang = args.language.lower()

        # Формируем имена файлов по шаблону
        original_filename = f'test_{field_format}_{data_lang}_original.{args.output_format}'
        variant_filename = f'test_{field_format}_{data_lang}_variant.{args.output_format}'

        # Если указаны пути к директориям, используем их
        if args.output_original:
            output_original = os.path.join(args.output_original, original_filename)
        else:
            output_original = os.path.join(DATA_INPUT_DIR, original_filename)

        if args.output_variant:
            output_variant = os.path.join(args.output_variant, variant_filename)
        else:
            output_variant = os.path.join(DATA_INPUT_DIR, variant_filename)

        # Создаем директории, если они не существуют
        os.makedirs(os.path.dirname(output_original), exist_ok=True)
        os.makedirs(os.path.dirname(output_variant), exist_ok=True)

        # Генерируем данные
        original_list, variant_list = generate_and_save_test_data(
            probabilities=probabilities,
            gen_fields=gen_fields,
            count=args.record_count,
            file_format=args.output_format,
            original_file=output_original,
            variant_file=output_variant,
            language=args.language,
            field_names_format=field_names_format,
            verbose=args.verbose
        )
        
        if args.verbose:
            print(f"\n{Colors.GREEN}Сгенерировано {len(original_list)} оригинальных и {len(variant_list)} искаженных записей{Colors.ENDC}")
            print(f"\n{Colors.CYAN}Оригинальные данные сохранены в {Colors.YELLOW}{output_original}{Colors.ENDC}")
            print(f"{Colors.CYAN}Искаженные данные сохранены в {Colors.YELLOW}{output_variant}{Colors.ENDC}")
            print(f"\n{Colors.YELLOW}Язык данных: {args.language.upper()}{Colors.ENDC}")
            print(f"{Colors.YELLOW}Формат названий полей: {field_names_format.upper()}{Colors.ENDC}")
        
        # Вывод первых 5 записей сгенерированных и изменённых данных в виде таблицы
        print(f"\n{Colors.CYAN}Первые 5 сгенерированных и измененных записей:{Colors.ENDC}")
        
        # Создаем таблицу
        table = PrettyTable()
        
        # Добавляем столбец для указания типа записи (оригинал/искаженная)
        field_names = ["Тип"] + [dg.FIELD_NAMES.get(field, field) for field in gen_fields]
        table.field_names = field_names
        
        # Добавляем данные в таблицу
        for i in range(min(5, len(original_list))):
            orig_row = ["Оригинал"]
            for field in gen_fields:
                field_name = dg.FIELD_NAMES.get(field, field)
                orig_row.append(original_list[i].get(field_name, ""))
            table.add_row(orig_row)
            
            if i < len(variant_list):
                var_row = ["Искаженная"]
                for field in gen_fields:
                    field_name = dg.FIELD_NAMES.get(field, field)
                    var_row.append(variant_list[i].get(field_name, ""))
                table.add_row(var_row)
                
                # Добавляем пустую строку для разделения пар записей
                if i < min(4, len(original_list) - 1):
                    table.add_row([""] * len(field_names))
        
        # Настраиваем стиль таблицы
        table.align = "l"  # Выравнивание по левому краю
        table.border = True
        table.header = True
        
        # Выводим таблицу
        print(table)
        
        # Сохраняем результаты
        if args.output_format == 'json':
            if output_original:
                save_to_json(original_list, output_original)
            if output_variant:
                save_to_json(variant_list, output_variant)
        else:
            if output_original:
                save_to_csv(original_list, output_original)
            if output_variant:
                save_to_csv(variant_list, output_variant)
        
        if args.verbose:
            print(f"{Colors.GREEN}Данные успешно сохранены:{Colors.ENDC}")
            print(f"{Colors.CYAN}- Оригинальные данные: {Colors.YELLOW}{output_original}{Colors.ENDC}")
            print(f"{Colors.CYAN}- Вариантные данные:  {Colors.YELLOW}{output_variant}{Colors.ENDC}")

        return
    
    # Определяем соответствие полей
    name_fields = parse_name_fields(args.name_fields, parse_match_fields(args.match_fields))
    
    # Создаем конфигурацию полей для сопоставления
    match_fields = parse_match_fields(args.match_fields)
    
    # Настраиваем транслитерацию, если она нужна
    transliteration_config = TransliterationConfig(
        enabled=(args.mode == 'transliterate'),
        standard=args.transliteration_standard,
        threshold=args.threshold,
        auto_detect=True,
        normalize_names=True
    )
    
    # Определяем основной алгоритм нечеткого сопоставления
    fuzzy_algorithm = None
    if args.fuzzy_algorithm:
        try:
            fuzzy_algorithm = getattr(FuzzyAlgorithm, args.fuzzy_algorithm)
        except AttributeError:
            print(f"{Colors.YELLOW}Предупреждение: неизвестный алгоритм '{args.fuzzy_algorithm}'. "
                  f"Будет использован алгоритм TOKEN_SORT.{Colors.ENDC}")
            fuzzy_algorithm = FuzzyAlgorithm.TOKEN_SORT
    
    # Создаем конфигурацию
    config = MatchConfig(
        fields=match_fields,
        threshold=args.threshold,
        block_field=args.block_field,
        transliteration=transliteration_config,
        fuzzy_algorithm=fuzzy_algorithm
    )
    
    # Создаем экземпляр DataMatcher
    matcher = DataMatcher(config=config)
    
    # Проверяем существование входных файлов для режимов match и transliterate
    if args.mode in ['match', 'transliterate']:
        if not args.input1:
            print(f"{Colors.RED}Ошибка: для режима {args.mode} необходимо указать входной файл (--input1){Colors.ENDC}")
            sys.exit(1)
            
        if not args.format1:
            print(f"{Colors.RED}Ошибка: для режима {args.mode} необходимо указать формат входного файла (--format1){Colors.ENDC}")
            sys.exit(1)
            
    if not os.path.exists(args.input1):
            print(f"{Colors.RED}Ошибка: файл {args.input1} не найден{Colors.ENDC}")
            sys.exit(1)
    
    if args.mode == 'match' and args.input2 and not os.path.exists(args.input2):
        print(f"{Colors.RED}Ошибка: файл {args.input2} не найден{Colors.ENDC}")
        sys.exit(1)
    
    # Загружаем первый набор данных
    try:
        if args.verbose:
            print(f"{Colors.CYAN}Загрузка данных из {args.input1}...{Colors.ENDC}")
        
        data1 = None
        if args.format1 == 'csv':
            data1 = matcher.load_from_csv(args.input1, name_fields)
        else:
            data1 = matcher.load_from_json(args.input1, name_fields)
        
        if args.verbose:
            print(f"{Colors.GREEN}Загружено {len(data1)} записей из {args.input1}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}Ошибка при загрузке данных из {args.input1}: {str(e)}{Colors.ENDC}")
        sys.exit(1)
    
    # Режим транслитерации
    if args.mode == 'transliterate':
        if not args.target_lang:
            print(f"{Colors.RED}Ошибка: для режима транслитерации необходимо указать целевой язык (--target-lang){Colors.ENDC}")
            sys.exit(1)
            
        if not args.transliterate_fields:
            print(f"{Colors.RED}Ошибка: необходимо указать поля для транслитерации (--transliterate-fields){Colors.ENDC}")
            sys.exit(1)
        
        if args.verbose:
            print(f"{Colors.CYAN}Транслитерация данных из {args.input1} в {args.target_lang}...{Colors.ENDC}")
        
        # Определяем поля для транслитерации
        fields_to_transliterate = [f.strip() for f in args.transliterate_fields.split(',')]
        
        # Загружаем данные без маппинга полей
        try:
            if args.verbose:
                print(f"{Colors.CYAN}Загрузка данных из {args.input1}...{Colors.ENDC}")
            
            data1 = None
            if args.format1 == 'csv':
                data1 = matcher.load_from_csv(args.input1, {})  # Пустой маппинг для сохранения оригинальных имен полей
            else:
                data1 = matcher.load_from_json(args.input1, None)  # None для сохранения оригинальных имен полей
            
            if args.verbose:
                print(f"{Colors.GREEN}Загружено {len(data1)} записей из {args.input1}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Ошибка при загрузке данных из {args.input1}: {str(e)}{Colors.ENDC}")
            sys.exit(1)
        
        # Проверяем, что все указанные поля существуют в данных
        if data1 and len(data1) > 0:
            missing_fields = [field for field in fields_to_transliterate if field not in data1[0]]
            if missing_fields:
                print(f"{Colors.RED}Ошибка: следующие поля отсутствуют в данных: {', '.join(missing_fields)}{Colors.ENDC}")
                print(f"{Colors.RED}Доступные поля: {', '.join(data1[0].keys())}{Colors.ENDC}")
                sys.exit(1)
        
        # Обновляем конфигурацию для включения транслитерации
        config.transliteration.enabled = True
        config.transliteration.standard = args.transliteration_standard or "Passport"
        
        # Обновляем поля в конфигурации для транслитерации
        config.fields = [
            MatchFieldConfig(
                field=field,
                weight=1.0,
                transliterate=True,
                fuzzy_algorithm=FuzzyAlgorithm.TOKEN_SORT
            )
            for field in fields_to_transliterate
        ]
        
        # Пересоздаем matcher с обновленной конфигурацией
        matcher = DataMatcher(config=config)
        
        # Транслитерируем данные
        transliterated_data = matcher.transliterate_data(
            data1, 
            target_lang=args.target_lang,
            fields=fields_to_transliterate
        )
        
        if args.verbose:
            print("\nПервые 5 оригинальных записей:")
            table = PrettyTable()
            table.field_names = ["№"] + fields_to_transliterate
            
            for i, record in enumerate(data1[:5], 1):
                row = [i]
                for field in fields_to_transliterate:
                    row.append(record.get(field, ""))
                table.add_row(row)
            
            print(table)
            
            print("\nПервые 5 транслитерированных записей:")
            table = PrettyTable()
            table.field_names = ["№"] + fields_to_transliterate
            
            for i, record in enumerate(transliterated_data[:5], 1):
                row = [i]
                for field in fields_to_transliterate:
                    row.append(record.get(field, ""))
                table.add_row(row)
            
            print(table)
        
        # Используем путь по умолчанию, если путь не указан
        output_path = args.output_path or os.path.join(DATA_OUTPUT_DIR, f'transliterated.{args.output_format}')
        
        # Сохраняем результаты
        if output_path:
            if args.output_format == 'json':
                matcher.save_consolidated_to_json(transliterated_data, output_path)
            else:
                matcher.save_consolidated_to_csv(transliterated_data, output_path)
            
            if args.verbose:
                print(f"{Colors.CYAN}Результаты сохранены в {Colors.YELLOW}{output_path}{Colors.ENDC}\n")
        else:
            # Выводим результаты на экран
            print(f"\n{Colors.YELLOW}Результаты транслитерации:{Colors.ENDC}")
            for i, record in enumerate(transliterated_data[:10]):
                print(f"{Colors.GREEN}{i+1}. {record}{Colors.ENDC}")
            
            if len(transliterated_data) > 10:
                print(f"{Colors.BLUE}... и еще {len(transliterated_data) - 10} записей{Colors.ENDC}")
    
    # Режим сопоставления
    elif args.mode == 'match':
        if not args.input2:
            print(f"{Colors.RED}Ошибка: для режима сопоставления необходимо указать второй входной файл (--input2){Colors.ENDC}")
            sys.exit(1)
        
        if not args.format2:
            print(f"{Colors.RED}Ошибка: для режима сопоставления необходимо указать формат второго файла (--format2){Colors.ENDC}")
            sys.exit(1)
        
        # Загружаем второй набор данных
        try:
            if args.verbose:
                print(f"{Colors.CYAN}Загрузка данных из {args.input2}...{Colors.ENDC}")
            
            data2 = None
            if args.format2 == 'csv':
                data2 = matcher.load_from_csv(args.input2, name_fields)
            else:
                data2 = matcher.load_from_json(args.input2, name_fields)
            
            if args.verbose:
                print(f"{Colors.GREEN}Загружено {len(data2)} записей из {args.input2}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Ошибка при загрузке данных из {args.input2}: {str(e)}{Colors.ENDC}")
            sys.exit(1)
        
        # Выполняем сопоставление
        if args.verbose:
            print(f"\n{Colors.CYAN}Сопоставление данных...{Colors.ENDC}")
        
        matches, consolidated = matcher.match_and_consolidate(data1, data2)
        
        if args.verbose:
            print(f"\n{Colors.GREEN}Найдено {len(matches)} совпадений{Colors.ENDC}")
            print(f"{Colors.GREEN}Консолидировано {len(consolidated)} записей{Colors.ENDC}")
            
            # Выводим примеры сопоставлений
            if matches:
                print(f"\n{Colors.CYAN}Примеры сопоставлений (первые 5):{Colors.ENDC}")
                
                # Создаем таблицу для сопоставлений
                match_table = PrettyTable()
                
                # Определяем поля для таблицы на основе полей сопоставления
                field_names = [f.field for f in config.fields]
                
                # Стандартизируем имя поля email
                field_names = ['email' if f.lower() == 'email' else f for f in field_names]
                
                match_table.field_names = ["Тип"] + field_names + ["Схожесть"]
                
                # Добавляем данные в таблицу
                for match in matches[:5]:
                    orig = match['Оригинал']
                    var = match['Вариант']
                    similarity = match['Схожесть']
                    
                    # Добавляем строку для оригинала
                    orig_row = ["Оригинал"]
                    for field in field_names:
                        # Проверяем оба варианта написания email
                        if field.lower() == 'email':
                            value = orig.get('email', orig.get('email', ""))
                        else:
                            value = orig.get(field, "")
                        orig_row.append(value)
                    orig_row.append("")  # Пустая ячейка для схожести
                    match_table.add_row(orig_row)
                    
                    # Добавляем строку для варианта
                    var_row = ["Вариант"]
                    for field in field_names:
                        # Проверяем оба варианта написания email
                        if field.lower() == 'email':
                            value = var.get('email', var.get('email', ""))
                        else:
                            value = var.get(field, "")
                        var_row.append(value)
                    var_row.append(f"{similarity:.2%}")  # Схожесть
                    match_table.add_row(var_row)
                    
                    # Добавляем пустую строку для разделения пар записей
                    if match != matches[:5][-1]:
                        match_table.add_row([""] * len(match_table.field_names))
                
                # Настраиваем стиль таблицы
                match_table.align = "l"
                match_table.border = True
                match_table.header = True
                
                print(match_table)
                print()  # Добавляем отступ между блоками
            
            # Выводим примеры консолидированных записей
            if consolidated:
                print(f"\n{Colors.CYAN}Примеры консолидированных записей (первые 10):{Colors.ENDC}")
                
                # Создаем таблицу для консолидированных записей
                cons_table = PrettyTable()
                
                # Определяем поля для таблицы на основе полей сопоставления
                field_names = [f.field for f in config.fields]
                
                # Стандартизируем имя поля email
                field_names = ['email' if f.lower() == 'email' else f for f in field_names]
                
                cons_table.field_names = field_names
                
                # Добавляем данные в таблицу
                for i, record in enumerate(consolidated[:10]):
                    row = []
                    for field in field_names:
                        # Проверяем оба варианта написания email
                        if field.lower() == 'email':
                            value = record.get('email', record.get('email', ""))
                        else:
                            value = record.get(field, "")
                        row.append(value)
                    cons_table.add_row(row)
                
                # Настраиваем стиль таблицы
                cons_table.align = "l"
                cons_table.border = True
                cons_table.header = True
                
                print(cons_table)
                print()  # Добавляем отступ между блоками
        
        # Сохраняем результаты
        if args.output_matches:
            if args.output_format == 'json':
                matcher.save_matches_to_json(matches, args.output_matches)
            else:
                matcher.save_matches_to_csv(matches, args.output_matches)
            
            if args.verbose:
                print(f"\n{Colors.CYAN}Совпадения сохранены в {Colors.YELLOW}{args.output_matches}{Colors.ENDC}")
        
        if args.output_path:
            if args.output_format == 'json':
                matcher.save_consolidated_to_json(consolidated, args.output_path)
            else:
                matcher.save_consolidated_to_csv(consolidated, args.output_path)
            
            if args.verbose:
                print(f"{Colors.CYAN}Консолидированные данные сохранены в {Colors.YELLOW}{args.output_path}{Colors.ENDC}")
                print()  # Добавляем отступ между блоками

# Добавляем функции для сохранения данных в JSON и CSV
def save_to_json(data, filename):
    """Сохраняет данные в JSON-файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_to_csv(data, filename):
    """Сохраняет данные в CSV-файл"""
    if not data:
        return
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    # Проверяем, запущен ли скрипт как модуль
    if not __package__:
        print(f"{Colors.RED}Ошибка: Скрипт должен запускаться как модуль Python.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Правильный способ запуска:{Colors.ENDC}")
        print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data [аргументы]{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}В PyCharm:{Colors.ENDC}")
        print("1. Run -> Edit Configurations")
        print("2. Module name: fuzzy_matching.cli.process_data")
        print("3. Working directory: корневая директория проекта")
        sys.exit(1)
    
    try:
        main()
    except Exception as e:
        print(f"{Colors.RED}Ошибка: {str(e)}{Colors.ENDC}")
        sys.exit(1) 