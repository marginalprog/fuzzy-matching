"""
Тест производительности для сравнения матчинга с транслитерацией и без неё
на разных объёмах данных.
"""

import time
import cProfile
import pstats
import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from prettytable import PrettyTable

from fuzzy_matching.utils.data_generator import DataGenerator, Language
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig


def generate_mixed_language_data(count, ru_to_en_ratio=0.5):
    """
    Генерирует смешанный набор данных на русском и английском языках.
    
    :param count: общее количество записей
    :param ru_to_en_ratio: отношение русских записей к английским (0-1)
    :return: кортеж (русские_данные, английские_данные)
    """
    # Настройки генератора данных
    probabilities = {
        'double_letter': 0.2,      # вероятность дублирования буквы
        'change_letter': 0.2,      # вероятность замены буквы
        'change_name': 0.1,        # вероятность полной замены ФИО
        'change_name_domain': 0.2, # вероятность изменения домена в email
        'double_number': 0.2,      # вероятность дублирования цифры
        'suffix_addition': 0.2     # вероятность добавления суффикса к ФИО
    }
    
    # Генерируем русские записи
    ru_gen = DataGenerator(language=Language.RUS, probabilities=probabilities)
    ru_count = int(count * ru_to_en_ratio)
    ru_fields = ['Фамилия', 'Имя', 'Отчество', 'email']
    
    # Генерируем английские записи на основе русских с транслитерацией
    en_gen = DataGenerator(language=Language.ENG, probabilities=probabilities)
    en_count = count - ru_count
    
    # Генерируем исходные русские данные
    russian_data = ru_gen.generate_clean_clients_list(ru_count, ru_fields)
    
    # Создаем английские варианты с транслитерацией части русских данных
    # и добавляем новые английские данные
    english_data = []
    
    # Транслитерируем часть русских данных
    translit_count = min(ru_count, en_count // 2)
    for i in range(translit_count):
        ru_client = russian_data[i]
        en_client = {
            'id': f"{ru_client['id']}_en",
            'Фамилия': ru_client['Фамилия'].replace('ов', 'ov').replace('ев', 'ev'),
            'Имя': ru_client['Имя'].replace('р', 'r').replace('н', 'n'),
            'Отчество': ru_client['Отчество'].replace('вич', 'vich').replace('вна', 'vna'),
            'email': ru_client['email'].replace('.ru', '.com'),
            'Пол': ru_client['Пол']
        }
        english_data.append(en_client)
    
    # Добавляем новые английские данные
    en_fields = ['Фамилия', 'Имя', 'Отчество', 'email']
    new_en_data = en_gen.generate_clean_clients_list(en_count - translit_count, en_fields)
    
    # Изменяем ID для новых английских данных
    for client in new_en_data:
        client['id'] = f"en_{client['id']}"
    
    english_data.extend(new_en_data)
    
    return russian_data, english_data


def run_benchmark(ru_data, en_data, with_transliteration=False):
    """
    Запускает тестирование производительности матчинга.
    
    :param ru_data: список записей на русском языке
    :param en_data: список записей на английском языке
    :param with_transliteration: использовать ли транслитерацию
    :return: кортеж (время_выполнения, кол-во_совпадений, профиль)
    """
    # Настройка транслитерации
    transliteration_config = TransliterationConfig(
        enabled=with_transliteration,
        standard="Паспортная транслитерация",
        threshold=0.7,
        auto_detect=True,
        normalize_names=True
    )
    
    # Настройка полей для матчинга
    match_config = MatchConfig(
        fields=[
            MatchFieldConfig(field='Фамилия', weight=0.4, transliterate=with_transliteration),
            MatchFieldConfig(field='Имя', weight=0.3, transliterate=with_transliteration),
            MatchFieldConfig(field='Отчество', weight=0.2, transliterate=with_transliteration),
            MatchFieldConfig(field='email', weight=0.1, transliterate=False)
        ],
        length_weight=0.01,
        threshold=0.7,
        block_field='Фамилия',  # Используем блокировку для ускорения
        sort_before_match=True,
        transliteration=transliteration_config
    )
    
    # Создаем профилировщик
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Запускаем сопоставление и замеряем время
    start_time = time.time()
    
    matcher = DataMatcher(config=match_config)
    matches, consolidated = matcher.match_and_consolidate(ru_data, en_data)
    
    duration = time.time() - start_time
    
    profiler.disable()
    
    # Получаем результаты профилирования в строку
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats(10)  # Выводим только 10 самых затратных функций
    
    return duration, len(matches), ps, s.getvalue()


def print_benchmark_results(results, title):
    """
    Выводит результаты бенчмарка в виде таблицы.
    
    :param results: словарь с результатами тестов
    :param title: заголовок таблицы
    """
    table = PrettyTable()
    table.title = title
    table.field_names = ["Количество записей", "Режим", "Время (сек)", "Найдено совпадений", "Скорость (записей/сек)"]
    
    for data_size in sorted(results.keys()):
        for mode, (duration, matches_count, _, _) in results[data_size].items():
            # Вычисляем скорость обработки записей в секунду
            speed = data_size / duration if duration > 0 else 0
            table.add_row([
                data_size,
                mode,
                f"{duration:.4f}",
                matches_count,
                f"{speed:.2f}"
            ])
    
    print(table)


def plot_benchmark_results(results, title):
    """
    Визуализирует результаты теста производительности.
    
    :param results: словарь с результатами тестов
    :param title: заголовок графика
    """
    sizes = sorted(results.keys())
    standard_times = [results[size]["Без транслитерации"][0] for size in sizes]
    translit_times = [results[size]["С транслитерацией"][0] for size in sizes]
    
    # График времени выполнения
    plt.figure(figsize=(12, 6))
    
    width = 0.35
    ind = np.arange(len(sizes))
    
    plt.subplot(1, 2, 1)
    plt.bar(ind - width/2, standard_times, width, label='Без транслитерации')
    plt.bar(ind + width/2, translit_times, width, label='С транслитерацией')
    
    plt.xlabel('Количество записей')
    plt.ylabel('Время выполнения (сек)')
    plt.title(f'{title} - Время выполнения')
    plt.xticks(ind, sizes)
    plt.legend()
    
    # График соотношения времени (транслитерация / стандартный)
    plt.subplot(1, 2, 2)
    ratio = [t/s if s > 0 else 0 for t, s in zip(translit_times, standard_times)]
    
    plt.bar(ind, ratio)
    plt.axhline(y=1, color='r', linestyle='-')
    
    plt.xlabel('Количество записей')
    plt.ylabel('Соотношение времени (транслит/стандарт)')
    plt.title('Относительная производительность')
    plt.xticks(ind, sizes)
    
    plt.tight_layout()
    plt.savefig(f'benchmark_results_{min(sizes)}_{max(sizes)}.png')
    plt.close()
    
    # Выводим процент увеличения времени
    print("\nПроцент увеличения времени при использовании транслитерации:")
    for i, size in enumerate(sizes):
        increase = (translit_times[i] - standard_times[i]) / standard_times[i] * 100 if standard_times[i] > 0 else 0
        print(f"Размер данных: {size} - Увеличение: {increase:.2f}%")


def main():
    """
    Основная функция для запуска бенчмарка.
    """
    print("\n===== ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ МАТЧИНГА С ТРАНСЛИТЕРАЦИЕЙ =====\n")
    
    # Размеры наборов данных для тестирования
    data_sizes = [100, 1000]
    
    results = {}
    
    # Запускаем тесты для каждого размера данных
    for size in data_sizes:
        print(f"\nГенерация данных размером {size} записей...")
        ru_data, en_data = generate_mixed_language_data(size)
        
        print(f"Запуск матчинга без транслитерации ({size} записей)...")
        standard_results = run_benchmark(ru_data, en_data, with_transliteration=False)
        
        print(f"Запуск матчинга с транслитерацией ({size} записей)...")
        translit_results = run_benchmark(ru_data, en_data, with_transliteration=True)
        
        results[size] = {
            "Без транслитерации": standard_results,
            "С транслитерацией": translit_results
        }
    
    # Выводим результаты
    print_benchmark_results(results, "Результаты тестирования производительности")
    
    # Строим графики
    try:
        plot_benchmark_results(results, "Сравнение производительности")
        print("\nГрафики с результатами сохранены в файл benchmark_results_*.png")
    except ImportError:
        print("\nНе удалось построить графики. Убедитесь, что установлен matplotlib и numpy.")
    
    # Выводим детальную информацию о профилировании для последнего теста
    print("\nДетальная информация о наиболее затратных функциях (для 1000 записей):")
    print("\nБез транслитерации:")
    print(results[1000]["Без транслитерации"][3])
    print("\nС транслитерацией:")
    print(results[1000]["С транслитерацией"][3])
    
    print("\n===== ЗАВЕРШЕНИЕ ТЕСТИРОВАНИЯ ПРОИЗВОДИТЕЛЬНОСТИ =====\n")


if __name__ == "__main__":
    main() 