import cProfile
import pstats
import random
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

_probabilities = {
    'double_letter_prob' : 0.4,
    'change_letter_prob' : 0.5,
    'change_name_prob' : 0.1,
    'change_name_domain_prob' : 0.3,
    'double_number_prob' : 0.3,
    'threshold' : 85
}



class DataGenerator:
    """Инициализация генератора фиктивных данных"""
    def __init__(self,
                 language=Language.RUS,
                 probabilities=None
                 ):
        self.language = language
        self.fake = faker.Faker(self.language.value)

        self.probabilities = probabilities or {
            'double_letter_prob': 0.4,
            'change_letter_prob': 0.5,
            'change_name_prob': 0.1,
            'change_name_domain_prob': 0.3,
            'double_number_prob': 0.3,
            'threshold': 85
        }
        self.double_letter_prob = self.probabilities['double_letter_prob']
        self.change_letter_prob = self.probabilities['change_letter_prob']
        self.change_name_prob = self.probabilities['change_name_prob']
        self.change_name_domain_prob = self.probabilities['change_name_domain_prob']
        self.double_number_probability = self.probabilities['double_number_prob']
        self.threshold = self.probabilities['threshold']

        self.gender_detector = gender.Detector()

    def doubling_letter(self, name, probability=0.5):
        if len(name) < 2:
            return name
        index_to_double = random.randint(0, len(name) - 1)
        return name[:index_to_double] + name[index_to_double] + name[index_to_double:]

    def changing_letter_rus(self, name, probability=0.5):
        if len(name) < 2:
            return name
        index_to_change = random.randint(1, len(name) - 1)
        new_letter = random.choice([c for c in 'абвгдежзиклмнопрстуфхцчшщэюя' if c != name[index_to_change]])
        return name[:index_to_change] + new_letter + name[index_to_change + 1:]

    def changing_letter_eng(self, name):
        if len(name) < 2:
            return name
        index_to_change = random.randint(1, len(name) - 1)
        new_letter = random.choice([c for c in 'abcdefghijklmnopqrstuvwxyz' if c != name[index_to_change]])
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
            return f"{self.changing_letter_eng(name)}@{domain}"
        if random_number < self.double_letter_prob + self.change_letter_prob + self.change_name_domain_prob:
            return f"{self.changing_letter_eng(name)}@{self.changing_letter_eng(domain)}"
        # Добавляем случайное число к имени пользователя    # name += str(random.randint(10, 99))
        return f"{name}@{domain}"

    """Функция для создания небольших различий в именах"""
    def vary_name(self, name, part: NamePart) -> (str, bool):
        # Определяем вероятность изменения буквы или всего имени
        random_number = random.random()
        flag_change_full_name = False  # Если изменили полностью Ф\И\О, то очевидно почты не могут совпадать

        # Случайно решаем, какое действие выполнить
        if random_number < self.double_letter_prob:
            return self.doubling_letter(name), flag_change_full_name
        elif random_number < self.double_letter_prob + self.change_letter_prob:
            if self.language == Language.RUS:
                return self.changing_letter_rus(name), flag_change_full_name
            else:
                return self.changing_letter_eng(name), flag_change_full_name
        elif random_number < self.double_letter_prob + self.change_letter_prob + self.change_name_prob:
            flag_change_full_name = True
            # Меняем Ф\И\О целиком
            if part == NamePart.FIRST:
                return self.fake.first_name_male() if gender =='male' else self.fake.first_name_female(), flag_change_full_name
            if part == NamePart.LAST:
                return self.fake.last_name_male() if gender == 'male' else self.fake.last_name_female(), flag_change_full_name
            if part == NamePart.MIDDLE:
                return self.fake.middle_name_male() if gender == 'male' else self.fake.middle_name_female(), flag_change_full_name

        if random.choice([True, False]):
            if self.language == Language.RUS:
                return name + random.choice(['ий', 'ов', 'ев', 'ский', 'цкий']), flag_change_full_name
            else:
                # todo: аналогичная смена окончаний на английском?
                # либо скип, тк отчества нет. либо другая логика
                pass
        return name, flag_change_full_name

    """Генерация списка клиентов"""
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
    def match_clients(self, list1, list2):
        # Группировка по первой букве фамилии
        def group_by_surname_initial(clients):
            groups = defaultdict(list)
            for client in clients:
                surname = client.get('Фамилия', '')
                if surname:
                    prefix = surname[0].upper()
                    groups[prefix].append(client)
            return groups

        groups1 = group_by_surname_initial(list1)
        groups2 = group_by_surname_initial(list2)

        matched_clients = []
        consolidated_clients = []
        matched_emails_1 = set()
        matched_emails_2 = set()

        for prefix in groups1:
            group1 = groups1[prefix]
            group2 = groups2.get(prefix, [])

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

                    # todo: мапить объект данных вне завиcимости от кол-ва полей, избавиться от хардкода
                    name_similarity = fuzz.token_sort_ratio(full_name1, full_name2)
                    email_similarity = fuzz.token_sort_ratio(email1, email2)
                    average_similarity = (name_similarity + email_similarity) / 2

                    if average_similarity >= self.threshold:
                        matched_clients.append({
                            'Запись 1': [full_name1, email1],
                            'Запись 2': [full_name2, email2],
                            'Совпадение': [average_similarity]
                        })
                        matched_emails_1.add(email1)
                        matched_emails_2.add(email2)

                        consolidated_clients.append(select_cleaner_client(client1, client2))
                        break

        # Добавляем оставшиеся уникальные записи
        unmatched_clients_1 = [client for client in list1 if client['Адрес почты'] not in matched_emails_1]
        unmatched_clients_2 = [client for client in list2 if client['Адрес почты'] not in matched_emails_2]
        consolidated_clients.extend(unmatched_clients_1 + unmatched_clients_2)

        return matched_clients, consolidated_clients

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


def select_cleaner_client(client1, client2):
    """
    Выбирает более "чистого" клиента, сравнивая нормализованное расстояние Левенштейна
    между ФИО и email каждого клиента.
    """
    def compute_score(client):
        # todo: аналогично на другие возможные параметры, без хардкода
        full_name = f"{client['Фамилия']} {client['Имя']} {client['Отчество']}"
        email = client['Адрес почты']
        name_distance = Levenshtein.normalized_distance(full_name, "")
        email_distance = Levenshtein.normalized_distance(email, "")
        return (name_distance + email_distance) / 2

    score1 = compute_score(client1)
    score2 = compute_score(client2)

    return client1 if score1 <= score2 else client2

if __name__ == "__main__":
    profiler = cProfile.Profile() # profiler

    data = DataGenerator(probabilities=_probabilities)

    # Создание основного списка клиентов
    clients_list_original = data.generate_clients_list(1000)

    # Копирование списка и внесение случайных изменений для создания второго списка
    clients_list_variant = [client.copy() for client in clients_list_original]
    name_changed_list = []  # Список, содержащий инф-ю об изменении Ф\И\О
    for client in clients_list_variant:
        if random.choice([True, False]):
            client['Имя'], flag_name_changed = data.vary_name(client['Имя'], NamePart.FIRST)
            name_changed_list.append(flag_name_changed)
        if random.choice([True, False]):
            client['Фамилия'], flag_name_changed = data.vary_name(client['Фамилия'], NamePart.LAST)
            name_changed_list.append(flag_name_changed)
        if random.choice([True, False]):
            client['Отчество'], flag_name_changed = data.vary_name(client['Отчество'], NamePart.MIDDLE)
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

    # print(f"{len(clients_list_original)=}")
    # print(f"{len(clients_list_variant)=}")

    # Вывод первых пяти клиентов из каждого списка для проверки
    print('Первые пять клиентов из оригинального списка:')

    # df_clients_original = pd.DataFrame(clients_list_original)
    # print(df_clients_original.head(5))
    print_table(clients_list_original[:3])

    print('\nПервые пять клиентов из похожего списка:')
    # df_clients_variant = pd.DataFrame(clients_list_variant)
    # print(df_clients_variant.head(5))
    print_table(clients_list_variant[:3])

    print()

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

