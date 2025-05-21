#!/usr/bin/env python
"""
Скрипт для генерации тестовых данных с контролируемыми искажениями.
Генерирует пары записей (оригинал и исказженная версия) с заданным уровнем искажений.
"""

import json
import os
import random
import string

# Создаем директорию для данных, если ее нет
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(data_dir, exist_ok=True)

def generate_person_data(count=5):
    """
    Генерирует список записей для тестирования
    
    :param count: количество записей
    :return: список словарей с данными
    """
    first_names = [
        "Иван", "Александр", "Михаил", "Дмитрий", "Сергей", 
        "Анна", "Елена", "Мария", "Ольга", "Татьяна"
    ]
    
    last_names = [
        "Иванов", "Смирнов", "Петров", "Кузнецов", "Соколов",
        "Иванова", "Смирнова", "Петрова", "Кузнецова", "Соколова"
    ]
    
    middle_names = [
        "Иванович", "Александрович", "Михайлович", "Дмитриевич", "Сергеевич",
        "Ивановна", "Александровна", "Михайловна", "Дмитриевна", "Сергеевна"
    ]
    
    records = []
    for i in range(count):
        gender_idx = random.randint(0, 1)  # 0 - мужской, 1 - женский
        record = {
            "id": f"record_{i+1}",
            "Фамилия": last_names[i % 5 + gender_idx * 5],
            "Имя": first_names[i % 5 + gender_idx * 5],
            "Отчество": middle_names[i % 5 + gender_idx * 5],
            "Телефон": f"+7 {random.randint(900, 999)} {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}",
            "email": f"user{i+1}@example.com",
            "Пол": "м" if gender_idx == 0 else "ж"
        }
        records.append(record)
    
    return records

def apply_slight_distortion(text):
    """
    Вносит небольшие искажения в текст
    
    :param text: исходный текст
    :return: искаженный текст
    """
    if not text or len(text) < 3:
        return text
    
    chars = list(text)
    
    # Выбираем один из способов искажения
    distortion_type = random.randint(0, 3)
    
    if distortion_type == 0:
        # Заменяем одну случайную букву
        pos = random.randint(1, len(chars) - 2)
        chars[pos] = random.choice(string.ascii_lowercase if chars[pos].islower() else string.ascii_uppercase)
    elif distortion_type == 1:
        # Добавляем одну лишнюю букву
        pos = random.randint(1, len(chars) - 1)
        chars.insert(pos, chars[pos])
    elif distortion_type == 2:
        # Меняем местами две соседние буквы
        pos = random.randint(1, len(chars) - 2)
        chars[pos], chars[pos+1] = chars[pos+1], chars[pos]
    else:
        # Пропускаем одну букву
        pos = random.randint(1, len(chars) - 2)
        chars.pop(pos)
    
    return ''.join(chars)

def create_distorted_data(records):
    """
    Создает искаженные версии записей
    
    :param records: исходные записи
    :return: список искаженных записей
    """
    distorted_records = []
    
    for record in records:
        distorted_record = record.copy()
        distorted_record["id"] = record["id"] + "_v"
        
        # Искажаем ФИО и контактные данные
        distorted_record["Фамилия"] = apply_slight_distortion(record["Фамилия"])
        distorted_record["Имя"] = apply_slight_distortion(record["Имя"])
        distorted_record["Отчество"] = apply_slight_distortion(record["Отчество"])
        
        # В 20% случаев искажаем телефон
        if random.random() < 0.2:
            if "Телефон" in record:
                phone = record["Телефон"]
                distorted_phone = list(phone)
                pos = random.randint(4, len(phone) - 1)
                if phone[pos].isdigit():
                    distorted_phone[pos] = str(random.randint(0, 9))
                distorted_record["Телефон"] = ''.join(distorted_phone)
        
        # В 20% случаев искажаем email
        if random.random() < 0.2:
            if "email" in record:
                email = record["email"]
                username, domain = email.split('@')
                distorted_username = apply_slight_distortion(username)
                distorted_record["email"] = f"{distorted_username}@{domain}"
        
        distorted_records.append(distorted_record)
    
    return distorted_records

def main():
    # Генерируем оригинальные записи
    original_records = generate_person_data(10)
    
    # Создаем искаженные версии
    distorted_records = create_distorted_data(original_records)
    
    # Сохраняем в файлы
    original_file = os.path.join(data_dir, 'simple_original.json')
    distorted_file = os.path.join(data_dir, 'simple_variant.json')
    
    with open(original_file, 'w', encoding='utf-8') as f:
        json.dump(original_records, f, ensure_ascii=False, indent=2)
    
    with open(distorted_file, 'w', encoding='utf-8') as f:
        json.dump(distorted_records, f, ensure_ascii=False, indent=2)
    
    print(f"Сгенерировано {len(original_records)} оригинальных и {len(distorted_records)} искаженных записей")
    print(f"Данные сохранены в:\n- {original_file}\n- {distorted_file}")
    
    # Выводим пример пары записей
    print("\nПример оригинальной записи:")
    print(json.dumps(original_records[0], ensure_ascii=False, indent=2))
    print("\nПример искаженной записи:")
    print(json.dumps(distorted_records[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main() 