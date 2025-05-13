import cProfile
import pstats
import pandas as pd
import re

from prettytable import PrettyTable
from data_generator import DataGenerator
from data_matcher import DataMatcher
from match_config_classes import MatchConfig, MatchFieldConfig


def generate_test_data(probabilities, gen_fields, count=100):
    dg = DataGenerator(probabilities=probabilities)
    original_list, variant_list = dg.generate_clients_pair(count, fields=gen_fields)
    return original_list, variant_list


# todo: in/out json/csv на выбор?
def generate_and_save_test_data(probabilities, gen_fields, count=100):
    dg = DataGenerator(probabilities=probabilities)
    original_list, variant_list = dg.generate_clients_pair(count, fields=gen_fields)
    dg.save_to_json(original_list, 'original_data_list1.json')
    dg.save_to_csv(original_list, 'original_data_list1.csv')
    dg.save_to_json(variant_list, 'variant_data_list2.json')
    dg.save_to_csv(variant_list, 'variant_data_list2.csv')
    return original_list, variant_list


def display_sample_data(original_list, variant_list, rows_count=5):
    print(f'Первые {rows_count} клиентов из оригинального списка:')
    print_table(original_list[:rows_count])
    print(f'\nПервые {rows_count} клиентов из искаженного списка:')
    print_table(variant_list[:rows_count])
    print()


def run_matching(original_list, variant_list, config: MatchConfig):
    match_fields = [f.field for f in config.fields]
    weights = {f.field: f.weight for f in config.fields}
    weights['length'] = config.length_weight

    matcher = DataMatcher(config=config)
    matches, consolidated = matcher.match_and_consolidate(original_list, variant_list)
    return matcher, matches, consolidated


def display_matches(matches, limit=5):
    """
    Выводит результаты совпадений в виде таблицы PrettyTable.
    """
    # Создаем таблицу и задаем заголовки колонок
    table = PrettyTable()
    # table.field_names = ["ID 1", "Запись 1", "ID 2", "Запись 2", "Совпадение"]
    table.field_names = ["Запись 1", "Запись 2", "Совпадение"]

    # Добавляем строки в таблицу
    for match in matches[:limit]:
        # id1 = match["ID 1"]
        # id2 = match["ID 2"]
        rec1 = " ".join(match["Запись 1"])
        rec2 = " ".join(match["Запись 2"])
        score = f"{match['Совпадение'][0]:.2f}"
        # table.add_row([id1, rec1, id2, rec2, score])
        table.add_row([rec1, rec2, score])

    # Опции выравнивания
    # table.align["ID 1"] = "r"
    # table.align["ID 2"] = "r"
    table.align["Запись 1"] = "l"
    table.align["Запись 2"] = "l"
    table.align["Совпадение"] = "r"

    # Вывод
    print(f"\nОтобрано: {len(matches)} записей\n")
    print(table)


def display_consolidated(consolidated, sort_field, limit=5):
    df_consolidated = pd.DataFrame(consolidated)
    if sort_field in df_consolidated.columns:
        df_consolidated = df_consolidated.sort_values(by="Фамилия", ascending=True)
    else:
        print(f'Столбец {sort_field} отсутствует в данных.')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('display.max_rows', limit)
    print(f"\nКонсолидировано: {len(consolidated)} записей\n")
    print(df_consolidated)



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


def save_results(matcher, matches, consolidated):
    matcher.save_matches_to_json(matches, 'matches.json')
    matcher.save_matches_to_csv(matches, 'matches.csv')
    matcher.save_consolidated_to_json(consolidated, 'consolidated.json')
    matcher.save_consolidated_to_csv(consolidated, 'consolidated.csv')


def main():
    # # параметры для генерации. Должны совпадать с параметрами для матчинга если тестируется
    # probabilities = {
    #     'double_letter': 0.3,       # вероятность дублирования буквы
    #     'change_letter': 0.2,       # вероятность замены буквы
    #     'change_name': 0.1,         # вероятность полной замены ФИО
    #     'change_name_domain': 0.2,  # вероятность изменения домена в email
    #     'double_number': 0.2,       # вероятность дублирования цифры
    #     'suffix_addition': 0.3      # вероятность добавления суффикса к ФИО
    # }
    # gen_fields = ['Фамилия', 'Имя', 'Отчество', 'email']
    # num_clients = 1000
    #
    # original_list, variant_list = generate_test_data(probabilities, gen_fields, num_clients)
    # display_sample_data(original_list, variant_list)
    # #

    # параметры для матчинга и консолидации
    match_config = MatchConfig(
        fields=[
            # MatchFieldConfig(field='Фамилия', weight=0.3),
            # MatchFieldConfig(field='Имя', weight=0.3),
            # MatchFieldConfig(field='Отчество', weight=0.2),
            # MatchFieldConfig(field='email', weight=0.1)
        ],
        length_weight=0.01,
        threshold=0.85,
        block_field='Фамилия',
        # group_fields=[],
        sort_before_match=True
    )

    profiler = cProfile.Profile()
    profiler.enable()

    matcher, matches, consolidated = run_matching(original_list, variant_list, match_config)
    #

    profiler.disable()
    profiler.dump_stats("profile_data.prof")

    display_matches(matches, 15)

    display_consolidated(consolidated,'Фамилия', 15)

    save_results(matcher, matches, consolidated)

    stats = pstats.Stats("profile_data.prof")
    stats.strip_dirs().sort_stats("cumulative").print_stats()

if __name__ == "__main__":
    main()
