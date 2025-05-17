"""
Пример использования предметно-ориентированных алгоритмов 
для разных типов данных (персональные данные, товары, компании).
"""

from prettytable import PrettyTable
import json
import os

from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig, 
    FuzzyAlgorithm, DomainSpecificAlgorithm
)
from fuzzy_matching.utils.data_generator import DataGenerator, Language


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


def display_matches(matches, limit=5):
    """
    Выводит результаты совпадений в виде таблицы PrettyTable.
    
    :param matches: список найденных совпадений
    :param limit: максимальное количество строк для отображения (по умолчанию 5)
    """
    # Создаем таблицу и задаем заголовки колонок
    table = PrettyTable()
    table.field_names = ["Запись 1", "Запись 2", "Совпадение"]

    # Добавляем строки в таблицу
    for match in matches[:limit]:
        rec1 = " ".join(match["Запись 1"])
        rec2 = " ".join(match["Запись 2"])
        score = f"{match['Совпадение'][0]:.2f}"
        table.add_row([rec1, rec2, score])

    # Опции выравнивания
    table.align["Запись 1"] = "l"
    table.align["Запись 2"] = "l"
    table.align["Совпадение"] = "r"

    # Вывод
    print(f"\nОтобрано: {len(matches)} записей\n")
    print(table)


def load_russian_employees():
    """Загружает тестовые данные о сотрудниках из JSON файла."""
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'russian_employees.json')
    
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    return data


def generate_person_data():
    """Генерирует тестовые данные для людей с различными вариациями."""
    # Базовые данные
    original_data = [
        {
            'id': 'p1',
            'Фамилия': 'Иванов',
            'Имя': 'Иван',
            'Отчество': 'Иванович',
            'Адрес': 'г. Москва, ул. Ленина, д. 10, кв. 5',
            'Телефон': '+7 (495) 123-45-67',
            'Email': 'ivanov@example.com'
        },
        {
            'id': 'p2',
            'Фамилия': 'Петров-Сидоров',
            'Имя': 'Александр',
            'Отчество': 'Михайлович',
            'Адрес': 'Санкт-Петербург, Невский проспект 15-2',
            'Телефон': '+7 (812) 987-65-43',
            'Email': 'petrov@example.ru'
        },
        {
            'id': 'p3',
            'Фамилия': 'Смирнова',
            'Имя': 'Екатерина',
            'Отчество': 'Владимировна',
            'Адрес': 'г. Новосибирск, проспект Маркса, дом 20, квартира 15',
            'Телефон': '+7 (383) 456-78-90',
            'Email': 'smirnova@mail.ru'
        },
        {
            'id': 'p4',
            'Фамилия': 'Кузнецов',
            'Имя': 'Дмитрий',
            'Отчество': 'Сергеевич',
            'Адрес': 'Екатеринбург, ул. Мира, д. 100, кв. 42',
            'Телефон': '+7 (343) 234-56-78',
            'Email': 'kuznetsov@yandex.ru'
        },
        {
            'id': 'p5',
            'Фамилия': 'Johnson',
            'Имя': 'John',
            'Отчество': 'Michael',
            'Адрес': '123 Main St, New York, NY',
            'Телефон': '+1 (212) 555-1234',
            'Email': 'johnson@gmail.com'
        }
    ]
    
    # Варианты с различными изменениями
    variant_data = [
        {
            'id': 'v1',
            'Фамилия': 'Иванов',
            'Имя': 'Ваня',  # Уменьшительное имя
            'Отчество': 'Иванович',
            'Адрес': 'Москва, Ленина 10-5',  # Сокращенный адрес
            'Телефон': '84951234567',  # Другой формат телефона
            'Email': 'i.ivanov@example.com'  # Измененный email
        },
        {
            'id': 'v2',
            'Фамилия': 'Сидоров-Петров',  # Изменен порядок в двойной фамилии
            'Имя': 'Саша',  # Уменьшительное имя
            'Отчество': 'Михайлович',
            'Адрес': 'проспект Невский, дом 15, квартира 2, г. Санкт-Петербург',  # Изменен порядок в адресе
            'Телефон': '+78129876543',
            'Email': 'a.petrov@example.ru'
        },
        {
            'id': 'v3',
            'Фамилия': 'Смирнова',
            'Имя': 'Катя',  # Уменьшительное имя
            'Отчество': 'Владимировна',
            'Адрес': 'проспект Маркса 20, кв 15, Новосибирск',  # Измененный порядок
            'Телефон': '8 (383) 456-78-90',
            'Email': 'e.smirnova@mail.ru'
        },
        {
            'id': 'v4',
            'Фамилия': 'Кузнецов',
            'Имя': 'Дмитрий',
            'Отчество': 'Сергеич',  # Разговорная форма отчества
            'Адрес': 'ул. Мира 100-42, гор. Екатеринбург',  # Измененный формат
            'Телефон': '8-343-234-5678',  # Другой формат
            'Email': 'd_kuznetsov@yandex.ru'
        },
        {
            'id': 'v5',
            'Фамилия': 'Johnson',
            'Имя': 'Johnny',  # Уменьшительная форма
            'Отчество': 'Mike',  # Сокращение
            'Адрес': 'New York, 123 Main Street, NY',  # Изменен порядок
            'Телефон': '1-212-555-1234',  # Другой формат
            'Email': 'john.johnson@gmail.com'  # Измененный email
        }
    ]
    
    return original_data, variant_data


def generate_product_data():
    """Генерирует тестовые данные для товаров с различными вариациями."""
    # Оригинальные данные о товарах
    original_data = [
        {
            'id': 'prod1',
            'Название': 'Смартфон Samsung Galaxy S21 Ultra',
            'Артикул': 'SM-G998B',
            'Описание': 'Флагманский смартфон с 6.8" Dynamic AMOLED 2X экраном, 108МП камерой',
            'Бренд': 'Samsung',
            'Категория': 'Мобильные телефоны и смартфоны'
        },
        {
            'id': 'prod2',
            'Название': 'Ноутбук Apple MacBook Pro 16"',
            'Артикул': 'MVVJ2RU/A',
            'Описание': 'Профессиональный ноутбук с экраном Retina 16", процессор Intel Core i9',
            'Бренд': 'Apple',
            'Категория': 'Ноутбуки и компьютеры'
        },
        {
            'id': 'prod3',
            'Название': 'Наушники Sony WH-1000XM4',
            'Артикул': 'WH1000XM4B',
            'Описание': 'Беспроводные накладные наушники с активным шумоподавлением',
            'Бренд': 'Sony',
            'Категория': 'Аудиотехника'
        },
        {
            'id': 'prod4',
            'Название': 'Телевизор LG OLED65C1',
            'Артикул': 'OLED65C1RLA',
            'Описание': '65" OLED телевизор с разрешением 4K, Smart TV на webOS',
            'Бренд': 'LG',
            'Категория': 'Телевизоры и видеотехника'
        },
        {
            'id': 'prod5',
            'Название': 'Кофемашина De\'Longhi Magnifica S',
            'Артикул': 'ECAM22.110.B',
            'Описание': 'Автоматическая кофемашина с капучинатором',
            'Бренд': 'De\'Longhi',
            'Категория': 'Кухонная техника'
        }
    ]
    
    # Варианты с различными изменениями
    variant_data = [
        {
            'id': 'var1',
            'Название': 'Samsung Galaxy S21 Ultra смартфон',  # Изменен порядок слов
            'Артикул': 'SM-G998B/DS',  # Небольшое изменение в артикуле
            'Описание': 'Смартфон с камерой 108МП, 6.8" Dynamic AMOLED 2X экраном',  # Изменен порядок в описании
            'Бренд': 'Samsung Electronics',  # Расширенное название бренда
            'Категория': 'Смартфоны'  # Сокращенная категория
        },
        {
            'id': 'var2',
            'Название': 'Apple MacBook Pro (16 дюймов)',  # Другой формат названия
            'Артикул': 'MVVJ2',  # Сокращенный артикул
            'Описание': 'Ноутбук с Intel Core i9, экраном Retina 16", для профессиональной работы',  # Изменен порядок
            'Бренд': 'Apple Inc.',  # Полное название
            'Категория': 'Ноутбуки'  # Сокращенная категория
        },
        {
            'id': 'var3',
            'Название': 'WH-1000XM4 наушники Sony',  # Изменен порядок
            'Артикул': 'WH-1000XM4',  # Небольшое изменение в формате
            'Описание': 'Накладные беспроводные наушники Sony с технологией активного шумоподавления',  # Изменен порядок и добавлен бренд
            'Бренд': 'SONY',  # Все заглавные
            'Категория': 'Наушники'  # Более узкая категория
        },
        {
            'id': 'var4',
            'Название': 'OLED Телевизор LG 65C1',  # Изменен порядок
            'Артикул': 'OLED65C1',  # Сокращенный артикул
            'Описание': 'Smart TV с webOS, OLED-экран 65 дюймов, разрешение 4K',  # Изменен порядок
            'Бренд': 'LG Electronics',  # Полное название
            'Категория': 'Телевизоры'  # Сокращенная категория
        },
        {
            'id': 'var5',
            'Название': 'Magnifica S кофемашина De Longhi',  # Изменен порядок и убран апостроф
            'Артикул': 'ECAM 22.110.B',  # Добавлен пробел
            'Описание': 'Кофемашина автоматическая с возможностью приготовления капучино',  # Перефразировано
            'Бренд': 'DeLonghi',  # Без апострофа и слитно
            'Категория': 'Кофемашины и кофеварки'  # Более детальная категория
        }
    ]
    
    return original_data, variant_data


def generate_company_data():
    """Генерирует тестовые данные для компаний с различными вариациями."""
    # Оригинальные данные о компаниях
    original_data = [
        {
            'id': 'comp1',
            'Название': 'ООО "Газпром"',
            'Юр_название': 'Общество с ограниченной ответственностью "Газпром"',
            'ИНН': '7736050003',
            'Адрес': 'г. Москва, ул. Наметкина, д. 16',
            'Телефон': '+7 (495) 719-30-01'
        },
        {
            'id': 'comp2',
            'Название': 'ПАО "Сбербанк России"',
            'Юр_название': 'Публичное акционерное общество "Сбербанк России"',
            'ИНН': '7707083893',
            'Адрес': 'г. Москва, ул. Вавилова, д. 19',
            'Телефон': '+7 (495) 500-55-50'
        },
        {
            'id': 'comp3',
            'Название': 'АО "Альфа-Банк"',
            'Юр_название': 'Акционерное общество "Альфа-Банк"',
            'ИНН': '7728168971',
            'Адрес': 'г. Москва, ул. Каланчевская, д. 27',
            'Телефон': '+7 (495) 788-88-78'
        },
        {
            'id': 'comp4',
            'Название': 'ООО "Яндекс"',
            'Юр_название': 'Общество с ограниченной ответственностью "Яндекс"',
            'ИНН': '7736207543',
            'Адрес': 'г. Москва, ул. Льва Толстого, д. 16',
            'Телефон': '+7 (495) 739-70-00'
        },
        {
            'id': 'comp5',
            'Название': 'Apple Inc.',
            'Юр_название': 'Apple Incorporated',
            'ИНН': '000000000', # Условный ИНН для примера
            'Адрес': 'One Apple Park Way, Cupertino, California, United States',
            'Телефон': '+1 (408) 996-1010'
        }
    ]
    
    # Варианты с различными изменениями
    variant_data = [
        {
            'id': 'var1',
            'Название': 'Газпром ООО',  # Изменен порядок
            'Юр_название': 'ООО Газпром',  # Сокращенное юр. название
            'ИНН': '7736050003',
            'Адрес': 'Москва, Наметкина 16',  # Сокращенный адрес
            'Телефон': '84957193001'  # Измененный формат
        },
        {
            'id': 'var2',
            'Название': 'Сбербанк',  # Сокращенное название
            'Юр_название': 'ПАО Сбербанк',  # Сокращенное юр. название
            'ИНН': '7707083893',
            'Адрес': 'ул. Вавилова 19, Москва',  # Измененный порядок
            'Телефон': '8 800 555 55 50'  # Другой телефон (горячая линия)
        },
        {
            'id': 'var3',
            'Название': 'Альфа-Банк',  # Без указания формы собственности
            'Юр_название': 'АО Альфа-Банк',  # Без кавычек
            'ИНН': '7728168971',
            'Адрес': 'Каланчевская улица, дом 27, город Москва',  # Изменен порядок и формат
            'Телефон': '8-800-200-00-00'  # Другой телефон (горячая линия)
        },
        {
            'id': 'var4',
            'Название': 'Яндекс',  # Без указания формы собственности
            'Юр_название': 'ООО Яндекс',  # Без кавычек
            'ИНН': '7736207543',
            'Адрес': 'Москва, улица Льва Толстого, дом 16',  # Изменен формат
            'Телефон': '495-739-7000'  # Измененный формат
        },
        {
            'id': 'var5',
            'Название': 'Apple',  # Сокращенное название
            'Юр_название': 'Apple Inc',  # Без точки
            'ИНН': '0000000000',  # Лишний ноль
            'Адрес': 'Cupertino, CA, Apple Park Way 1',  # Измененный порядок и формат
            'Телефон': '1-408-996-1010'  # Измененный формат
        }
    ]
    
    return original_data, variant_data


def run_domain_comparison(domain_name, data1, data2, field_type_mapping):
    """
    Запускает сравнение с использованием стандартного и предметно-ориентированного алгоритмов.
    
    :param domain_name: название предметной области
    :param data1: первый набор данных
    :param data2: второй набор данных
    :param field_type_mapping: словарь соответствия полей типам для предметной области
    """
    print(f"\n=== СРАВНЕНИЕ АЛГОРИТМОВ ДЛЯ ПРЕДМЕТНОЙ ОБЛАСТИ: {domain_name} ===\n")
    
    # Вывод исходных данных
    print("\nИсходные данные:")
    print("\nПервый набор данных:")
    print_table(data1)
    print("\nВторой набор данных:")
    print_table(data2)
    
    # Получаем поля из первой записи
    fields = list(data1[0].keys())
    fields.remove('id')  # Исключаем id из полей для сопоставления
    
    # Создаем конфигурации полей с одинаковыми весами
    field_weight = 1.0 / len(fields)
    
    # Базовая конфигурация полей (без учета типов)
    base_fields = []
    domain_fields = []
    
    for field in fields:
        # Для базовой конфигурации просто используем фиксированный алгоритм
        base_fields.append(MatchFieldConfig(
            field=field,
            weight=field_weight,
            transliterate=False
        ))
        
        # Для предметно-ориентированной конфигурации указываем типы полей
        field_type = field_type_mapping.get(field)
        domain_fields.append(MatchFieldConfig(
            field=field,
            weight=field_weight,
            transliterate=False,
            field_type=field_type
        ))
    
    # Создаем базовую конфигурацию с общим алгоритмом
    base_config = MatchConfig(
        fields=base_fields,
        threshold=0.6,  # Используем более низкий порог для демонстрации
        fuzzy_algorithm=FuzzyAlgorithm.RATIO
    )
    
    # Выбираем подходящую предметную область
    domain_algo = None
    if domain_name == 'Персональные данные':
        domain_algo = DomainSpecificAlgorithm.PERSON_DATA
    elif domain_name == 'Товары':
        domain_algo = DomainSpecificAlgorithm.PRODUCT_DATA
    elif domain_name == 'Компании':
        domain_algo = DomainSpecificAlgorithm.COMPANY_DATA
    
    # Создаем предметно-ориентированную конфигурацию
    domain_config = MatchConfig(
        fields=domain_fields,
        threshold=0.6,  # Тот же порог
        domain_algorithm=domain_algo
    )
    
    # Запускаем сопоставление с базовой конфигурацией
    base_matcher = DataMatcher(config=base_config)
    base_matches, _ = base_matcher.match_and_consolidate(data1, data2)
    
    # Запускаем сопоставление с предметно-ориентированной конфигурацией
    domain_matcher = DataMatcher(config=domain_config)
    domain_matches, _ = domain_matcher.match_and_consolidate(data1, data2)
    
    # Выводим результаты
    print(f"\n=== РЕЗУЛЬТАТЫ СОПОСТАВЛЕНИЯ ДЛЯ {domain_name} ===")
    
    print("\nОбщий алгоритм (RATIO):")
    display_matches(base_matches)
    
    print(f"\nПредметно-ориентированный алгоритм ({domain_algo.name}):")
    display_matches(domain_matches)
    
    # Сравнительная таблица
    comparison = []
    for i, record1 in enumerate(data1):
        row = {'ID': record1['id']}
        
        # Добавляем строковое представление записи
        record_str = " ".join(str(record1.get(f, "")) for f in fields)
        row['Запись'] = record_str[:50] + "..." if len(record_str) > 50 else record_str
        
        # Базовый алгоритм
        base_match = next((m for m in base_matches if m['ID 1'] == record1['id']), None)
        row['Базовый'] = f"{base_match['Совпадение'][0]:.2f}" if base_match else "-"
        
        # Предметно-ориентированный алгоритм
        domain_match = next((m for m in domain_matches if m['ID 1'] == record1['id']), None)
        row['Предметный'] = f"{domain_match['Совпадение'][0]:.2f}" if domain_match else "-"
        
        comparison.append(row)
    
    print("\n=== СРАВНИТЕЛЬНАЯ ТАБЛИЦА ===")
    print_table(comparison)
    
    # Анализ результатов
    base_count = len(base_matches)
    domain_count = len(domain_matches)
    
    print("\n=== АНАЛИЗ РЕЗУЛЬТАТОВ ===")
    print(f"Базовый алгоритм: найдено {base_count} совпадений")
    print(f"Предметный алгоритм: найдено {domain_count} совпадений")
    
    if domain_count > base_count:
        print(f"Предметный алгоритм обнаружил на {domain_count - base_count} совпадений БОЛЬШЕ")
    elif base_count > domain_count:
        print(f"Базовый алгоритм обнаружил на {base_count - domain_count} совпадений БОЛЬШЕ")
    else:
        print("Оба алгоритма нашли одинаковое количество совпадений")
    
    # Анализ качества совпадений
    base_avg = sum(m['Совпадение'][0] for m in base_matches) / len(base_matches) if base_matches else 0
    domain_avg = sum(m['Совпадение'][0] for m in domain_matches) / len(domain_matches) if domain_matches else 0
    
    print(f"Средняя схожесть для базового алгоритма: {base_avg:.2f}")
    print(f"Средняя схожесть для предметного алгоритма: {domain_avg:.2f}")
    
    # Сравнение результатов
    better = "предметный" if domain_avg > base_avg else "базовый"
    diff_percent = abs(domain_avg - base_avg) / max(base_avg, domain_avg) * 100
    
    print(f"Для данной предметной области {better} алгоритм показал лучший результат.")
    print(f"Разница в средней схожести: {diff_percent:.1f}%")


def main():
    """
    Основная функция примера.
    """
    print("\n===== ДЕМОНСТРАЦИЯ ИСПОЛЬЗОВАНИЯ ПРЕДМЕТНО-ОРИЕНТИРОВАННЫХ АЛГОРИТМОВ =====\n")
    
    # 1. Персональные данные
    person_data1, person_data2 = generate_person_data()
    person_field_mapping = {
        'Фамилия': 'surname',
        'Имя': 'name',
        'Отчество': 'patronymic',
        'Адрес': 'address',
        'Телефон': 'phone',
        'Email': 'email'
    }
    
    run_domain_comparison('Персональные данные', person_data1, person_data2, person_field_mapping)
    
    # 2. Данные о товарах
    product_data1, product_data2 = generate_product_data()
    product_field_mapping = {
        'Название': 'name',
        'Артикул': 'sku',
        'Описание': 'description',
        'Бренд': 'brand',
        'Категория': 'category'
    }
    
    run_domain_comparison('Товары', product_data1, product_data2, product_field_mapping)
    
    # 3. Данные о компаниях
    company_data1, company_data2 = generate_company_data()
    company_field_mapping = {
        'Название': 'name',
        'Юр_название': 'legal_name',
        'ИНН': 'inn',
        'Адрес': 'address',
        'Телефон': 'phone'
    }
    
    run_domain_comparison('Компании', company_data1, company_data2, company_field_mapping)
    
    print("\n===== ЗАВЕРШЕНИЕ ДЕМОНСТРАЦИИ ПРЕДМЕТНО-ОРИЕНТИРОВАННЫХ АЛГОРИТМОВ =====\n")


if __name__ == "__main__":
    main() 