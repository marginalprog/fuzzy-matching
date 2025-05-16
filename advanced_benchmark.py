"""
Расширенное тестирование производительности матчинга с транслитерацией.
Включает тесты с различными конфигурациями и большими объемами данных.
"""

import time
import cProfile
import pstats
import io
import pandas as pd
import pickle
import os
from prettytable import PrettyTable

from data_generator import DataGenerator, Language
from data_matcher import DataMatcher
from match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
import transliteration_utils as translit


def generate_test_data(sizes):
    """
    Генерирует тестовые данные разных размеров и сохраняет их для повторного использования.
    
    :param sizes: список размеров данных для генерации
    :return: словарь с сгенерированными данными по размерам
    """
    data_cache_file = "benchmark_data_cache.pkl"
    
    # Проверяем, есть ли кэш данных
    if os.path.exists(data_cache_file):
        print("Загрузка данных из кэша...")
        with open(data_cache_file, 'rb') as f:
            data_cache = pickle.load(f)
            
        # Проверяем, все ли размеры есть в кэше
        missing_sizes = [size for size in sizes if size not in data_cache]
        if not missing_sizes:
            return data_cache
        
        # Если есть отсутствующие размеры, генерируем только их
        print(f"Генерация недостающих данных размеров: {missing_sizes}")
        sizes = missing_sizes
    else:
        data_cache = {}
    
    # Настройки генератора данных
    probabilities = {
        'double_letter': 0.2,
        'change_letter': 0.2,
        'change_name': 0.1,
        'change_name_domain': 0.2,
        'double_number': 0.2,
        'suffix_addition': 0.2
    }
    
    # Поля для генерации
    fields = ['Фамилия', 'Имя', 'Отчество', 'email']
    
    # Генерируем данные для каждого размера
    for size in sizes:
        print(f"Генерация данных размером {size} записей...")
        
        # Генерируем русские и английские данные
        ru_gen = DataGenerator(language=Language.RUS, probabilities=probabilities)
        en_gen = DataGenerator(language=Language.ENG, probabilities=probabilities)
        
        # Разделяем размер поровну между русскими и английскими данными
        ru_size = size // 2
        en_size = size - ru_size
        
        # Генерируем чистые данные
        ru_data = ru_gen.generate_clean_clients_list(ru_size, fields)
        en_data = en_gen.generate_clean_clients_list(en_size, fields)
        
        # Создаем искаженные данные для имитации реальных сценариев
        ru_data_distorted = ru_gen.apply_distortions(ru_data, fields)
        en_data_distorted = en_gen.apply_distortions(en_data, fields)
        
        # Добавляем транслитерированные варианты русских имен
        ru_data_transliterated = []
        for client in ru_data[:ru_size//3]:  # Берем треть русских данных
            en_client = client.copy()
            en_client['id'] = f"{client['id']}_translit"
            
            # Транслитерируем русские имена
            en_client['Фамилия'] = translit.transliterate_ru_to_en(client['Фамилия'])
            en_client['Имя'] = translit.transliterate_ru_to_en(client['Имя'])
            en_client['Отчество'] = translit.transliterate_ru_to_en(client['Отчество'])
            
            ru_data_transliterated.append(en_client)
        
        # Сохраняем сгенерированные данные
        data_cache[size] = {
            'ru_data': ru_data,
            'en_data': en_data,
            'ru_data_distorted': ru_data_distorted,
            'en_data_distorted': en_data_distorted,
            'ru_data_transliterated': ru_data_transliterated
        }
    
    # Сохраняем данные в кэш
    with open(data_cache_file, 'wb') as f:
        pickle.dump(data_cache, f)
    
    return data_cache


def create_test_configs():
    """
    Создает различные конфигурации для тестирования.
    
    :return: список конфигураций для тестирования
    """
    configs = []
    
    # Базовая конфигурация без транслитерации
    base_config = {
        'name': 'Базовая без транслитерации',
        'transliteration_enabled': False,
        'fields_transliterate': [False, False, False, False],
        'block_field': 'Фамилия',
        'sort_before_match': True,
        'threshold': 0.7
    }
    configs.append(base_config)
    
    # Конфигурация с транслитерацией всех полей
    full_translit_config = base_config.copy()
    full_translit_config.update({
        'name': 'Полная транслитерация',
        'transliteration_enabled': True,
        'fields_transliterate': [True, True, True, False],
    })
    configs.append(full_translit_config)
    
    # Конфигурация с транслитерацией только имени и фамилии
    partial_translit_config = base_config.copy()
    partial_translit_config.update({
        'name': 'Частичная транслитерация (имя, фамилия)',
        'transliteration_enabled': True,
        'fields_transliterate': [True, True, False, False],
    })
    configs.append(partial_translit_config)
    
    # Конфигурация с транслитерацией и без блокировки
    no_blocking_translit_config = full_translit_config.copy()
    no_blocking_translit_config.update({
        'name': 'Транслитерация без блокировки',
        'block_field': None,
    })
    configs.append(no_blocking_translit_config)
    
    # Конфигурация с высоким порогом схожести
    high_threshold_config = full_translit_config.copy()
    high_threshold_config.update({
        'name': 'Транслитерация с высоким порогом (0.9)',
        'threshold': 0.9
    })
    configs.append(high_threshold_config)
    
    return configs


def build_match_config(config_dict):
    """
    Создает объект MatchConfig на основе словаря с параметрами.
    
    :param config_dict: словарь с параметрами конфигурации
    :return: объект MatchConfig
    """
    # Создаем конфигурацию транслитерации
    transliteration_config = TransliterationConfig(
        enabled=config_dict['transliteration_enabled'],
        standard="Паспортная транслитерация",
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    # Создаем конфигурацию полей
    field_names = ['Фамилия', 'Имя', 'Отчество', 'email']
    field_weights = [0.4, 0.3, 0.2, 0.1]
    fields = []
    
    for i, field in enumerate(field_names):
        fields.append(MatchFieldConfig(
            field=field,
            weight=field_weights[i],
            transliterate=config_dict['fields_transliterate'][i]
        ))
    
    # Создаем основную конфигурацию
    match_config = MatchConfig(
        fields=fields,
        length_weight=0.01,
        threshold=config_dict['threshold'],
        block_field=config_dict['block_field'],
        sort_before_match=config_dict['sort_before_match'],
        transliteration=transliteration_config
    )
    
    return match_config


def run_test(test_data, config_dict, data_size):
    """
    Запускает тест производительности с заданной конфигурацией.
    
    :param test_data: словарь с тестовыми данными
    :param config_dict: словарь с параметрами конфигурации
    :param data_size: размер данных для тестирования
    :return: результаты теста
    """
    # Получаем данные для теста
    data = test_data[data_size]
    
    # Собираем все данные для первого списка (оригинальные русские + искаженные английские)
    list1 = data['ru_data'] + data['en_data_distorted']
    
    # Собираем все данные для второго списка (искаженные русские + оригинальные английские + транслитерированные русские)
    list2 = data['ru_data_distorted'] + data['en_data'] + data['ru_data_transliterated']
    
    # Создаем конфигурацию для теста
    match_config = build_match_config(config_dict)
    
    # Создаем профилировщик
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Запускаем сопоставление и замеряем время
    start_time = time.time()
    
    # Создаем matcher и запускаем сопоставление
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(list1, list2)
    
    duration = time.time() - start_time
    
    profiler.disable()
    
    # Получаем статистику профилирования
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    
    return {
        'config_name': config_dict['name'],
        'duration': duration,
        'matches_count': len(matches),
        'consolidated_count': len(consolidated),
        'profile_stats': s.getvalue()
    }


def print_test_results(results):
    """
    Выводит результаты тестов в виде таблицы.
    
    :param results: список результатов тестов
    """
    table = PrettyTable()
    table.title = "Результаты расширенного тестирования производительности"
    table.field_names = ["Размер данных", "Конфигурация", "Время (сек)", "Совпадений", "Консолидированных", "Скорость (записей/сек)"]
    
    for size in sorted(results.keys()):
        for result in results[size]:
            # Вычисляем скорость обработки записей
            speed = size / result['duration'] if result['duration'] > 0 else 0
            
            table.add_row([
                size,
                result['config_name'],
                f"{result['duration']:.4f}",
                result['matches_count'],
                result['consolidated_count'],
                f"{speed:.2f}"
            ])
    
    print(table)


def analyze_performance_factors(results):
    """
    Анализирует факторы, влияющие на производительность.
    
    :param results: словарь с результатами тестов
    """
    print("\n=== АНАЛИЗ ФАКТОРОВ ПРОИЗВОДИТЕЛЬНОСТИ ===\n")
    
    # Анализ влияния транслитерации на время выполнения
    for size in sorted(results.keys()):
        base_time = None
        translit_time = None
        
        for result in results[size]:
            if result['config_name'] == 'Базовая без транслитерации':
                base_time = result['duration']
            elif result['config_name'] == 'Полная транслитерация':
                translit_time = result['duration']
        
        if base_time is not None and translit_time is not None:
            overhead = (translit_time - base_time) / base_time * 100
            print(f"Размер данных: {size}")
            print(f"  - Без транслитерации: {base_time:.4f} сек")
            print(f"  - С транслитерацией: {translit_time:.4f} сек")
            print(f"  - Накладные расходы: {overhead:.2f}%")
    
    # Анализ влияния блокировки на производительность с транслитерацией
    print("\nВлияние блокировки на производительность с транслитерацией:")
    for size in sorted(results.keys()):
        with_blocking = None
        without_blocking = None
        
        for result in results[size]:
            if result['config_name'] == 'Полная транслитерация':
                with_blocking = result['duration']
            elif result['config_name'] == 'Транслитерация без блокировки':
                without_blocking = result['duration']
        
        if with_blocking is not None and without_blocking is not None:
            blocking_impact = (without_blocking - with_blocking) / with_blocking * 100
            print(f"Размер данных: {size}")
            print(f"  - С блокировкой: {with_blocking:.4f} сек")
            print(f"  - Без блокировки: {without_blocking:.4f} сек")
            print(f"  - Различие: {blocking_impact:.2f}%")
    
    # Анализ масштабируемости (как время растет с увеличением размера данных)
    print("\nМасштабируемость:")
    sizes = sorted(results.keys())
    if len(sizes) >= 2:
        for config_name in ['Базовая без транслитерации', 'Полная транслитерация']:
            times = []
            for size in sizes:
                for result in results[size]:
                    if result['config_name'] == config_name:
                        times.append(result['duration'])
            
            if len(times) >= 2:
                # Вычисляем коэффициент масштабирования (во сколько раз увеличивается время при 10-кратном увеличении объема данных)
                scaling_ratio = times[-1] / times[0]
                data_size_ratio = sizes[-1] / sizes[0]
                scaling_factor = scaling_ratio / data_size_ratio
                
                print(f"Конфигурация: {config_name}")
                print(f"  - Время для {sizes[0]} записей: {times[0]:.4f} сек")
                print(f"  - Время для {sizes[-1]} записей: {times[-1]:.4f} сек")
                print(f"  - Коэффициент масштабирования: {scaling_factor:.2f}x")
                
                if scaling_factor > 1:
                    print(f"  - Сложность хуже линейной (приблизительно O(n^{scaling_factor:.1f}))")
                else:
                    print(f"  - Сложность линейная или лучше")


def save_results_to_csv(results, filename="benchmark_results.csv"):
    """
    Сохраняет результаты тестов в CSV-файл.
    
    :param results: словарь с результатами тестов
    :param filename: имя файла для сохранения
    """
    # Подготавливаем данные для DataFrame
    data = []
    
    for size in sorted(results.keys()):
        for result in results[size]:
            speed = size / result['duration'] if result['duration'] > 0 else 0
            
            data.append({
                'Размер данных': size,
                'Конфигурация': result['config_name'],
                'Время (сек)': round(result['duration'], 4),
                'Совпадений': result['matches_count'],
                'Консолидированных': result['consolidated_count'],
                'Скорость (записей/сек)': round(speed, 2)
            })
    
    # Создаем DataFrame и сохраняем в CSV
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"\nРезультаты сохранены в файл {filename}")


def main():
    """
    Основная функция для запуска расширенного тестирования.
    """
    print("\n===== РАСШИРЕННОЕ ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ МАТЧИНГА =====\n")
    
    # Размеры данных для тестирования
    data_sizes = [100, 1000]
    
    # Генерируем тестовые данные
    test_data = generate_test_data(data_sizes)
    
    # Создаем конфигурации для тестирования
    configs = create_test_configs()
    
    # Запускаем тесты
    results = {}
    
    for size in data_sizes:
        print(f"\nЗапуск тестов для размера данных {size}...")
        results[size] = []
        
        for config in configs:
            print(f"  - Конфигурация: {config['name']}")
            result = run_test(test_data, config, size)
            results[size].append(result)
    
    # Выводим результаты
    print("\n=== РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ===\n")
    print_test_results(results)
    
    # Анализируем факторы производительности
    analyze_performance_factors(results)
    
    # Сохраняем результаты в CSV
    try:
        save_results_to_csv(results)
    except Exception as e:
        print(f"\nОшибка при сохранении результатов: {e}")
    
    # Выводим детальную информацию о профилировании для последнего теста
    print("\n=== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ПРОФИЛИРОВАНИИ (для размера 1000) ===\n")
    
    for result in results[1000]:
        print(f"\nКонфигурация: {result['config_name']}")
        print(result['profile_stats'])
    
    print("\n===== ЗАВЕРШЕНИЕ РАСШИРЕННОГО ТЕСТИРОВАНИЯ =====\n")


if __name__ == "__main__":
    main() 