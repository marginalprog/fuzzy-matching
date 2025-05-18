#!/usr/bin/env python
"""
Скрипт для сопоставления или транслитерации данных из CSV/JSON файлов.
Запускается только через командную строку.

Примеры использования:

1. Сопоставление данных и поиск похожих записей:
```
python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.json --format1 json --input2 data/input/variant.json --format2 json --output-matches data/output/matches.json --output-consolidated data/output/consolidated.json --threshold 0.7 --match-fields "Фамилия:0.4:true:TOKEN_SORT,Имя:0.3:true:PARTIAL_RATIO,Отчество:0.2:true:RATIO,Email:0.1:false:RATIO" --verbose
```

2. Транслитерация данных между русским и английским языками:
```
python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/russian_data.json --format1 json --target-lang en --output-consolidated data/output/english_data.json --transliterate-fields "Фамилия,Имя,Отчество" --verbose
```

3. Генерация тестовых данных для отладки и тестирования:
```
python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input/original.json --output-variant data/input/variant.json --output-format json --record-count 100 --typo-probability 0.1 --character-probability 0.05 --generate-fields "id,Фамилия,Имя,Отчество,Email" --verbose
```

Описание основных параметров:
  --mode: режим работы (match, transliterate или generate)
  --input1, --input2: пути к входным файлам
  --format1, --format2: форматы входных файлов (csv или json)
  --output-matches: путь для сохранения найденных совпадений
  --output-consolidated: путь для сохранения консолидированных данных
  --threshold: порог схожести (от 0 до 1)
  --match-fields: конфигурация полей для сопоставления
  --target-lang: целевой язык для транслитерации (ru или en)
  --generate-fields: список полей для генерации в режиме generate
"""

import argparse
import sys
import os

from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig, 
    FuzzyAlgorithm
)
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.utils.cli_utils import generate_and_save_test_data

# Определение путей по умолчанию для файлов данных и результатов
DATA_INPUT_DIR = 'data/input'
DATA_OUTPUT_DIR = 'data/output'

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

def parse_name_fields(fields_str):
    """
    Парсит строку с соответствием полей в формате 'source1:target1,source2:target2'
    и возвращает словарь соответствий.
    """
    if not fields_str:
        return {
            'id': 'id',
            'Фамилия': 'Фамилия',
            'Имя': 'Имя',
            'Отчество': 'Отчество',
            'Email': 'Email',
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
        return [
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=False),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=False),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=False),
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
                print(f"Предупреждение: неизвестный алгоритм '{algorithm_name}' для поля '{field}'. "
                      f"Будет использован алгоритм по умолчанию.")
        
        match_fields.append(MatchFieldConfig(
            field=field,
            weight=weight,
            transliterate=transliterate,
            fuzzy_algorithm=algorithm
        ))
    
    return match_fields


def main():
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
    parser.add_argument('--transliteration-standard', choices=['ГОСТ 7.79-2000', 'Научная', 'Паспортная'], 
                      default='Паспортная',
                      help="Стандарт транслитерации (по умолчанию Паспортная)")
    
    # Параметры для вывода
    parser.add_argument('--output-matches',
                      help=f"Путь для сохранения результатов сопоставления (по умолчанию {os.path.join(DATA_OUTPUT_DIR, 'matches.json')})")
    parser.add_argument('--output-consolidated',
                      help=f"Путь для сохранения консолидированных данных (по умолчанию {os.path.join(DATA_OUTPUT_DIR, 'consolidated.json')})")
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
    parser.add_argument('--typo-probability', type=float, default=0.1,
                      help="Вероятность опечатки в поле (от 0 до 1, по умолчанию 0.1)")
    parser.add_argument('--character-probability', type=float, default=0.05,
                      help="Вероятность искажения символов в поле (от 0 до 1, по умолчанию 0.05)")
    parser.add_argument('--generate-fields',
                      help="Список полей для генерации, разделенных запятыми (по умолчанию: id,Фамилия,Имя,Отчество,Email,Телефон)")
    
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
- Email/телефоны: RATIO

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
                      default='TOKEN_SORT',
                      help="Основной алгоритм нечеткого сопоставления (для полей без явно указанного алгоритма)")
    
    args = parser.parse_args()

    # Режим генерации тестовых данных
    if args.mode == 'generate':
        if args.verbose:
            print(f"Генерация тестовых данных...")
        
        # Определяем вероятности искажений
        probabilities = {
            'typo': args.typo_probability,
            'swap': args.character_probability,
            'case': 0.2,  # Вероятность изменения регистра
            'extra_space': 0.1  # Вероятность добавления лишних пробелов
        }
        
        # Определяем поля для генерации
        default_fields = [
            {'name': 'id', 'type': 'id'},
            {'name': 'Фамилия', 'type': 'last_name'},
            {'name': 'Имя', 'type': 'first_name'},
            {'name': 'Отчество', 'type': 'middle_name'},
            {'name': 'Email', 'type': 'email'},
            {'name': 'Телефон', 'type': 'phone'},
            {'name': 'Пол', 'type': 'gender'}
        ]
        
        # Если указаны конкретные поля, фильтруем список полей
        gen_fields = default_fields
        if args.generate_fields:
            selected_fields = [field.strip() for field in args.generate_fields.split(',')]
            gen_fields = [field for field in default_fields if field['name'] in selected_fields]
            # Добавляем id, если его нет, так как он необходим для работы
            if not any(field['name'] == 'id' for field in gen_fields):
                gen_fields.insert(0, {'name': 'id', 'type': 'id'})
            
            if args.verbose:
                print(f"Генерация полей: {', '.join(field['name'] for field in gen_fields)}")
        
        # Используем пути по умолчанию, если пути не указаны
        output_original = args.output_original or os.path.join(DATA_INPUT_DIR, f'original.{args.output_format}')
        output_variant = args.output_variant or os.path.join(DATA_INPUT_DIR, f'variant.{args.output_format}')
        
        # Генерируем данные
        original_list, variant_list = generate_and_save_test_data(
            probabilities=probabilities,
            gen_fields=gen_fields,
            count=args.record_count,
            file_format=args.output_format,
            original_file=output_original,
            variant_file=output_variant
        )
        
        if args.verbose:
            print(f"Сгенерировано {len(original_list)} оригинальных и {len(variant_list)} искаженных записей")
            print(f"Оригинальные данные сохранены в {output_original}")
            print(f"Искаженные данные сохранены в {output_variant}")
        
        # Вывод 5 записей из каждого датасета
        print("\nПримеры оригинальных записей:")
        for i, record in enumerate(original_list[:5]):
            print(f"{i+1}. {record}")
            
        print("\nПримеры искаженных записей:")
        for i, record in enumerate(variant_list[:5]):
            print(f"{i+1}. {record}")
        
        return
    
    # Определяем соответствие полей
    name_fields = parse_name_fields(args.name_fields)
    
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
            print(f"Предупреждение: неизвестный алгоритм '{args.fuzzy_algorithm}'. "
                  f"Будет использован алгоритм TOKEN_SORT.")
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
            print(f"Ошибка: для режима {args.mode} необходимо указать входной файл (--input1)")
            sys.exit(1)
            
        if not args.format1:
            print(f"Ошибка: для режима {args.mode} необходимо указать формат входного файла (--format1)")
            sys.exit(1)
            
        if not os.path.exists(args.input1):
            print(f"Ошибка: файл {args.input1} не найден")
            sys.exit(1)
    
    if args.mode == 'match' and args.input2 and not os.path.exists(args.input2):
        print(f"Ошибка: файл {args.input2} не найден")
        sys.exit(1)
    
    # Загружаем первый набор данных
    try:
        if args.verbose:
            print(f"Загрузка данных из {args.input1}...")
        
        data1 = None
        if args.format1 == 'csv':
            data1 = matcher.load_from_csv(args.input1, name_fields)
        else:
            data1 = matcher.load_from_json(args.input1, name_fields)
        
        if args.verbose:
            print(f"Загружено {len(data1)} записей из {args.input1}")
    except Exception as e:
        print(f"Ошибка при загрузке данных из {args.input1}: {str(e)}")
        sys.exit(1)
    
    # Режим транслитерации
    if args.mode == 'transliterate':
        if not args.target_lang:
            print("Ошибка: для режима транслитерации необходимо указать целевой язык (--target-lang)")
            sys.exit(1)
        
        if args.verbose:
            print(f"Транслитерация данных из {args.input1} в {args.target_lang}...")
        
        # Определяем поля для транслитерации
        fields_to_transliterate = []
        if args.transliterate_fields:
            fields_to_transliterate = [f.strip() for f in args.transliterate_fields.split(',')]
        else:
            # По умолчанию транслитерируем все текстовые поля
            fields_to_transliterate = ['Фамилия', 'Имя', 'Отчество']
        
        # Транслитерируем данные
        transliterated_data = matcher.transliterate_data(
            data1, 
            target_lang=args.target_lang,
            fields=fields_to_transliterate
        )
        
        # Используем путь по умолчанию, если путь не указан
        output_consolidated = args.output_consolidated or os.path.join(DATA_OUTPUT_DIR, f'transliterated.{args.output_format}')
        
        # Сохраняем результаты
        if output_consolidated:
            if args.output_format == 'json':
                matcher.save_consolidated_to_json(transliterated_data, output_consolidated)
            else:
                matcher.save_consolidated_to_csv(transliterated_data, output_consolidated)
            
            if args.verbose:
                print(f"Результаты сохранены в {output_consolidated}")
        else:
            # Выводим результаты на экран
            print("\nРезультаты транслитерации:")
            for i, record in enumerate(transliterated_data[:10]):
                print(f"{i+1}. {record}")
            
            if len(transliterated_data) > 10:
                print(f"... и еще {len(transliterated_data) - 10} записей")
    
    # Режим сопоставления
    elif args.mode == 'match':
        if not args.input2:
            print("Ошибка: для режима сопоставления необходимо указать второй входной файл (--input2)")
            sys.exit(1)
        
        if not args.format2:
            print("Ошибка: для режима сопоставления необходимо указать формат второго файла (--format2)")
            sys.exit(1)
        
        # Загружаем второй набор данных
        try:
            if args.verbose:
                print(f"Загрузка данных из {args.input2}...")
            
            data2 = None
            if args.format2 == 'csv':
                data2 = matcher.load_from_csv(args.input2, name_fields)
            else:
                data2 = matcher.load_from_json(args.input2, name_fields)
            
            if args.verbose:
                print(f"Загружено {len(data2)} записей из {args.input2}")
        except Exception as e:
            print(f"Ошибка при загрузке данных из {args.input2}: {str(e)}")
            sys.exit(1)
        
        # Выполняем сопоставление
        if args.verbose:
            print(f"Сопоставление данных...")
        
        matches, consolidated = matcher.match_and_consolidate(data1, data2)
        
        if args.verbose:
            print(f"Найдено {len(matches)} совпадений")
            print(f"Консолидировано {len(consolidated)} записей")
        
        # Используем пути по умолчанию, если пути не указаны
        output_matches = args.output_matches or os.path.join(DATA_OUTPUT_DIR, f'matches.{args.output_format}')
        output_consolidated = args.output_consolidated or os.path.join(DATA_OUTPUT_DIR, f'consolidated.{args.output_format}')
        
        # Сохраняем результаты
        if output_matches:
            if args.output_format == 'json':
                matcher.save_matches_to_json(matches, output_matches)
            else:
                matcher.save_matches_to_csv(matches, output_matches)
            
            if args.verbose:
                print(f"Совпадения сохранены в {output_matches}")
        
        if output_consolidated:
            if args.output_format == 'json':
                matcher.save_consolidated_to_json(consolidated, output_consolidated)
            else:
                matcher.save_consolidated_to_csv(consolidated, output_consolidated)
            
            if args.verbose:
                print(f"Консолидированные данные сохранены в {output_consolidated}")
        
        if not output_matches and not output_consolidated:
            # Выводим результаты на экран
            print("\nНайденные совпадения:")
            for i, match in enumerate(matches[:5]):
                print(f"{i+1}. {match}")
            
            if len(matches) > 5:
                print(f"... и еще {len(matches) - 5} совпадений")


if __name__ == '__main__':
    main() 