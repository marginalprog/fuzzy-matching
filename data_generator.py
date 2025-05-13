import random
import faker
import json
import csv
import gender_guesser.detector as gender
from enum import Enum
# from rapidfuzz.distance import Levenshtein


class Language(Enum):
    RUS = 'ru_RU',
    ENG = 'en_US'


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
            # добавляем суффикс к id, чтобы отличить вариант
            orig_id = distorted_client['id']
            distorted_client['id'] = f"{orig_id}_v"

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
