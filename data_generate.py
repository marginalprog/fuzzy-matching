import cProfile
import pstats
import random
import re

import faker
import pandas as pd
from itertools import product
import json
import csv
import gender_guesser.detector as gender
from prettytable import PrettyTable
from enum import Enum
from rapidfuzz import fuzz
from collections import defaultdict
from rapidfuzz.distance import Levenshtein


class NamePart(Enum):
    FIRST = 'name'
    LAST = 'lastname'
    MIDDLE = 'middlename'


class Language(Enum):
    RUS = 'ru_RU',
    ENG = 'en_US'


# Гиперпараметры гд: вероятности ошибок
_probabilities = {
    'double_letter' : 0.4,
    'change_letter' : 0.5,
    'change_name' : 0.1,
    'change_name_domain' : 0.3,
    'double_number' : 0.3,
    'suffix_addition': 0.3,
    'threshold' : 85
}

# Гиперпараметры гд: веса для полей
_weights = {
    'name': 0.6,
    'email': 0.4,
    'length': 0.01,
}

# Поле(столбец), по которому нужно делать блокировку
_block_field = 'Фамилия'

# Поля(столбцы), по которым нужно делать группировку
_group_fields = []

# Поля(столбцы), по которым будет мэтчинг
_match_fields = ['']

class DataGenerator:
    """Инициализация генератора фиктивных данных"""
    def __init__(self,
                 language=Language.RUS,
                 match_fields=None,
                 probabilities=None,
                 weights=None,
                 block_field=None,
                 group_fields=None,
                 ):
        self.language = language
        self.fake = faker.Faker(self.language.value)

        # todo: задание self.keyfields из csv или json
        # юзер сам определяет по каким полям лучше сделать блокировку (оптимальнее) и какие поля сортировать

        self.block_field = block_field
        self.group_fields = group_fields

        self.weights = weights # or {} - default value
        self.name_weight = self.weights['name']
        self.email_weight = self.weights['email']
        self.length_weight = self.weights['length']

        self.probabilities = probabilities # or {} - default value
        self.double_letter_prob = self.probabilities['double_letter']
        self.change_letter_prob = self.probabilities['change_letter']
        self.change_name_prob = self.probabilities['change_name']
        self.change_name_domain_prob = self.probabilities['change_name_domain']
        self.double_number_probability = self.probabilities['double_number']
        self.suffix_addition_prob = self.probabilities['suffix_addition']
        self.threshold = self.probabilities['threshold']

        self.gender_detector = gender.Detector()

    def doubling_letter(self, name):
        if len(name) < 2:
            return name
        index_to_double = random.randint(0, len(name) - 1)
        return name[:index_to_double] + name[index_to_double] + name[index_to_double:]

    def changing_letter(self, name, email_flag=False):
        if len(name) < 2:
            return name
        index_to_change = random.randint(1, len(name) - 1)
        new_letter = ''
        if self.language == Language.ENG or email_flag:
            new_letter = random.choice([c for c in 'abcdefghijklmnopqrstuvwxyz' if c != name[index_to_change]])
        elif self.language == Language.RUS:
            new_letter = random.choice([c for c in 'абвгдежзиклмнопрстуфхцчшщэюя' if c != name[index_to_change]])
        else:
            # todo: try-catch для ошибки
            print(f'Несуществующий язык: {self.language}')
        return name[:index_to_change] + new_letter + name[index_to_change + 1:]

    """Создание вариации номера телефона"""
    def vary_phone_number(self, phone):
        # todo: принимать флаг изменения человека (ф\и\о, как в почте)
        phone_as_list = list(phone)

        # Изменяем одну случайную цифру в номере телефона
        index_to_vary = random.randint(2, len(phone_as_list) - 1)
        phone_as_list[index_to_vary] = str(random.randint(0, 9))

        # вероятность двойной ошибки в номере
        # С некоторой вероятностью изменяем еще одну случайную цифру номера
        if random.random() < self.double_number_probability:
            index_to_vary = random.randint(2, len(phone_as_list) - 1)
            phone_as_list[index_to_vary] = str(random.randint(0, 9))
        return ''.join(phone_as_list)

    """Функция для создания вариации электронной почты"""
    def vary_email(self, email, new_person):
        name, domain = email.split('@')
        # перенести в конструктор, чтобы можно было при инициализации управлять вероятностями
        random_number = random.random()

        if new_person:  # Если изменено было Ф\И\О, то генерируем новый адрес почты
            return ''.join(self.fake.email())

        if random_number < self.double_letter_prob:
            return f"{self.doubling_letter(name)}@{domain}"
        if random_number < self.double_letter_prob + self.change_letter_prob:
            return f"{self.changing_letter(name, True)}@{domain}"
        if random_number < self.double_letter_prob + self.change_letter_prob + self.change_name_domain_prob:
            return f"{self.changing_letter(name, True)}@{self.changing_letter(domain, True)}"
        # Добавляем случайное число к имени пользователя    # name += str(random.randint(10, 99))
        return f"{name}@{domain}"

    """Функция для создания небольших различий в именах"""
    def vary_name(self, name, part: NamePart, gender='male') -> (str, bool):
        # Определяем вероятность изменения буквы или всего имени
        random_number = random.random()
        flag_change_full_name = False  # Если изменили полностью Ф\И\О, то очевидно почты не могут совпадать

        # Случайно решаем, какое действие выполнить
        if random_number < self.double_letter_prob:
            return self.doubling_letter(name), flag_change_full_name
        elif random_number < self.double_letter_prob + self.change_letter_prob:
            return self.changing_letter(name), flag_change_full_name
        elif random_number < self.double_letter_prob + self.change_letter_prob + self.change_name_prob:
            flag_change_full_name = True
            # Меняем Ф\И\О целиком
            if part == NamePart.FIRST:
                return self.fake.first_name_male() if gender =='м' else self.fake.first_name_female(), flag_change_full_name
            if part == NamePart.LAST:
                return self.fake.last_name_male() if gender == 'м' else self.fake.last_name_female(), flag_change_full_name
            if part == NamePart.MIDDLE:
                return self.fake.middle_name_male() if gender == 'м' else self.fake.middle_name_female(), flag_change_full_name

        if random.random() < self.suffix_addition_prob:
            if self.language == Language.RUS:
                russian_suffixes = ['ов', 'ев', 'ин', 'ский', 'цкий']
                return name + random.choice(russian_suffixes), flag_change_full_name
            elif self.language == Language.ENG:
                english_suffixes = ['son', 'man', 'er', 'ley', 'ton', 'ford', 'field', 'wood']
                return name + random.choice(english_suffixes), flag_change_full_name
        return name, flag_change_full_name

    """Генерация списка клиентов"""
    # todo:  добавить выбор генерации номера телефона и работы с его полями
    def generate_clients_list(self, num_clients):
        clients_list = []
        for _ in range(num_clients):
            gender = random.choice(['м', 'ж'])
            name = self.fake.first_name_male() if gender == 'м' else self.fake.first_name_female()
            surname = self.fake.last_name_male() if gender == 'м' else self.fake.last_name_female()
            patronymic = self.fake.middle_name_male() if gender == 'м' else self.fake.middle_name_female()
            email = self.fake.email()
            # phone = fake.phone_number()
            # address = fake.address().replace('\n', ', ')
            clients_list.append({
                'Фамилия': surname,
                'Имя': name,
                'Отчество': patronymic,
                'Адрес почты': email,
                'Пол': gender
                # 'Номер телефона': phone,
                # 'Адрес': address
            })
        return clients_list

    """Функция для сопоставления клиентов из двух списков"""
    def match_clients(self, list1, list2) -> (list, list):
        blocks1 = block_by_fields(list1, self.block_field, self.group_fields)
        blocks2 = block_by_fields(list2, self.block_field, self.group_fields)

        matched_clients = []
        consolidated_clients = []
        matched_emails_1 = set()
        matched_emails_2 = set()

        # группировка/матчинг - объединение данных из блоков
        for prefix in blocks1:
            group1 = blocks1[prefix]
            group2 = blocks2.get(prefix, [])

            for client1 in group1:
                email1 = client1['Адрес почты']
                if email1 in matched_emails_1:
                    continue

                full_name1 = f"{client1['Фамилия']} {client1['Имя']} {client1['Отчество']}"
                email1 = client1['Адрес почты']

                for client2 in group2:
                    email2 = client2['Адрес почты']
                    if email2 in matched_emails_2:
                        continue

                    full_name2 = f"{client2['Фамилия']} {client2['Имя']} {client2['Отчество']}"
                    email2 = client2['Адрес почты']

                    values = {
                        'name': fuzz.token_sort_ratio(full_name1, full_name2),
                        'email': fuzz.token_sort_ratio(email1, email2),
                    }

                    total_weight = sum(self.weights.values())
                    weighted_sum = sum(values[key] * self.weights[key] for key in values if key in self.weights)

                    # средневзвешенная сумма атрибутов
                    similarity = weighted_sum / total_weight if total_weight else 0

                    if similarity >= self.threshold:
                        matched_clients.append({
                            'Запись 1': [full_name1, email1],
                            'Запись 2': [full_name2, email2],
                            'Совпадение': [similarity]
                        })
                        matched_emails_1.add(email1)
                        matched_emails_2.add(email2)

                        cleaner_client = self.select_cleaner_client(client1, client2, client1.keys())
                        consolidated_clients.append(cleaner_client)
                        break

        # Добавляем оставшиеся уникальные записи
        unmatched_clients_1 = [client for client in list1 if client['Адрес почты'] not in matched_emails_1]
        unmatched_clients_2 = [client for client in list2 if client['Адрес почты'] not in matched_emails_2]
        consolidated_clients.extend(unmatched_clients_1 + unmatched_clients_2)

        return matched_clients, consolidated_clients

    def select_cleaner_client(self, client1, client2, key_fields):
        def cleanliness_score(client):
            combined = ' '.join(str(client.get(field, '')) for field in key_fields)
            special_chars = len(re.findall(r'[^a-zA-Zа-яА-Я0-9\s]', combined))
            length = len(combined)
            return special_chars + length * self.length_weight

        score1 = cleanliness_score(client1)
        score2 = cleanliness_score(client2)

        if score1 < score2:
            return client1
        elif score2 < score1:
            return client2
        else:
            # Дополнительно используем другие критерии:
            # Выбор записи с меньшей длиной объединенных полей
            length1 = sum(len(str(client1.get(field, ''))) for field in key_fields)
            length2 = sum(len(str(client2.get(field, ''))) for field in key_fields)
            return client1 if length1 <= length2 else client2

    def save_to_json(self, data, filename):
        """Сохраняет данные в JSON-файл"""
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    def save_to_csv(self, data, filename):
        """Сохраняет данные в CSV-файл"""
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def load_from_json(self, filename):
        """Загружает данные из JSON-файла"""
        with open(filename, 'r', encoding='utf-8') as input_file:
            return json.load(input_file)

    def load_from_csv(self, filename):
        """Загружает данные из CSV-файла"""
        with open(filename, 'r', newline='', encoding='utf-8') as input_file:
            reader = csv.DictReader(input_file)
            return [row for row in reader]

def sort_data(clients, sort_keys):
    """Сортирует входные данные, чтобы ускорить блокировку и сопоставление"""
    return sorted(clients, key=lambda x: tuple(x.get(k, '') for k in sort_keys))

def weighted_average(values, weights):
    total_weight = sum(weights.values())
    weighted_sum = sum(values[key] * weights[key] for key in values if key in weights)
    return weighted_sum / total_weight if total_weight else 0

def block_by_fields(clients, block_field, group_fields=None):
    """
    Универсальная функция блокировки и группировки записей.

    :param clients: Список словарей с данными клиентов.
    :param block_field: Название поля для блокировки (например, 'Фамилия').
    :param group_fields: Список полей для дополнительной группировки внутри блоков (например, ['Имя', 'Отчество']).
    :return: Словарь блоков с возможной дополнительной группировкой.
    """
    if group_fields and group_fields.length > 0:
        blocks = defaultdict(lambda: defaultdict(list))
        for client in clients:
            block_value = client.get(block_field, '')
            if not block_value:
                continue
            block_key = block_value[0].upper()
            group_key = ' '.join(str(client.get(field, '')).strip() for field in group_fields)
            blocks[block_key][group_key].append(client)
    else:
        blocks = defaultdict(list)
        for client in clients:
            block_value = client.get(block_field, '')
            if not block_value:
                continue
            block_key = block_value[0].upper()
            blocks[block_key].append(client)
    return blocks


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


if __name__ == "__main__":
    profiler = cProfile.Profile() # profiler

    data = DataGenerator(
        match_fields=_match_fields, # todo
        probabilities=_probabilities,
        weights=_weights,
        block_field=_block_field,
        group_fields=_group_fields
    )

    # Создание основного списка клиентов
    clients_list_original = data.generate_clients_list(1000)

    # todo: универсальный парсинг по полям без привязки к названиям столбцов
    # Копирование списка и внесение случайных изменений для создания второго списка
    clients_list_variant = [client.copy() for client in clients_list_original]
    name_changed_list = []  # Список, содержащий инф-ю об изменении Ф\И\О
    for client in clients_list_variant:
        if random.choice([True, False]):
            client['Имя'], flag_name_changed = data.vary_name(client['Имя'], NamePart.FIRST, client['Пол'])
            name_changed_list.append(flag_name_changed)
        if random.choice([True, False]):
            client['Фамилия'], flag_name_changed = data.vary_name(client['Фамилия'], NamePart.LAST, client['Пол'])
            name_changed_list.append(flag_name_changed)
        if random.choice([True, False]):
            client['Отчество'], flag_name_changed = data.vary_name(client['Отчество'], NamePart.MIDDLE, client['Пол'])
            name_changed_list.append(flag_name_changed)
        # if random.choice([True, False]) or (True in name_changed_list):  # Или 0.5 вероятность для изменения или 100% меняем
        #     client['Номер телефона'] = vary_phone_number(client['Номер телефона'])

        if True in name_changed_list:  # 100% меняем
            client['Адрес почты'] = data.vary_email(client['Адрес почты'], True)
        else:
            if random.choice([True, False]):  # Если фио не менялись, то с вероятностью 0.5 делаем опечатки
                client['Адрес почты'] = data.vary_email(client['Адрес почты'], False)
        flag_name_changed = False  # Обновляем флаг изменения имени
        name_changed_list.clear()  # Обновляем список состояний Ф\И\О


    # Вывод первых пяти клиентов из каждого списка для проверки
    print('Первые пять клиентов из оригинального списка:')

    print_table(clients_list_original[:3])

    print('\nПервые пять клиентов из похожего списка:')

    print_table(clients_list_variant[:3])

    print()

    sorted_list1 = sort_data(clients_list_original, clients_list_original[0].keys())
    sorted_list2 = sort_data(clients_list_variant, clients_list_original[0].keys())

    profiler.enable()
    # Сопоставление клиентов
    matches, consolidated_data = data.match_clients(clients_list_original, clients_list_variant)

    profiler.disable()
    profiler.dump_stats("profile_data.prof")

    c = 0
    for match in matches:
        print(70 * '_')
        print(
            f"{' '.join(match['Запись 1']):<61} | 1.00\n{' '.join(match['Запись 2']):<61} | {(match['Совпадение'][0]/100):.2f}")
        c += 1
        if c > 5:
            break

    print(f"\n\t\t\t\t\tОтобрано {len(matches)} записей")

    print(f"\nКонсолидация будет содержать {len(consolidated_data)} записей")

    df_consolidated_data = pd.DataFrame(consolidated_data).sort_values(by="Фамилия", ascending=True)

    pd.set_option('display.max_colwidth', 40)
    pd.set_option('display.max_rows', None)
    print(df_consolidated_data.head(10))
    print(df_consolidated_data.tail(20))

    # profiler.sort_stats('time')
    # profiler.sort_stats("cumulative").print_stats()

    stats = pstats.Stats("profile_data.prof")
    stats.strip_dirs().sort_stats("cumulative").print_stats()

