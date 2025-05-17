#!/usr/bin/env python
"""
Скрипт для запуска всех тестов и генерации отчетов о производительности
и эффективности алгоритмов нечеткого сопоставления.
"""

import os
import time
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

from fuzzy_matching.tests.benchmark_test import main as run_benchmark
from fuzzy_matching.tests.advanced_benchmark import main as run_advanced_benchmark
from fuzzy_matching.examples.algorithm_comparison_example import main as run_algorithm_comparison
from fuzzy_matching.examples.domain_specific_example import main as run_domain_specific


def create_directory(path):
    """
    Создает директорию, если она не существует.
    
    :param path: путь к директории
    """
    if not os.path.exists(path):
        os.makedirs(path)


def run_all_benchmarks():
    """
    Запускает все тесты производительности и генерирует отчет.
    """
    print("\n===== ЗАПУСК ВСЕХ ТЕСТОВ ПРОИЗВОДИТЕЛЬНОСТИ =====\n")
    
    # Создаем директории для результатов
    results_dir = "results"
    reports_dir = os.path.join(results_dir, "reports")
    create_directory(results_dir)
    create_directory(reports_dir)
    
    # Запускаем стандартный тест производительности
    print("\n----- Запуск стандартного теста производительности -----\n")
    run_benchmark()
    
    # Запускаем расширенный тест производительности
    print("\n----- Запуск расширенного теста производительности -----\n")
    run_advanced_benchmark()
    
    # Импортируем результаты тестов
    benchmark_results = pd.read_csv("benchmark_results.csv")
    advanced_results = pd.read_csv("benchmark_results.csv")  # Тот же файл, но с большим количеством данных
    
    # Создаем сводный отчет
    create_summary_report(benchmark_results, advanced_results, reports_dir)


def create_summary_report(benchmark_results, advanced_results, reports_dir):
    """
    Создает сводный отчет по результатам тестов.
    
    :param benchmark_results: результаты стандартного теста
    :param advanced_results: результаты расширенного теста
    :param reports_dir: директория для сохранения отчетов
    """
    print("\n===== СОЗДАНИЕ СВОДНОГО ОТЧЕТА =====\n")
    
    # Объединяем результаты
    all_results = pd.concat([benchmark_results, advanced_results]).drop_duplicates()
    
    # Сохраняем сводную таблицу
    all_results.to_csv(os.path.join(reports_dir, "all_benchmark_results.csv"), index=False)
    
    # Создаем HTML-отчет
    html_report = "<html><head><title>Отчет о производительности алгоритмов нечеткого сопоставления</title>"
    html_report += "<style>body{font-family:Arial;margin:20px}table{border-collapse:collapse;width:100%;margin-bottom:20px}"
    html_report += "th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background-color:#f2f2f2}"
    html_report += "img{max-width:100%;height:auto;display:block;margin:20px 0}</style></head>"
    html_report += "<body><h1>Отчет о производительности алгоритмов нечеткого сопоставления</h1>"
    
    # Добавляем сводную таблицу
    html_report += "<h2>Сводная таблица результатов</h2>"
    html_report += all_results.to_html(index=False)
    
    # Добавляем графики
    html_report += "<h2>Графики производительности</h2>"
    
    # Перечисляем все графики в директории results
    graph_files = [f for f in os.listdir("results") if f.endswith(".png")]
    
    for graph_file in graph_files:
        html_report += f"<h3>{graph_file.replace('_', ' ').replace('.png', '')}</h3>"
        html_report += f"<img src='../{graph_file}' alt='{graph_file}'>"
    
    # Анализ результатов
    html_report += "<h2>Анализ результатов</h2>"
    
    # 1. Анализ влияния транслитерации на производительность
    translit_impact = all_results[all_results['Конфигурация'].isin(['Без транслитерации', 'С транслитерацией'])]
    
    if not translit_impact.empty:
        html_report += "<h3>Влияние транслитерации на производительность</h3>"
        
        # Группируем по размеру данных
        grouped = translit_impact.groupby(['Размер данных', 'Конфигурация'])['Время (сек)'].mean().unstack()
        
        # Вычисляем процент увеличения времени
        if 'Без транслитерации' in grouped.columns and 'С транслитерацией' in grouped.columns:
            grouped['Увеличение (%)'] = (grouped['С транслитерацией'] - grouped['Без транслитерации']) / grouped['Без транслитерации'] * 100
            
            html_report += "<p>Транслитерация увеличивает время выполнения в среднем на "
            html_report += f"{grouped['Увеличение (%)'].mean():.1f}%.</p>"
            
            html_report += "<table><tr><th>Размер данных</th><th>Без транслитерации (сек)</th><th>С транслитерацией (сек)</th><th>Увеличение (%)</th></tr>"
            
            for idx, row in grouped.iterrows():
                html_report += f"<tr><td>{idx}</td><td>{row['Без транслитерации']:.4f}</td><td>{row['С транслитерацией']:.4f}</td><td>{row['Увеличение (%)']:.1f}</td></tr>"
            
            html_report += "</table>"
    
    # 2. Анализ эффективности алгоритмов
    algorithms = all_results[all_results['Конфигурация'].str.contains('Алгоритм')]
    
    if not algorithms.empty:
        html_report += "<h3>Эффективность различных алгоритмов</h3>"
        
        # Вычисляем эффективность (совпадений в секунду)
        algorithms['Эффективность'] = algorithms['Совпадений'] / algorithms['Время (сек)']
        
        # Группируем по алгоритму
        algorithm_efficiency = algorithms.groupby('Конфигурация')['Эффективность'].mean().sort_values(ascending=False)
        
        html_report += "<p>Рейтинг алгоритмов по эффективности (совпадений в секунду):</p>"
        html_report += "<table><tr><th>Алгоритм</th><th>Эффективность (совпадений/сек)</th></tr>"
        
        for alg, eff in algorithm_efficiency.items():
            html_report += f"<tr><td>{alg}</td><td>{eff:.2f}</td></tr>"
        
        html_report += "</table>"
    
    # 3. Рекомендации по выбору алгоритма
    html_report += "<h2>Рекомендации по выбору алгоритма</h2>"
    html_report += "<h3>Для персональных данных (ФИО, контакты)</h3>"
    html_report += "<ul>"
    html_report += "<li><strong>PARTIAL_RATIO</strong> для имен и отчеств - лучше обрабатывает уменьшительные формы (Александр/Саша)</li>"
    html_report += "<li><strong>TOKEN_SORT</strong> или <strong>TOKEN_SET</strong> для адресов - не зависят от порядка слов</li>"
    html_report += "<li><strong>RATIO</strong> для точных полей (email, телефон)</li>"
    html_report += "</ul>"
    
    html_report += "<h3>Для товаров и продуктов</h3>"
    html_report += "<ul>"
    html_report += "<li><strong>TOKEN_SET</strong> для названий и описаний - учитывает перестановку слов</li>"
    html_report += "<li><strong>PARTIAL_RATIO</strong> для брендов - учитывает вариации написания</li>"
    html_report += "<li><strong>RATIO</strong> для артикулов - обеспечивает точность</li>"
    html_report += "</ul>"
    
    html_report += "<h3>Для организаций и компаний</h3>"
    html_report += "<ul>"
    html_report += "<li><strong>TOKEN_SET</strong> для названий компаний - учитывает организационно-правовую форму</li>"
    html_report += "<li><strong>RATIO</strong> для реквизитов (ИНН, КПП) - требуется точность</li>"
    html_report += "</ul>"
    
    html_report += "<h3>Общие рекомендации</h3>"
    html_report += "<ul>"
    html_report += "<li>Всегда используйте блокировку для больших наборов данных - это критически важно для производительности</li>"
    html_report += "<li>Если требуется транслитерация, применяйте ее только к необходимым полям (имя, фамилия)</li>"
    html_report += "<li>Для сложных случаев используйте предметно-ориентированные наборы алгоритмов</li>"
    html_report += "<li>WRatio показывает наилучший баланс между качеством сопоставления и производительностью</li>"
    html_report += "</ul>"
    
    html_report += "</body></html>"
    
    # Сохраняем HTML-отчет
    with open(os.path.join(reports_dir, "benchmark_report.html"), "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print(f"Сводный отчет создан: {os.path.join(reports_dir, 'benchmark_report.html')}")


def run_all_examples():
    """
    Запускает все примеры и сохраняет результаты.
    """
    print("\n===== ЗАПУСК ВСЕХ ПРИМЕРОВ =====\n")
    
    # Запускаем пример сравнения алгоритмов
    print("\n----- Запуск примера сравнения алгоритмов -----\n")
    run_algorithm_comparison()
    
    # Запускаем пример с предметно-ориентированными алгоритмами
    print("\n----- Запуск примера предметно-ориентированных алгоритмов -----\n")
    run_domain_specific()


def main():
    """
    Основная функция для запуска всех тестов и создания отчетов.
    """
    print("===== ГЕНЕРАЦИЯ ОТЧЕТОВ О ПРОИЗВОДИТЕЛЬНОСТИ И ЭФФЕКТИВНОСТИ АЛГОРИТМОВ =====\n")
    
    start_time = time.time()
    
    # Запускаем все тесты производительности
    run_all_benchmarks()
    
    # Запускаем все примеры
    run_all_examples()
    
    # Выводим информацию о завершении
    elapsed_time = time.time() - start_time
    print(f"\nВсе тесты и отчеты успешно сгенерированы за {elapsed_time:.1f} секунд.")
    print("Результаты доступны в директории: results/reports/")


if __name__ == "__main__":
    main() 