"""
Простой пример использования библиотеки fuzzy_matching.

Этот скрипт показывает базовое использование функций нечеткого сопоставления 
с поддержкой транслитерации.
"""

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.utils.data_generator import DataGenerator, Language
from fuzzy_matching.examples.utils import print_table, print_matches, save_example_results
from fuzzy_matching.examples.data_examples import PERSONAL_DATA_RU, PERSONAL_DATA_EN


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
    original_data, variant_data = generator.generate_records_pair(10, fields)
    
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
    print_matches(matches)
    
    print(f"\nКонсолидировано записей: {len(consolidated)}")
    
    # Сохраняем результаты
    save_example_results(matches, consolidated, prefix="simple_basic", results_dir="results")


def demo_transliteration_matching():
    """Демонстрирует сопоставление данных с транслитерацией."""
    print("\n===== СОПОСТАВЛЕНИЕ С ТРАНСЛИТЕРАЦИЕЙ =====\n")
    
    # Используем предопределенные данные
    russian_data = PERSONAL_DATA_RU
    english_data = PERSONAL_DATA_EN
    
    print("Данные на русском:")
    print_table(russian_data)
    
    print("\nДанные на английском:")
    print_table(english_data)
    
    # Настройка конфигурации с транслитерацией
    transliteration_config = TransliterationConfig(
        enabled=True,
        standard="Паспортная",
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
    print_matches(matches)
    
    print(f"\nКонсолидировано записей: {len(consolidated)}")
    
    # Сохраняем результаты
    save_example_results(matches, consolidated, prefix="simple_translit", results_dir="results")


def main():
    print("===== ДЕМОНСТРАЦИЯ РАБОТЫ БИБЛИОТЕКИ FUZZY MATCHING =====\n")
    
    # Демонстрация базового сопоставления
    demo_basic_matching()
    
    # Демонстрация сопоставления с транслитерацией
    demo_transliteration_matching()
    
    print("\n===== ЗАВЕРШЕНИЕ ДЕМОНСТРАЦИИ =====")


if __name__ == "__main__":
    main()
