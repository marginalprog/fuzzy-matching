"""
Пример сравнения различных алгоритмов нечеткого сопоставления.
Демонстрирует разницу в работе алгоритмов на конкретных примерах.
"""

from rapidfuzz import fuzz

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, FuzzyAlgorithm
from fuzzy_matching.examples.utils import print_table, print_matches, save_example_results
from fuzzy_matching.examples.data_examples import (
    ALGORITHM_EXAMPLES, ALGORITHM_VARIANTS, STRING_COMPARISON_EXAMPLES
)


def compare_algorithms_on_strings():
    """
    Сравнивает работу различных алгоритмов нечеткого сопоставления на строках.
    """
    algorithms = [
        FuzzyAlgorithm.RATIO,
        FuzzyAlgorithm.PARTIAL_RATIO,
        FuzzyAlgorithm.TOKEN_SORT,
        FuzzyAlgorithm.TOKEN_SET,
        FuzzyAlgorithm.WRatio
    ]
    
    print("\n=== СРАВНЕНИЕ РАБОТЫ АЛГОРИТМОВ НА СТРОКАХ ===")
    
    for s1, s2 in STRING_COMPARISON_EXAMPLES:
        print(f"\nПример: '{s1}' и '{s2}'")
        results = []
        for algo in algorithms:
            if algo == FuzzyAlgorithm.RATIO:
                score = fuzz.ratio(s1, s2)
            elif algo == FuzzyAlgorithm.PARTIAL_RATIO:
                score = fuzz.partial_ratio(s1, s2)
            elif algo == FuzzyAlgorithm.TOKEN_SORT:
                score = fuzz.token_sort_ratio(s1, s2)
            elif algo == FuzzyAlgorithm.TOKEN_SET:
                score = fuzz.token_set_ratio(s1, s2)
            elif algo == FuzzyAlgorithm.WRatio:
                score = fuzz.WRatio(s1, s2)
            else:
                score = 0
            
            results.append({
                'Алгоритм': algo.name,
                'Схожесть': f"{score:.1f}%"
            })
        
        # Выводим результаты
        print_table(results)


def compare_algorithms_on_records():
    """
    Сравнивает работу различных алгоритмов нечеткого сопоставления на записях.
    """
    algorithms = [
        FuzzyAlgorithm.RATIO,
        FuzzyAlgorithm.PARTIAL_RATIO,
        FuzzyAlgorithm.TOKEN_SORT,
        FuzzyAlgorithm.TOKEN_SET,
        FuzzyAlgorithm.WRatio
    ]
    
    # Получаем тестовые данные
    data1 = ALGORITHM_EXAMPLES
    data2 = ALGORITHM_VARIANTS
    
    print("\n=== СРАВНЕНИЕ РАБОТЫ АЛГОРИТМОВ НА ЗАПИСЯХ ===")
    
    # Базовая конфигурация
    field_configs = [
        MatchFieldConfig(field='Фамилия', weight=0.4),
        MatchFieldConfig(field='Имя', weight=0.3),
        MatchFieldConfig(field='Отчество', weight=0.2),
        MatchFieldConfig(field='email', weight=0.1)
    ]
    
    all_matches = {}
    
    for algorithm in algorithms:
        # Создаем конфигурацию с текущим алгоритмом
        match_config = MatchConfig(
            fields=field_configs,
            threshold=0.5,  # Устанавливаем низкий порог для демонстрации
            block_field=None,  # Отключаем блокировку для полного сравнения
            fuzzy_algorithm=algorithm
        )
        
        # Создаем матчер и запускаем сопоставление
        matcher = DataMatcher(config=match_config)
        matches, _ = matcher.match_and_consolidate(data1, data2)
        
        # Сохраняем результаты
        all_matches[algorithm.name] = matches
        
        print(f"\nАлгоритм: {algorithm.name}")
        print(f"Найдено совпадений: {len(matches)}")
        
        for match in matches:
            print(f"\nID: {match['ID 1']} - {match['ID 2']}")
            print(f"Запись 1: {' '.join(match['Запись 1'])}")
            print(f"Запись 2: {' '.join(match['Запись 2'])}")
            print(f"Схожесть: {match['Совпадение'][0]:.2f}")
            print("-" * 50)
    
    # Сравнительная таблица результатов
    comparison = []
    for i, record1 in enumerate(data1):
        row = {'ID': record1['id'], 'ФИО': f"{record1['Фамилия']} {record1['Имя']} {record1['Отчество']}"}
        
        for algo_name in [algo.name for algo in algorithms]:
            # Находим соответствующее совпадение для этой записи
            match = next((m for m in all_matches[algo_name] if m['ID 1'] == record1['id']), None)
            row[algo_name] = f"{match['Совпадение'][0]:.2f}" if match else "-"
        
        comparison.append(row)
    
    print("\n=== СРАВНИТЕЛЬНАЯ ТАБЛИЦА РАБОТЫ АЛГОРИТМОВ ===")
    print_table(comparison)
    
    # Сохраняем результаты
    for algo_name, matches in all_matches.items():
        if matches:
            save_example_results(matches, [], prefix=f"algo_{algo_name.lower()}", results_dir="results")


def main():
    """
    Основная функция примера.
    """
    print("\n===== СРАВНЕНИЕ АЛГОРИТМОВ НЕЧЕТКОГО СОПОСТАВЛЕНИЯ =====\n")
    
    # Получаем тестовые данные
    data1 = ALGORITHM_EXAMPLES
    data2 = ALGORITHM_VARIANTS
    
    print("Исходные данные:")
    print("\nПервый набор данных:")
    print_table(data1)
    print("\nВторой набор данных:")
    print_table(data2)
    
    # Сравниваем алгоритмы на строках
    compare_algorithms_on_strings()
    
    # Сравниваем алгоритмы на записях
    compare_algorithms_on_records()
    
    print("\n===== ЗАВЕРШЕНИЕ СРАВНЕНИЯ АЛГОРИТМОВ =====\n")


if __name__ == "__main__":
    main() 