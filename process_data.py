#!/usr/bin/env python
"""
Скрипт для сопоставления или транслитерации данных из CSV/JSON файлов.

Примеры использования:

1. Сопоставление данных из CSV файлов:
   python process_data.py --mode match \
       --input1 dataset1.csv --format1 csv \
       --input2 dataset2.csv --format2 csv \
       --output-matches matches.json \
       --output-consolidated consolidated.json \
       --threshold 0.8 \
       --block-field Фамилия \
       --domain person

2. Транслитерация данных из JSON файла:
   python process_data.py --mode transliterate \
       --input1 russian_names.json --format1 json \
       --target-lang en \
       --output-consolidated english_names.json
"""

import argparse
import sys
import os

from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig, 
    FuzzyAlgorithm, DomainSpecificAlgorithm
)
from fuzzy_matching.core.data_matcher import DataMatcher


def parse_name_fields(fields_str):
    """
    Парсит строку с соответствием полей в формате 'source1:target1,source2:target2'
    и возвращает словарь соответствий.
    """
    if not fields_str:
        return {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'email': 'email',
            'phone': 'Телефон'
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
    'field1:weight1:transliterate1,field2:weight2:transliterate2'
    и возвращает список объектов MatchFieldConfig.
    """
    if not fields_str:
        return [
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False)
        ]
    
    match_fields = []
    pairs = fields_str.split(',')
    for pair in pairs:
        parts = pair.split(':')
        field = parts[0].strip()
        weight = float(parts[1]) if len(parts) > 1 else 1.0
        transliterate = parts[2].lower() == 'true' if len(parts) > 2 else False
        
        match_fields.append(MatchFieldConfig(
            field=field,
            weight=weight,
            transliterate=transliterate
        ))
    
    return match_fields


def main():
    parser = argparse.ArgumentParser(description="Сопоставление или транслитерация данных из файлов")
    
    # Общие параметры
    parser.add_argument('--mode', choices=['match', 'transliterate'], required=True,
                      help="Режим работы: match (сопоставление) или transliterate (транслитерация)")
    parser.add_argument('--input1', required=True,
                      help="Путь к первому входному файлу (CSV или JSON)")
    parser.add_argument('--format1', choices=['csv', 'json'], required=True,
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
                      help="Путь для сохранения результатов сопоставления")
    parser.add_argument('--output-consolidated',
                      help="Путь для сохранения консолидированных данных")
    parser.add_argument('--output-format', choices=['csv', 'json'], default='json',
                      help="Формат выходных файлов (по умолчанию json)")
    parser.add_argument('--verbose', action='store_true',
                      help="Подробный вывод информации о процессе")
    
    # Параметры конфигурации
    parser.add_argument('--threshold', type=float, default=0.7,
                      help="Порог схожести для сопоставления (от 0 до 1)")
    parser.add_argument('--block-field',
                      help="Поле для блокировки (ускоряет сопоставление)")
    parser.add_argument('--domain', choices=['person', 'product', 'company', 'transliteration'],
                      help="Предметная область для выбора алгоритмов")
    parser.add_argument('--name-fields',
                      help="Соответствие полей в формате 'source1:target1,source2:target2'")
    parser.add_argument('--match-fields',
                      help="Конфигурация полей для сопоставления в формате 'field1:weight1:transliterate1,field2:weight2:transliterate2'")
    parser.add_argument('--transliterate-fields',
                      help="Поля для транслитерации, разделенные запятыми")
    
    args = parser.parse_args()
    
    # Определяем соответствие полей
    name_fields = parse_name_fields(args.name_fields)
    
    # Создаем конфигурацию полей для сопоставления
    match_fields = parse_match_fields(args.match_fields)
    
    # Настраиваем транслитерацию, если она нужна
    transliteration_config = TransliterationConfig(
        enabled=(args.mode == 'transliterate' or args.domain == 'transliteration'),
        standard=args.transliteration_standard,
        threshold=args.threshold,
        auto_detect=True,
        normalize_names=True
    )
    
    # Выбираем предметную область, если указана
    domain_algorithm = None
    if args.domain == 'person':
        domain_algorithm = DomainSpecificAlgorithm.PERSON_DATA
    elif args.domain == 'product':
        domain_algorithm = DomainSpecificAlgorithm.PRODUCT_DATA
    elif args.domain == 'company':
        domain_algorithm = DomainSpecificAlgorithm.COMPANY_DATA
    elif args.domain == 'transliteration':
        domain_algorithm = DomainSpecificAlgorithm.TRANSLITERATION
    
    # Создаем конфигурацию
    config = MatchConfig(
        fields=match_fields,
        threshold=args.threshold,
        block_field=args.block_field,
        transliteration=transliteration_config,
        domain_algorithm=domain_algorithm
    )
    
    # Создаем экземпляр DataMatcher
    matcher = DataMatcher(config=config)
    
    # Проверяем существование входных файлов
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
            print("Ошибка: для транслитерации необходимо указать целевой язык (--target-lang)")
            sys.exit(1)
        
        # Определяем поля для транслитерации
        transliterate_fields = ['Фамилия', 'Имя', 'Отчество']
        if args.transliterate_fields:
            transliterate_fields = [field.strip() for field in args.transliterate_fields.split(',')]
        
        try:
            if args.verbose:
                print(f"Транслитерация данных с {args.target_lang == 'ru' and 'английского на русский' or 'русского на английский'}...")
            
            # Транслитерируем данные
            transliterated_data = matcher.translate_data(
                data1,
                target_lang=args.target_lang,
                fields=transliterate_fields
            )
            
            # Сохраняем результаты
            output_file = args.output_consolidated or f"transliterated_{args.target_lang}.{args.output_format}"
            if args.output_format == 'csv':
                matcher.save_consolidated_to_csv(transliterated_data, output_file)
            else:
                matcher.save_consolidated_to_json(transliterated_data, output_file)
            
            print(f"Транслитерированные данные сохранены в {output_file}")
        except Exception as e:
            print(f"Ошибка при транслитерации данных: {str(e)}")
            sys.exit(1)
    
    # Режим сопоставления
    else:
        if not args.input2:
            print("Ошибка: для сопоставления необходимо указать второй входной файл (--input2)")
            sys.exit(1)
        
        if not args.format2:
            print("Ошибка: для сопоставления необходимо указать формат второго входного файла (--format2)")
            sys.exit(1)
        
        try:
            if args.verbose:
                print(f"Загрузка данных из {args.input2}...")
            
            # Загружаем второй набор данных
            data2 = None
            if args.format2 == 'csv':
                data2 = matcher.load_from_csv(args.input2, name_fields)
            else:
                data2 = matcher.load_from_json(args.input2, name_fields)
            
            if args.verbose:
                print(f"Загружено {len(data2)} записей из {args.input2}")
                print("Выполнение сопоставления...")
            
            # Выполняем сопоставление
            matches, consolidated = matcher.match_and_consolidate(data1, data2)
            
            if args.verbose:
                print(f"Найдено {len(matches)} совпадений")
                print(f"Создано {len(consolidated)} консолидированных записей")
            
            # Сохраняем результаты сопоставления
            if args.output_matches:
                if args.output_format == 'csv':
                    matcher.save_matches_to_csv(matches, args.output_matches)
                else:
                    matcher.save_matches_to_json(matches, args.output_matches)
                print(f"Результаты сопоставления сохранены в {args.output_matches}")
            
            # Сохраняем консолидированные данные
            if args.output_consolidated:
                if args.output_format == 'csv':
                    matcher.save_consolidated_to_csv(consolidated, args.output_consolidated)
                else:
                    matcher.save_consolidated_to_json(consolidated, args.output_consolidated)
                print(f"Консолидированные данные сохранены в {args.output_consolidated}")
            
            print(f"Найдено {len(matches)} совпадений")
            print(f"Создано {len(consolidated)} консолидированных записей")
        except Exception as e:
            print(f"Ошибка при сопоставлении данных: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main() 