import random
import faker
from fuzzywuzzy import fuzz
import pandas as pd
from enum import Enum
from itertools import product


class NamePart(Enum):
    FIRST = "name"
    LAST = "lastname"
    MIDDLE = "middlename"


class DataGenerator:
    """Инициализация генератора фиктивных данных"""
    def __init__(self,
                 languages=None,
                 double_letter_prob=0.4,
                 change_letter_prob=0.5,
                 change_name_prob=0.1,
                 change_name_domain_prob=0.3,
                 double_number_prob=0.3
                 ):
        if languages is None:
            languages = ['ru_RU']
        self.languages = languages
        self.fake = faker.Faker(self.languages[0])
        self.double_letter_prob = double_letter_prob
        self.change_letter_prob = change_letter_prob
        self.change_name_prob = change_name_prob
        self.change_name_domain_prob = change_name_domain_prob  # вероятность изменить и имя и домен
        self.double_number_probability = double_number_prob

    def doubling_letter(self, name, probability=0.5):
        if len(name) < 2:
            return name
        name_as_list = list(name)
        index_to_double = random.randint(0, len(name_as_list) - 1)
        name_as_list.insert(index_to_double, random.choice(list(name)))
        return ''.join(name_as_list)

    def changing_letter(self, name, probability=0.5):
        if len(name) < 2:
            return name
        name_as_list = list(name)
        index_to_change = random.randint(1, len(name_as_list) - 1)
        name_as_list[index_to_change] = random.choice(list(name))
        return ''.join(name_as_list)

    """Создание вариации номера телефона"""
    def vary_phone_number(self, phone):
        # не доделано - не принимает флаг изменения человека (ф\и\о, как в почте)
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
            return f"{self.changing_letter(name)}@{domain}"
        if random_number < self.double_letter_prob + self.change_letter_prob + self.change_name_domain_prob:
            return f"{self.changing_letter(name)}@{self.changing_letter(domain)}"
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
            return self.changing_letter(name), flag_change_full_name
        elif random_number < self.double_letter_prob + self.change_letter_prob + self.change_name_prob:
            flag_change_full_name = True
            # Меняем Ф\И\О целиком
            if part == NamePart.FIRST:
                return self.fake.first_name(), flag_change_full_name
            if part == NamePart.LAST:
                return self.fake.last_name(), flag_change_full_name
            if part == NamePart.MIDDLE:
                return self.fake.middle_name(), flag_change_full_name

        if random.choice([True, False]):
            return name + random.choice(['ий', 'ов', 'ев', 'ский', 'цкий']), flag_change_full_name
        return name, flag_change_full_name

    """Генерация списка клиентов"""
    def generate_clients_list(self, num_clients):
        clients_list = []
        for _ in range(num_clients):
            name = self.fake.first_name()
            surname = self.fake.last_name()
            patronymic = self.fake.middle_name()
            # phone = fake.phone_number()
            email = self.fake.email()
            # address = fake.address().replace('\n', ', ')
            clients_list.append({
                'Фамилия': surname,
                'Имя': name,
                'Отчество': patronymic,
                # 'Номер телефона': phone,
                'Адрес почты': email,
                # 'Адрес': address
            })
        return clients_list

    """Функция для сопоставления клиентов из двух списков"""
    def match_clients(self, list1, list2):
        remaining_customers_1, remaining_customers_2 = list1.copy(), list2.copy()
        table_matched_clients = []
        returned_clients = []
        for client1 in list1:
            # Собираем данные для сопоставления
            full_name1 = f"{client1['Фамилия']} {client1['Имя']} {client1['Отчество']}"
            email1 = client1['Адрес почты']
            # phone1 = client1['Номер телефона']

            # Сопоставляем каждое поле и считаем среднее значение совпадения
            for client2 in list2:
                full_name2 = f"{client2['Фамилия']} {client2['Имя']} {client2['Отчество']}"
                email2 = client2['Адрес почты']
                # phone2 = client2['Номер телефона']

                # Вычисляем сходство для каждого поля
                name_similarity = fuzz.token_sort_ratio(full_name1, full_name2)
                email_similarity = fuzz.token_sort_ratio(email1, email2)
                # phone_similarity = fuzz.token_sort_ratio(phone1, phone2)

                # Считаем среднее значение совпадения
                average_similarity = (name_similarity + email_similarity) / 2  # phone_similarity

                # Если среднее сходство выше порога, добавляем в результаты
                if average_similarity > 85:
                    table_matched_clients.append({
                        'Запись 1': [full_name1, email1],
                        'Запись 2': [full_name2, email2],
                        'Совпадение': [name_similarity, email_similarity]  # phone_similarity
                    })
                    returned_clients.append(client1)
                    remaining_customers_1.remove(client1)
                    remaining_customers_2.remove(client2)
                    break
        consolidated_clients = returned_clients + remaining_customers_1 + remaining_customers_2
        return table_matched_clients, consolidated_clients

if __name__ == "__main__":
    data = DataGenerator(["ru_RU"])

    # Создание основного списка клиентов
    clients_list_original = data.generate_clients_list(100)

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

    df_clients_original = pd.DataFrame(clients_list_original)
    print(df_clients_original.head(5))

    print('\nПервые пять клиентов из похожего списка:')
    df_clients_variant = pd.DataFrame(clients_list_variant)
    print(df_clients_variant.head(5))

    print()

    # Сопоставление клиентов
    matches, consolidated_data = data.match_clients(clients_list_original, clients_list_variant)

    c = 0
    for match in matches:
        print(70 * '_')
        print(
            f"{' '.join(match['Запись 1']):<61} | 1.00\n{' '.join(match['Запись 2']):<61} | {sum(match['Совпадение']) / (100 * len(match['Совпадение'])):.2f}")
        c += 1
        if c > 5:
            break

    print(f"\n\t\t\t\t\tОтобрано {len(matches)} записей")

    print(f"\nКонсолидация будет содержать {len(consolidated_data)} записей")

    df_consolidated_data = pd.DataFrame(consolidated_data)

    pd.set_option('display.max_colwidth', 40)
    print(df_consolidated_data.head(3))
    print('\t\t\t\t.............................')
    print(df_consolidated_data.tail(3))