import cProfile
import pstats
import random
import re
import uuid

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
    """
    Генерирует фиктивные данные с возможными искажениями (ошибками) в фамилии, имени, отчестве, email и телефоне.
    """
    DEFAULT_PROBABILITIES = {
        'double_letter': 0.4,       # вероятность дублирования буквы
        'change_letter': 0.5,       # вероятность замены буквы
        'change_name': 0.1,         # вероятность полной замены ФИО
        'change_name_domain': 0.3,  # вероятность изменения домена в email
        'double_number': 0.3,       # вероятность дублирования цифры
        'suffix_addition': 0.3      # вероятность добавления суффикса к ФИО
    }

    # Русские названия полей для вывода данных
    FIELD_NAMES = {
        'last_name': 'Фамилия',
        'first_name': 'Имя',
        'middle_name': 'Отчество',
        'email': 'email',
        'phone': 'Телефон'
    }


    def __init__(self,
                 language=Language.RUS,
                 probabilities=None,
                 ):
        self.language = language
        self.fake = faker.Faker(self.language.value)

        # Устанавливаем вероятности искажений (или используем по умолчанию)
        probs = probabilities or {}
        self.double_letter_prob = probs.get('double_letter', self.DEFAULT_PROBABILITIES['double_letter'])
        self.change_letter_prob = probs.get('change_letter', self.DEFAULT_PROBABILITIES['change_letter'])
        self.change_name_prob = probs.get('change_name', self.DEFAULT_PROBABILITIES['change_name'])
        self.change_name_domain_prob = probs.get('change_name_domain', self.DEFAULT_PROBABILITIES['change_name_domain'])
        self.double_number_prob = probs.get('double_number', self.DEFAULT_PROBABILITIES['double_number'])
        self.suffix_addition_prob = probs.get('suffix_addition', self.DEFAULT_PROBABILITIES['suffix_addition'])

        self.gender_detector = gender.Detector()

    def doubling_letter(self, text):
        """Дублирует случайную букву в строке."""
        if len(text) < 2:
            return text
        idx = random.randint(0, len(text) - 1)
        return text[:idx] + text[idx] + text[idx:]

    def changing_letter(self, text, email_flag=False):
        """Заменяет случайную букву на другую (для email используется латиница)."""
        if len(text) < 2:
            return text
        idx = random.randint(1, len(text) - 1)
        letters = []
        if self.language == Language.ENG or email_flag:
            letters = [c for c in 'abcdefghijklmnopqrstuvwxyz']
        elif self.language == Language.RUS:
            letters = [c for c in 'абвгдежзийклмнопрстуфхцчшщэюя']
        current = text[idx].lower()
        letters = [c for c in letters if c != current]
        new_letter = random.choice(letters) if letters else text[idx]
        return text[:idx] + new_letter + text[idx + 1:]

    def vary_phone_number(self, phone, new_person):
        """
        Вносит искажения в номер телефона: изменяет случайную цифру,
        с вероятностью добавляет ещё одно изменение.
        Если new_person=True, генерируется новый номер телефона.
        """
        digits = list(phone)
        if not digits:
            return phone

        if new_person:
            # Если ФИО было полностью изменено, генерируем новый телефон
            return self.fake.email()

        # Изменяем одну случайную цифру в номере телефона
        idx = random.randint(0, len(digits) - 1)
        digits[idx] = str(random.randint(0, 9))

        # Дополнительная ошибка с заданной вероятностью
        if random.random() < self.double_number_prob:
            idx2 = random.randint(0, len(digits) - 1)
            digits[idx2] = str(random.randint(0, 9))
        return ''.join(digits)

    def vary_email(self, email, new_person):
        """
        Вносит искажения в email.
        Если new_person=True, генерируется новый email; иначе
        - дублирует или заменяет букву в логине,
        — или (с некоторой вероятностью) изменяет букву в домене.
        """
        if new_person:
            # Если ФИО было полностью изменено, генерируем новый email
            return self.fake.email()
        user, domain = email.split('@')
        rnd = random.random()
        if rnd < self.double_letter_prob:
            # Дублируем букву в логине email
            return f"{self.doubling_letter(user)}@{domain}"
        elif rnd < self.double_letter_prob + self.change_letter_prob:
            # Заменяем букву в логине email
            return f"{self.changing_letter(user, email_flag=True)}@{domain}"
        elif rnd < self.double_letter_prob + self.change_letter_prob + self.change_name_domain_prob:
            # Изменяем букву и в логине, и в домене
            new_user = self.changing_letter(user, email_flag=True)
            new_domain = self.changing_letter(domain, email_flag=True)
            return f"{new_user}@{new_domain}"
        # todo: Добавляем случайное число к имени пользователя name += str(random.randint(10, 99))
        # Без изменений
        return email

    """Функция для создания небольших различий в именах"""
    def vary_name(self, name, part, gender='male') -> (str, bool):
        """
        Вносит искажения в одно из слов ФИО (имя, фамилию или отчество):
        - дублирует букву,
        — заменяет букву,
        — полностью меняет на другое (через Faker),
        — добавляет суффикс.
        Возвращает (new_name, full_change_flag).
        """
        # Определяем вероятность изменения буквы или всего имени
        rnd = random.random()
        if rnd < self.double_letter_prob:
            return self.doubling_letter(name), False
        elif rnd < self.double_letter_prob + self.change_letter_prob:
            return self.changing_letter(name), False
        elif rnd < self.double_letter_prob + self.change_letter_prob + self.change_name_prob:
            # Полная замена имени через Faker
            if part == 'first':
                new_name = self.fake.first_name_male() if gender == 'м' else self.fake.first_name_female()
            elif part == 'last':
                new_name = self.fake.last_name_male() if gender == 'м' else self.fake.last_name_female()
            elif part == 'middle':
                new_name = self.fake.middle_name_male() if gender == 'м' else self.fake.middle_name_female()
            else:
                new_name = name
            return new_name, True
        # Добавление суффикса
        if random.random() < self.suffix_addition_prob:
            if self.language == Language.RUS:
                russian_suffixes = ['ов', 'ев', 'ин', 'ский', 'цкий']
                return name + random.choice(russian_suffixes), False
            else:
                english_suffixes = ['son', 'man', 'er', 'ley', 'ton', 'ford', 'field', 'wood']
                return name + random.choice(english_suffixes), False
        return name, False


    """Генерация списка клиентов"""

    def generate_clean_clients_list(self, num_clients, fields=None):
        """
        Генерирует список клиентов без искажений.
        :fields - уточнение генерируемых полей
        """
        if fields is None:
            fields = list(self.FIELD_NAMES.values())
        clients = []
        for i in range(num_clients):
            gender = random.choice(['м', 'ж'])
            first = self.fake.first_name_male() if gender == 'м' else self.fake.first_name_female()
            last = self.fake.last_name_male() if gender == 'м' else self.fake.last_name_female()
            middle = self.fake.middle_name_male() if gender == 'м' else self.fake.middle_name_female()
            email = self.fake.email()
            phone = self.fake.phone_number()
            client = {}
            if self.FIELD_NAMES['last_name'] in fields:
                client[self.FIELD_NAMES['last_name']] = last
            if self.FIELD_NAMES['first_name'] in fields:
                client[self.FIELD_NAMES['first_name']] = first
            if self.FIELD_NAMES['middle_name'] in fields:
                client[self.FIELD_NAMES['middle_name']] = middle
            if self.FIELD_NAMES['email'] in fields:
                client[self.FIELD_NAMES['email']] = email
            if self.FIELD_NAMES['phone'] in fields:
                client[self.FIELD_NAMES['phone']] = phone
            client['Пол'] = gender
            client['id'] = f'client_{i+1}'
            clients.append(client)
        return clients

    def apply_distortions(self, clients, fields=None):
        """
        Применяет искажения к списку клиентов.
        """
        if fields is None:
            fields = list(self.FIELD_NAMES.values())
        distorted_clients = []
        for client in clients:
            distorted_client = client.copy()
            gender = distorted_client.get('Пол', 'м')
            new_person = False
            if self.FIELD_NAMES['last_name'] in fields:
                last_name, new_person = self.vary_name(distorted_client[self.FIELD_NAMES['last_name']], 'last', gender)
                distorted_client[self.FIELD_NAMES['last_name']] = last_name
            if self.FIELD_NAMES['first_name'] in fields:
                first_name, new_person = self.vary_name(distorted_client[self.FIELD_NAMES['first_name']], 'first', gender)
                distorted_client[self.FIELD_NAMES['first_name']] = first_name
            if self.FIELD_NAMES['middle_name'] in fields:
                middle_name, new_person = self.vary_name(distorted_client[self.FIELD_NAMES['middle_name']], 'middle', gender)
                distorted_client[self.FIELD_NAMES['middle_name']] = middle_name
            if self.FIELD_NAMES['email'] in fields:
                email = self.vary_email(distorted_client[self.FIELD_NAMES['email']], new_person)
                distorted_client[self.FIELD_NAMES['email']] = email
            if self.FIELD_NAMES['phone'] in fields:
                phone = self.vary_phone_number(distorted_client[self.FIELD_NAMES['phone']], new_person)
                distorted_client[self.FIELD_NAMES['phone']] = phone
            distorted_clients.append(distorted_client)
        return distorted_clients

    def generate_clients_pair(self, num_clients, fields=None):
        """
        Генерирует пару списков клиентов: оригинальный и искаженный.
        """
        clean_clients = self.generate_clean_clients_list(num_clients, fields)
        distorted_clients = self.apply_distortions(clean_clients, fields)
        return clean_clients, distorted_clients

    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_to_csv(self, data, filename):
        if not data:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


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


class DataMatcher:
    """
    Класс для загрузки данных из CSV/JSON, маппинга полей в 'name', 'email', 'phone',
    выполнения фаззи-сопоставления (RapidFuzz) и консолидации похожих записей.
    """
    DEFAULT_WEIGHTS = {
        'name': 0.6,
        'email': 0.4,
        'phone': 0.0,
        'length': 0.01
    }

    def __init__(self,
                 match_fields=None,
                 weights=None,
                 threshold=85,
                 block_field='name',
                 group_fields=None,
                 sort_before_match=False
                 ):
        # Поля для фаззи-матчинга
        self.match_fields = match_fields if match_fields else ['name', 'email']
        self.weights = weights if weights else self.DEFAULT_WEIGHTS.copy()
        self.threshold = threshold
        # Поле для блокировки (первый символ) и дополнительные поля группировки
        self.block_field = block_field
        self.group_fields = group_fields or []
        self.sort_before_match = sort_before_match

    def load_from_csv(self, filename, field_mapping):
        """
        Загружает данные из CSV и мапит колонки по field_mapping в 'name', 'email', 'phone'.
        Пример field_mapping: {'Фамилия': 'name', 'Имя': 'name', 'Email': 'email', 'Телефон': 'phone'}
        """
        records = []
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {}
                name_parts = []
                for col, key in field_mapping.items():
                    if key == 'name':
                        val = row.get(col, '').strip()
                        if val:
                            name_parts.append(val)
                    elif key in ('email', 'phone'):
                        record[key] = row.get(col, '').strip()
                if name_parts:
                    record['name'] = ' '.join(name_parts)
                records.append(record)
        return records

    def load_from_json(self, filename, field_mapping):
        """
        Загружает данные из JSON и мапит колонки по field_mapping в 'name', 'email', 'phone'.
        """
        data = json.load(open(filename, 'r', encoding='utf-8'))
        records = []
        for row in data:
            record = {}
            name_parts = []
            for col, key in field_mapping.items():
                if key == 'name':
                    val = row.get(col, '').strip()
                    if val:
                        name_parts.append(val)
                elif key in ('email', 'phone'):
                    record[key] = row.get(col, '').strip()
            if name_parts:
                record['name'] = ' '.join(name_parts)
            records.append(record)
        return records

    def save_matches_to_json(self, matches, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=4)

    def save_matches_to_csv(self, matches, filename):
        if not matches:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Запись 1', 'Запись 2', 'Совпадение']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for match in matches:
                writer.writerow({
                    'Запись 1': ' '.join(match['Запись 1']),
                    'Запись 2': ' '.join(match['Запись 2']),
                    'Совпадение': f"{match['Совпадение'][0] / 100:.2f}"
                })

    def save_consolidated_to_json(self, consolidated, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=4)

    def save_consolidated_to_csv(self, consolidated, filename):
        if not consolidated:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=consolidated[0].keys())
            writer.writeheader()
            writer.writerows(consolidated)

    @staticmethod
    def _sort_data(clients, sort_keys):
        """Сортирует входные данные, чтобы ускорить блокировку и сопоставление"""
        return sorted(clients, key=lambda x: tuple(x.get(k, '') for k in sort_keys))

    @staticmethod
    def _weighted_average(values, weights):
        total_weight = sum(weights.get(key, 0) for key in values)
        if total_weight == 0:
            return 0
        weighted_sum = sum(values[key] * weights.get(key, 0) for key in values)
        return weighted_sum / total_weight

    def _block_by_fields(self, recs):
        """
        Блокирует записи по первому символу поля block_field,
        с дополнительной группировкой по полям group_fields.
        """
        if self.block_field is None:
            return {'ALL': recs}
        if self.group_fields:
            blocks = defaultdict(lambda: defaultdict(list))
            for rec in recs:
                val = rec.get(self.block_field, '')
                if not val:
                    continue
                key = val[0].upper()
                group_key = tuple(rec.get(f, '') for f in self.group_fields)
                blocks[key][group_key].append(rec)
        else:
            blocks = defaultdict(list)
            for rec in recs:
                val = rec.get(self.block_field, '')
                if not val:
                    continue
                key = val[0].upper()
                blocks[key].append(rec)
        return blocks

    def select_cleaner_client(self, client1, client2):
        """
        Выбирает запись с меньшим 'шумом' (спецсимволы + длина).
        """
        def cleanliness_score(client):
            combined = ' '.join(str(client.get(f, '')) for f in self.match_fields)
            special_chars = len(re.findall(r'[^a-zA-Zа-яА-Я0-9\s]', combined))
            length = len(combined)
            return special_chars + length * self.weights.get('length', 0)

        score1 = cleanliness_score(client1)
        score2 = cleanliness_score(client2)
        if score1 < score2:
            return client1
        elif score2 < score1:
            return client2
        # Если равны, выбираем более короткую запись
        length1 = sum(len(str(client1.get(f, ''))) for f in self.match_fields)
        length2 = sum(len(str(client2.get(f, ''))) for f in self.match_fields)
        return client1 if length1 <= length2 else client2

    def match_and_consolidate(self, list1, list2):
        if self.sort_before_match:
            list1 = self._sort_data(list1, self.match_fields)
            list2 = self._sort_data(list2, self.match_fields)

        blocks1 = self._block_by_fields(list1)
        blocks2 = self._block_by_fields(list2)

        consolidated = []
        matches = []
        matched_1 = set()
        matched_2 = set()

        def process_block(group1, group2):
            for client1 in group1:
                id1 = client1.get('id')
                if id1 in matched_1:
                    continue
                for client2 in group2:
                    id2 = client2.get('id')
                    if id2 in matched_2:
                        continue
                    values = {}
                    for field in self.match_fields:
                        v1 = client1.get(field, '')
                        v2 = client2.get(field, '')
                        if v1 and v2:
                            values[field] = fuzz.token_sort_ratio(v1, v2)

                    similarity = self._weighted_average(values, self.weights)

                    if similarity >= self.threshold:
                        matches.append({
                            'ID 1': id1,
                            'ID 2': id2,
                            'Запись 1': [client1.get(f, '') for f in self.match_fields],
                            'Запись 2': [client2.get(f, '') for f in self.match_fields],
                            'Совпадение': [similarity]
                        })
                        matched_1.add(id1)
                        matched_2.add(id2)
                        cleaner = self.select_cleaner_client(client1, client2)
                        consolidated.append(cleaner)
                        break

        for key in blocks1:
            g1 = blocks1[key]
            g2 = blocks2.get(key, {})
            if isinstance(g1, dict):
                for subkey in g1:
                    process_block(g1[subkey], g2.get(subkey, []) if isinstance(g2, dict) else [])
            else:
                process_block(g1, g2 if isinstance(g2, list) else [])

        # Добавляем несопоставленные записи
        unmatched1 = [c for c in list1 if c.get('id') not in matched_1]
        unmatched2 = [c for c in list2 if c.get('id') not in matched_2]
        consolidated.extend(unmatched1 + unmatched2)

        return matches, consolidated


if __name__ == "__main__":
    profiler = cProfile.Profile() # profiler
    match_fields = ['Фамилия', 'Имя', 'Отчество', 'email']
    dg = DataGenerator()
    original_list, variant_list = dg.generate_clients_pair(100, fields=match_fields)

    # Вывод первых пяти клиентов из каждого списка для проверки
    print('Первые пять клиентов из оригинального списка:')
    print_table(original_list[:3])

    print('\nПервые пять клиентов из похожего списка:')
    print_table(variant_list[:3])
    print()

    profiler.enable()
    # Сопоставление клиентов
    matcher = DataMatcher(
        match_fields=['Фамилия', 'Имя', 'Отчество', 'email'],
        weights={'Фамилия': 0.3, 'Имя': 0.3, 'Отчество': 0.2, 'email': 0.1, 'length': 0.01},
        threshold=85,
        block_field='Фамилия',
        sort_before_match=False
    )
    matches, consolidated = matcher.match_and_consolidate(original_list, variant_list)

    profiler.disable()
    profiler.dump_stats("profile_data.prof")

    c = 0
    for match in matches[:5]:
        print('_' * 70)
        print(f"{' '.join(match['Запись 1']):<61} | 1.00")
        print(f"{' '.join(match['Запись 2']):<61} | {(match['Совпадение'][0] / 100):.2f}")

    print(f"\n\t\t\t\t\tОтобрано {len(matches)} записей")

    print(f"\nКонсолидировано: {len(consolidated)} записей")


    df_consolidated = pd.DataFrame(consolidated)
    if 'Фамилия' in df_consolidated.columns:
        df_consolidated = df_consolidated.sort_values(by="Фамилия", ascending=True)
    else:
        print("Столбец 'Фамилия' отсутствует в данных.")

    # pd.set_option('display.max_colwidth', 40)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)  # Отключает перенос строк
    pd.set_option('display.max_rows', None)
    print(df_consolidated)

    stats = pstats.Stats("profile_data.prof")
    stats.strip_dirs().sort_stats("cumulative").print_stats()


