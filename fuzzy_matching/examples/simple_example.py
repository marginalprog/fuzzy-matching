"""
Простой пример использования библиотеки fuzzy_matching.

Этот скрипт показывает базовое использование функций нечеткого сопоставления 
с поддержкой транслитерации.
"""

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.utils.data_generator import DataGenerator, Language
from prettytable import PrettyTable


def print_table(data):
    """Выводит данные в виде форматированной таблицы"""
    if not data:
        print("Нет данных для отображения")
        return

    table = PrettyTable()
    table.field_names = data[0].keys()
    for row in data:
        table.add_row(row.values())

    table.align = 'l'
    print(table)


def generate_test_data():
    """Генерирует тестовые данные для демонстрации."""
    # Настройки генератора данных
    probabilities = {
        'double_letter': 0.2,
        'change_letter': 0.2,
        'change_name': 0.1,
        'change_name_domain': 0.2,
        'double_number': 0.2,
        'suffix_addition': 0.2
    }
    
    # Генерируем данные
    generator = DataGenerator(language=Language.RUS, probabilities=probabilities)
    fields = ['Фамилия', 'Имя', 'Отчество', 'email']
    original_data, variant_data = generator.generate_clients_pair(10, fields)
    
    return original_data, variant_data


def demo_basic_matching():
    """Демонстрирует базовое сопоставление данных без транслитерации."""
    print("\n===== ПРОСТОЕ СОПОСТАВЛЕНИЕ БЕЗ ТРАНСЛИТЕРАЦИИ =====\n")
    
    # Генерируем тестовые данные
    original_data, variant_data = generate_test_data()
    
    print("Исходные данные:")
    print_table(original_data[:3])
    
    print("\nВариантные данные:")
    print_table(variant_data[:3])
    
    # Настройка конфигурации сопоставления
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4),
            MatchFieldConfig(field='Имя', weight=0.3),
            MatchFieldConfig(field='Отчество', weight=0.2),
            MatchFieldConfig(field='email', weight=0.1)
        ],
        length_weight=0.01,
        threshold=0.7,
        block_field='Фамилия',
        sort_before_match=True
    )
    
    # Выполняем сопоставление
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(original_data, variant_data)
    
    # Выводим результаты
    print("\nРезультаты сопоставления:")
    
    # Создаем таблицу совпадений
    if matches:
        table = PrettyTable()
        table.field_names = ["Запись 1", "Запись 2", "Совпадение"]
        
        for match in matches:
            rec1 = " ".join(match["Запись 1"])
            rec2 = " ".join(match["Запись 2"])
            score = f"{match['Совпадение'][0]:.2f}"
            table.add_row([rec1, rec2, score])
        
        table.align["Запись 1"] = "l"
        table.align["Запись 2"] = "l"
        table.align["Совпадение"] = "r"
        
        print(f"\nНайдено совпадений: {len(matches)}")
        print(table)
    else:
        print("Совпадений не найдено")
        
    print(f"\nКонсолидировано записей: {len(consolidated)}")


def demo_transliteration_matching():
    """Демонстрирует сопоставление данных с транслитерацией."""
    print("\n===== СОПОСТАВЛЕНИЕ С ТРАНСЛИТЕРАЦИЕЙ =====\n")
    
    # Создаем тестовые данные на разных языках
    russian_data = [
        {
            'id': 'ru_1',
            'Фамилия': 'Иванов',
            'Имя': 'Александр',
            'Отчество': 'Сергеевич',
            'email': 'ivanov@example.ru'
        },
        {
            'id': 'ru_2',
            'Фамилия': 'Петров',
            'Имя': 'Михаил',
            'Отчество': 'Иванович',
            'email': 'petrov@example.ru'
        }
    ]
    
    # Создадим более правильные английские варианты имен с учетом культурных особенностей
    english_data = [
        {
            'id': 'en_1',
            'Фамилия': 'Ivanov',
            'Имя': 'Alexander',  # Английский вариант имени
            'Отчество': 'Sergeevich',  # Транслитерированное отчество
            'email': 'ivanov@example.com'
        },
        {
            'id': 'en_2',
            'Фамилия': 'Petrov',
            'Имя': 'Michael',  # Английский эквивалент имени
            'Отчество': 'Ivanovich',  # Транслитерированное отчество
            'email': 'petrov@example.com'
        }
    ]
    
    print("Данные на русском:")
    print_table(russian_data)
    
    print("\nДанные на английском:")
    print_table(english_data)
    
    # Настройка конфигурации с транслитерацией
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Паспортная транслитерация",
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=True),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=True),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=True),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False)
        ],
        length_weight=0.01,
        threshold=0.7,
        block_field=None,  # Без блокировки для простоты демонстрации
        sort_before_match=False,
        transliteration=transliteration_config
    )
    
    # Выполняем сопоставление
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(russian_data, english_data)
    
    # Выводим результаты
    print("\nРезультаты сопоставления с транслитерацией:")
    
    # Создаем таблицу совпадений
    if matches:
        table = PrettyTable()
        table.field_names = ["Запись 1", "Запись 2", "Совпадение"]
        
        for match in matches:
            rec1 = " ".join(match["Запись 1"])
            rec2 = " ".join(match["Запись 2"])
            score = f"{match['Совпадение'][0]:.2f}"
            table.add_row([rec1, rec2, score])
        
        table.align["Запись 1"] = "l"
        table.align["Запись 2"] = "l"
        table.align["Совпадение"] = "r"
        
        print(f"\nНайдено совпадений: {len(matches)}")
        print(table)
    else:
        print("Совпадений не найдено")
        
    print(f"\nКонсолидировано записей: {len(consolidated)}")


def main():
    print("===== ДЕМОНСТРАЦИЯ РАБОТЫ БИБЛИОТЕКИ FUZZY MATCHING =====\n")
    
    # Демонстрация базового сопоставления
    demo_basic_matching()
    
    # Демонстрация сопоставления с транслитерацией
    demo_transliteration_matching()
    
    print("\n===== ЗАВЕРШЕНИЕ ДЕМОНСТРАЦИИ =====")


if __name__ == "__main__":
    main()
