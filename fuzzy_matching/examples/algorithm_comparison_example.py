"""
Пример сравнения различных алгоритмов нечеткого сопоставления.
Демонстрирует разницу в работе алгоритмов на конкретных примерах.
"""

from prettytable import PrettyTable
from rapidfuzz import fuzz

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig, FuzzyAlgorithm
from fuzzy_matching.utils.data_generator import DataGenerator, Language


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
    """Генерирует тестовые данные для демонстрации работы алгоритмов."""
    # Специальные примеры для демонстрации разницы в алгоритмах
    special_cases = [
        {
            'id': 's1',
            'Фамилия': 'Иванов',
            'Имя': 'Иван',
            'Отчество': 'Иванович',
            'email': 'ivanov@example.com'
        },
        {
            'id': 's2',
            'Фамилия': 'Чехов-Петров',
            'Имя': 'Антон',
            'Отчество': 'Павлович',
            'email': 'chekhov@example.com'
        },
        {
            'id': 's3',
            'Фамилия': 'Сидоров',
            'Имя': 'Петр',
            'Отчество': 'Сидорович',
            'email': 'sidorov@example.com'
        },
        {
            'id': 's4',
            'Фамилия': 'Smith',
            'Имя': 'John',
            'Отчество': 'Robert',
            'email': 'jsmith@example.com'
        },
        {
            'id': 's5',
            'Фамилия': 'Johnson',
            'Имя': 'James',
            'Отчество': 'William',
            'email': 'jjohnson@example.com'
        }
    ]
    
    # Варианты с различными типами ошибок для демонстрации разных алгоритмов
    variant_cases = [
        {
            'id': 'v1',
            'Фамилия': 'Иванов',
            'Имя': 'Иван',
            'Отчество': 'Ивановч',  # Пропущена буква (опечатка)
            'email': 'ivanov@example.com'
        },
        {
            'id': 'v2',
            'Фамилия': 'Петров-Чехов',  # Порядок слов изменен
            'Имя': 'Антон',
            'Отчество': 'Павлович',
            'email': 'chekhov@example.com'
        },
        {
            'id': 'v3',
            'Фамилия': 'Сидоров',
            'Имя': 'Сидорович',  # Имя и отчество перепутаны местами
            'Отчество': 'Петр',  # Алгоритм token_set должен лучше справляться
            'email': 'sidorov@example.com'
        },
        {
            'id': 'v4',
            'Фамилия': 'Smith',
            'Имя': 'Johnny',  # Уменьшительное имя
            'Отчество': 'Rob',  # Сокращение
            'email': 'johnsmith@example.com'  # Изменен email
        },
        {
            'id': 'v5',
            'Фамилия': 'Johnson',
            'Имя': 'Jim',      # Сокращенная форма имени
            'Отчество': 'Bill', # Сокращенная форма отчества
            'email': 'jim.johnson@example.com'  # Изменен формат email
        }
    ]
    
    return special_cases, variant_cases


def compare_algorithms(data1, data2):
    """
    Сравнивает работу различных алгоритмов нечеткого сопоставления.
    
    :param data1: первый набор данных
    :param data2: второй набор данных
    """
    algorithms = [
        FuzzyAlgorithm.RATIO,
        FuzzyAlgorithm.PARTIAL_RATIO,
        FuzzyAlgorithm.TOKEN_SORT,
        FuzzyAlgorithm.TOKEN_SET,
        FuzzyAlgorithm.WRatio
    ]
    
    # Для наглядности работы алгоритмов сравниваем две строки
    print("\n=== СРАВНЕНИЕ РАБОТЫ АЛГОРИТМОВ НА СТРОКАХ ===")
    string_examples = [
        ("Иванов Иван", "Иванов Иван"),              # Точное совпадение
        ("Иванов Иван", "Иванов Иван Иванович"),     # Частичное совпадение
        ("Петров-Чехов", "Чехов-Петров"),            # Перестановка токенов
        ("Иван Сидорович", "Сидорович Иван"),        # Перестановка слов
        ("John Smith", "Johnny Smith"),              # Уменьшительное имя
        ("The quick brown fox", "The brown fox was quick")  # Перемешанные слова
    ]
    
    for s1, s2 in string_examples:
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
    
    # Теперь применяем разные алгоритмы к нашим данным
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


def main():
    """
    Основная функция примера.
    """
    print("\n===== СРАВНЕНИЕ АЛГОРИТМОВ НЕЧЕТКОГО СОПОСТАВЛЕНИЯ =====\n")
    
    # Генерируем тестовые данные
    data1, data2 = generate_test_data()
    
    print("Исходные данные:")
    print("\nПервый набор данных:")
    print_table(data1)
    print("\nВторой набор данных:")
    print_table(data2)
    
    # Сравниваем алгоритмы
    compare_algorithms(data1, data2)
    
    print("\n===== ЗАВЕРШЕНИЕ СРАВНЕНИЯ АЛГОРИТМОВ =====\n")


if __name__ == "__main__":
    main() 