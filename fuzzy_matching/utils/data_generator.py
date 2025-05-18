import random
import faker
import json
import csv
import gender_guesser.detector as gender
from enum import Enum
# from rapidfuzz.distance import Levenshtein


class Language(Enum):
    RUS = 'ru_RU'
    ENG = 'en_US'


class DataGenerator:
    """
    Генерирует фиктивные данные с возможными искажениями (ошибками) в фамилии, имени, отчестве, email и телефоне.
    
    Основные функции:
    - Генерация чистых данных с помощью библиотеки Faker
    - Внесение различных искажений в данные (дублирование букв, замена букв и т.д.)
    - Создание пар данных для тестирования алгоритмов сопоставления
    - Сохранение сгенерированных данных в форматах JSON и CSV
    
    Параметры искажений контролируются через словарь вероятностей.
    
    Параметры вероятностей искажений:
    - double_char_probability: вероятность дублирования буквы (например, "Иванов" -> "Ивванов")
    - change_char_probability: вероятность замены буквы (например, "Иванов" -> "Иваноа")
    - change_name_probability: вероятность полной замены ФИО
    - change_domain_probability: вероятность изменения домена в email
    - double_number_probability: вероятность дублирования цифры в телефоне
    - suffix_probability: вероятность добавления суффикса к ФИО
    
    Доступные языки:
    - ru: русский язык (Language.RUS)
    - en: английский язык (Language.ENG)
    
    Форматы названий полей:
    - ru: русские названия полей (Фамилия, Имя, Отчество и т.д.)
    - en: английские названия полей (LastName, FirstName, MiddleName и т.д.)
    """
    DEFAULT_PROBABILITIES = {
        'double_char_probability': 0.3,     # вероятность дублирования буквы
        'change_char_probability': 0.4,     # вероятность замены буквы
        'change_name_probability': 0.1,     # вероятность полной замены ФИО
        'change_domain_probability': 0.3,   # вероятность изменения домена в email
        'double_number_probability': 0.3,   # вероятность дублирования цифры
        'suffix_probability': 0.1           # вероятность добавления суффикса к ФИО
    }

    # Названия полей для вывода данных
    FIELD_NAMES_RU = {
        'last_name': 'Фамилия',
        'first_name': 'Имя',
        'middle_name': 'Отчество',
        'email': 'Email',
        'phone': 'Телефон',
        'gender': 'Пол'
    }
    
    # Английские названия полей
    FIELD_NAMES_EN = {
        'last_name': 'LastName',
        'first_name': 'FirstName',
        'middle_name': 'MiddleName',
        'email': 'Email',
        'phone': 'Phone',
        'gender': 'Gender'
    }

    def __init__(self,
                 language=Language.RUS,
                 probabilities=None,
                 use_patronymic_for_english=False
                 ):
        """
        Инициализирует генератор данных.
        
        :param language: язык генерируемых данных (Language.RUS или Language.ENG)
        :param probabilities: словарь вероятностей различных искажений. Поддерживаются следующие ключи:
            - double_char_probability: вероятность дублирования буквы (0.0-1.0)
            - change_char_probability: вероятность замены буквы (0.0-1.0)
            - change_name_probability: вероятность полной замены ФИО (0.0-1.0)
            - change_domain_probability: вероятность изменения домена в email (0.0-1.0)
            - double_number_probability: вероятность дублирования цифры в телефоне (0.0-1.0)
            - suffix_probability: вероятность добавления суффикса к ФИО (0.0-1.0)
        :param use_patronymic_for_english: если True, для английской локализации будет
                                         использоваться транслитерированное отчество вместо middle name
        """
        self.language = language
        self.fake = faker.Faker(self.language.value)
        self.use_patronymic_for_english = use_patronymic_for_english
        
        # Выбираем словарь названий полей в зависимости от языка
        self.FIELD_NAMES = self.FIELD_NAMES_RU if language == Language.RUS else self.FIELD_NAMES_EN

        # Устанавливаем вероятности искажений (или используем по умолчанию)
        probs = probabilities or {}
        
        # Обратная совместимость со старыми ключами
        if 'double_letter' in probs:
            probs['double_char_probability'] = probs.pop('double_letter')
        if 'typo_probability' in probs:
            probs['double_char_probability'] = probs.pop('typo_probability')
        if 'change_letter' in probs or 'swap' in probs:
            key = 'swap' if 'swap' in probs else 'change_letter'
            probs['change_char_probability'] = probs.pop(key)
        if 'character_probability' in probs:
            probs['change_char_probability'] = probs.pop('character_probability')
        if 'change_name' in probs:
            probs['change_name_probability'] = probs.pop('change_name')
        if 'change_name_domain' in probs:
            probs['change_domain_probability'] = probs.pop('change_name_domain')
        if 'double_number' in probs:
            probs['double_number_probability'] = probs.pop('double_number')
        if 'suffix_addition' in probs:
            probs['suffix_probability'] = probs.pop('suffix_addition')
        
        # Устанавливаем вероятности с учетом значений по умолчанию
        self.double_char_probability = probs.get('double_char_probability', self.DEFAULT_PROBABILITIES['double_char_probability'])
        self.change_char_probability = probs.get('change_char_probability', self.DEFAULT_PROBABILITIES['change_char_probability'])
        self.change_name_probability = probs.get('change_name_probability', self.DEFAULT_PROBABILITIES['change_name_probability'])
        self.change_domain_probability = probs.get('change_domain_probability', self.DEFAULT_PROBABILITIES['change_domain_probability'])
        self.double_number_probability = probs.get('double_number_probability', self.DEFAULT_PROBABILITIES['double_number_probability'])
        self.suffix_probability = probs.get('suffix_probability', self.DEFAULT_PROBABILITIES['suffix_probability'])

        self.gender_detector = gender.Detector()

    def doubling_letter(self, text):
        """
        Дублирует случайную букву в строке.
        
        :param text: исходный текст
        :return: текст с дублированной случайной буквой
        """
        if len(text) < 2:
            return text
        idx = random.randint(0, len(text) - 1)
        return text[:idx] + text[idx] + text[idx:]

    def changing_letter(self, text, email_flag=False):
        """
        Заменяет случайную букву на другую.
        
        :param text: исходный текст
        :param email_flag: флаг для замены буквы в email (используется латиница)
        :return: текст с замененной случайной буквой
        """
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
            # Если ФИО было полностью изменено, генерируем новый номер телефона
            return self.fake.phone_number()

        # Изменяем одну случайную цифру в номере телефона
        idx = random.randint(0, len(digits) - 1)
        digits[idx] = str(random.randint(0, 9))

        # Дополнительная ошибка с заданной вероятностью
        if random.random() < self.double_number_probability:
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
        if rnd < self.double_char_probability:
            # Дублируем букву в логине email
            return f"{self.doubling_letter(user)}@{domain}"
        elif rnd < self.double_char_probability + self.change_char_probability:
            # Заменяем букву в логине email
            return f"{self.changing_letter(user, email_flag=True)}@{domain}"
        elif rnd < self.double_char_probability + self.change_char_probability + self.change_domain_probability:
            # Изменяем букву и в логине, и в домене
            new_user = self.changing_letter(user, email_flag=True)
            new_domain = self.changing_letter(domain, email_flag=True)
            return f"{new_user}@{new_domain}"
        # todo: Добавляем случайное число к имени пользователя name += str(random.randint(10, 99))
        # Без изменений
        return email

    def _generate_middle_name_male(self):
        """
        Генерирует мужское отчество (для русского) или middle name (для английского).
        
        :return: отчество или middle name
        """
        if self.language == Language.RUS:
            # Список популярных русских мужских отчеств
            middle_names = [
                'Александрович', 'Алексеевич', 'Андреевич', 'Антонович', 'Аркадьевич',
                'Борисович', 'Валентинович', 'Васильевич', 'Викторович', 'Владимирович',
                'Вячеславович', 'Геннадьевич', 'Георгиевич', 'Григорьевич', 'Данилович',
                'Дмитриевич', 'Евгеньевич', 'Егорович', 'Иванович', 'Игоревич',
                'Ильич', 'Кириллович', 'Константинович', 'Леонидович', 'Максимович',
                'Михайлович', 'Николаевич', 'Олегович', 'Павлович', 'Петрович',
                'Романович', 'Сергеевич', 'Станиславович', 'Степанович', 'Фёдорович',
                'Юрьевич', 'Яковлевич', 'Ярославович'
            ]
            return random.choice(middle_names)
        else:
            # В английской традиции middle name - это обычно просто второе имя, не отчество
            # Можно использовать обычное мужское имя
            return self.fake.first_name_male()

    def _generate_middle_name_female(self):
        """
        Генерирует женское отчество (для русского) или middle name (для английского).
        
        :return: отчество или middle name
        """
        if self.language == Language.RUS:
            # Список популярных русских женских отчеств
            middle_names = [
                'Александровна', 'Алексеевна', 'Андреевна', 'Антоновна', 'Аркадьевна',
                'Борисовна', 'Валентиновна', 'Васильевна', 'Викторовна', 'Владимировна',
                'Вячеславовна', 'Геннадьевна', 'Георгиевна', 'Григорьевна', 'Даниловна',
                'Дмитриевна', 'Евгеньевна', 'Егоровна', 'Ивановна', 'Игоревна',
                'Ильинична', 'Кирилловна', 'Константиновна', 'Леонидовна', 'Максимовна',
                'Михайловна', 'Николаевна', 'Олеговна', 'Павловна', 'Петровна',
                'Романовна', 'Сергеевна', 'Станиславовна', 'Степановна', 'Фёдоровна',
                'Юрьевна', 'Яковлевна', 'Ярославовна'
            ]
            return random.choice(middle_names)
        else:
            # В английской традиции middle name - это обычно просто второе имя, не отчество
            # Можно использовать обычное женское имя
            return self.fake.first_name_female()

    def _get_transliterated_middle_name(self, gender='male'):
        """
        Генерирует транслитерированное отчество для тестирования транслитерации.
        Это полезно, когда нужно протестировать алгоритмы транслитерации с русского на английский.
        
        :param gender: пол ('м' или 'ж')
        :return: транслитерированное отчество
        """
        # Временно меняем язык на русский, генерируем отчество и транслитерируем
        original_language = self.language
        self.language = Language.RUS
        
        if gender == 'м':
            middle_name_ru = self._generate_middle_name_male()
        else:
            middle_name_ru = self._generate_middle_name_female()
        
        # Возвращаем исходный язык
        self.language = original_language
        
        # Простая транслитерация (можно заменить на более сложную)
        transliteration_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        }
        
        result = ''
        for char in middle_name_ru:
            result += transliteration_map.get(char, char)
        
        return result

    def vary_name(self, name, part, gender='male') -> (str, bool):
        """
        Вносит искажения в одно из слов ФИО (имя, фамилию или отчество).
        
        :param name: исходное имя
        :param part: часть ФИО ('first' - имя, 'last' - фамилия, 'middle' - отчество)
        :param gender: пол ('м' или 'ж')
        :return: кортеж (измененное имя, флаг полной замены имени)
        """
        # Определяем вероятность изменения буквы или всего имени
        rnd = random.random()
        if rnd < self.double_char_probability:
            return self.doubling_letter(name), False
        elif rnd < self.double_char_probability + self.change_char_probability:
            return self.changing_letter(name), False
        elif rnd < self.double_char_probability + self.change_char_probability + self.change_name_probability:
            # Полная замена имени через Faker или наши кастомные генераторы
            if part == 'first':
                new_name = self.fake.first_name_male() if gender == 'м' else self.fake.first_name_female()
            elif part == 'last':
                new_name = self.fake.last_name_male() if gender == 'м' else self.fake.last_name_female()
            elif part == 'middle':
                new_name = self._generate_middle_name_male() if gender == 'м' else self._generate_middle_name_female()
            else:
                new_name = name
            return new_name, True
        # Добавление суффикса
        if random.random() < self.suffix_probability:
            if self.language == Language.RUS:
                russian_suffixes = ['ов', 'ев', 'ин', 'ский', 'цкий']
                return name + random.choice(russian_suffixes), False
            else:
                english_suffixes = ['son', 'man', 'er', 'ley', 'ton', 'ford', 'field', 'wood']
                return name + random.choice(english_suffixes), False
        return name, False

    """Генерация списка записей"""
    def generate_clean_records_list(self, num_records, fields=None, use_patronymic_for_english=None):
        """
        Генерирует список записей без искажений.
        
        :param num_records: количество записей для генерации
        :param fields: список полей для генерации (если None, используются все поля)
            Поля должны соответствовать значениям из self.FIELD_NAMES, например:
            - Для русского формата: ['Фамилия', 'Имя', 'Отчество', 'Email']
            - Для английского формата: ['LastName', 'FirstName', 'MiddleName', 'Email']
            - Поле 'id' всегда добавляется автоматически
        :param use_patronymic_for_english: если указано, переопределяет настройку из конструктора
        :return: список записей
        """
        if fields is None:
            fields = list(self.FIELD_NAMES.values())
            
        # Используем параметр из аргумента, если он указан, иначе берем из конструктора
        use_patronymic = use_patronymic_for_english if use_patronymic_for_english is not None else self.use_patronymic_for_english
            
        records = []
        for i in range(num_records):
            gender = random.choice(['м', 'ж'])
            first = self.fake.first_name_male() if gender == 'м' else self.fake.first_name_female()
            last = self.fake.last_name_male() if gender == 'м' else self.fake.last_name_female()
            
            # Выбираем стратегию генерации отчества/middle name
            if self.language == Language.ENG and use_patronymic:
                # Используем транслитерированное русское отчество для английской локализации
                middle = self._get_transliterated_middle_name(gender)
            else:
                # Используем обычное отчество или middle name в зависимости от локализации
                middle = self._generate_middle_name_male() if gender == 'м' else self._generate_middle_name_female()
                
            email = self.fake.email()
            phone = self.fake.phone_number()
            record = {}
            if self.FIELD_NAMES['last_name'] in fields:
                record[self.FIELD_NAMES['last_name']] = last
            if self.FIELD_NAMES['first_name'] in fields:
                record[self.FIELD_NAMES['first_name']] = first
            if self.FIELD_NAMES['middle_name'] in fields:
                record[self.FIELD_NAMES['middle_name']] = middle
            if self.FIELD_NAMES['email'] in fields:
                record[self.FIELD_NAMES['email']] = email
            if self.FIELD_NAMES['phone'] in fields:
                record[self.FIELD_NAMES['phone']] = phone
            if self.FIELD_NAMES['gender'] in fields:
                record[self.FIELD_NAMES['gender']] = gender
            
            # ID всегда добавляется
            record['id'] = f'record_{i+1}'
            records.append(record)
        return records

    def apply_distortions(self, records, fields=None):
        """
        Применяет искажения к списку записей.
        
        :param records: исходный список записей
        :param fields: список полей, к которым будут применены искажения
        :return: искаженный список записей
        """
        if fields is None:
            fields = list(self.FIELD_NAMES.values())
        distorted_records = []
        for record in records:
            distorted_record = record.copy()
            # добавляем суффикс к id, чтобы отличить вариант
            orig_id = distorted_record['id']
            distorted_record['id'] = f"{orig_id}_v"

            # Получаем пол (если доступен), иначе используем мужской пол по умолчанию
            gender = distorted_record.get(self.FIELD_NAMES.get('gender', 'Пол'), 'м')
            new_person = False
            if self.FIELD_NAMES['last_name'] in fields:
                last_name, new_person = self.vary_name(distorted_record[self.FIELD_NAMES['last_name']], 'last', gender)
                distorted_record[self.FIELD_NAMES['last_name']] = last_name
            if self.FIELD_NAMES['first_name'] in fields:
                first_name, new_person = self.vary_name(distorted_record[self.FIELD_NAMES['first_name']], 'first', gender)
                distorted_record[self.FIELD_NAMES['first_name']] = first_name
            if self.FIELD_NAMES['middle_name'] in fields:
                middle_name, new_person = self.vary_name(distorted_record[self.FIELD_NAMES['middle_name']], 'middle', gender)
                distorted_record[self.FIELD_NAMES['middle_name']] = middle_name
            if self.FIELD_NAMES['email'] in fields:
                email = self.vary_email(distorted_record[self.FIELD_NAMES['email']], new_person)
                distorted_record[self.FIELD_NAMES['email']] = email
            if self.FIELD_NAMES['phone'] in fields:
                phone = self.vary_phone_number(distorted_record[self.FIELD_NAMES['phone']], new_person)
                distorted_record[self.FIELD_NAMES['phone']] = phone
            distorted_records.append(distorted_record)
        return distorted_records

    def generate_records_pair(self, num_records, fields=None):
        """
        Генерирует пару списков записей: оригинальный и искаженный.
        
        :param num_records: количество записей для генерации
        :param fields: список полей для генерации
            Поля должны соответствовать значениям из self.FIELD_NAMES, например:
            - Для русского формата: ['Фамилия', 'Имя', 'Отчество', 'Email']
            - Для английского формата: ['LastName', 'FirstName', 'MiddleName', 'Email']
            - Поле 'id' всегда добавляется автоматически
        :return: кортеж (список оригинальных записей, список искаженных записей)
        """
        clean_records = self.generate_clean_records_list(num_records, fields)
        distorted_records = self.apply_distortions(clean_records, fields)
        return clean_records, distorted_records

    def save_to_json(self, data, filename):
        """
        Сохраняет данные в JSON-файл.
        
        :param data: данные для сохранения
        :param filename: имя файла для сохранения
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_to_csv(self, data, filename):
        """
        Сохраняет данные в CSV-файл.
        
        :param data: данные для сохранения
        :param filename: имя файла для сохранения
        """
        if not data:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
