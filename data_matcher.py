import re
import json
import csv
from typing import Optional

from rapidfuzz import fuzz
from collections import defaultdict

from match_config_classes import MatchConfig


class DataMatcher:
    """
    Класс для загрузки данных из CSV/JSON, маппинга полей для матчинга,
    выполнения фаззи-сопоставления (RapidFuzz) и консолидации похожих записей.
    
    Основные функции:
    - Загрузка данных из разных источников
    - Блокировка данных для эффективного сопоставления
    - Фаззи-сопоставление полей с учетом весов
    - Консолидация совпадающих записей
    - Сохранение результатов в разных форматах
    """
    def __init__(self, config: MatchConfig = None):
        """
        Инициализирует экземпляр класса DataMatcher.
        
        :param config: объект конфигурации MatchConfig, содержащий настройки для сопоставления
        """
        # Поля для блокировки (первый символ) и дополнительные поля группировки
        self.block_field = config.block_field
        self.group_fields = config.group_fields or []
        self.sort_before_match = config.sort_before_match
        # Поля для фаззи-матчинга
        self.match_fields = [f.field for f in config.fields]
        self.weights = {f.field: f.weight for f in config.fields}
        self.weights['length'] = config.length_weight
        self.threshold = config.threshold

    def load_from_csv(self, filename, name_fields):
        """
        Загружает данные из CSV и мапит колонки в ключи записи согласно field_mapping.
        
        :param filename: путь к CSV-файлу
        :param name_fields: словарь соответствия имен столбцов в файле именам полей в записи
        :return: список записей в виде словарей
        """
        records = []
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {}
                for col_name, target_key in name_fields.items():
                    val = row.get(col_name, '').strip()
                    # Если уже есть поле с таким ключом, склеиваем через пробел
                    if target_key in record and record[target_key]:
                        record[target_key] = f"{record[target_key]} {val}"
                    else:
                        record[target_key] = val
                records.append(record)
        return records

    def load_from_json(self, filename, name_fields):
        """
        Загружает данные из JSON и мапит ключи из name_fields.
        
        :param filename: путь к JSON-файлу (список объектов)
        :param name_fields: словарь соответствия имен полей в JSON-объекте именам полей в записи
        :return: список записей в виде словарей
        """
        with open(filename, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        records = []
        for obj in raw:
            record = {}
            for orig_key, target_key in name_fields.items():
                val = str(obj.get(orig_key, '')).strip()
                if target_key in record and record[target_key]:
                    record[target_key] = f"{record[target_key]} {val}"
                else:
                    record[target_key] = val
            records.append(record)
        return records

    def save_matches_to_json(self, matches, filename):
        """
        Сохраняет список совпадений в JSON-файл.
        
        :param matches: список совпадений для сохранения
        :param filename: имя файла для сохранения
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=4)

    def save_matches_to_csv(self, matches, filename):
        """
        Сохраняет список совпадений в CSV-файл.
        
        :param matches: список совпадений для сохранения
        :param filename: имя файла для сохранения
        """
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
        """
        Сохраняет список консолидированных записей в JSON-файл.
        
        :param consolidated: список консолидированных записей
        :param filename: имя файла для сохранения
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=4)

    def save_consolidated_to_csv(self, consolidated, filename):
        """
        Сохраняет список консолидированных записей в CSV-файл.
        
        :param consolidated: список консолидированных записей
        :param filename: имя файла для сохранения
        """
        if not consolidated:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=consolidated[0].keys())
            writer.writeheader()
            writer.writerows(consolidated)

    @staticmethod
    def _sort_data(clients, sort_keys):
        """
        Сортирует входные данные по указанным ключам.
        
        :param clients: список записей для сортировки
        :param sort_keys: список ключей для сортировки
        :return: отсортированный список записей
        """
        return sorted(clients, key=lambda x: tuple(x.get(k, '') for k in sort_keys))

    @staticmethod
    def _weighted_average(values, weights):
        """
        Вычисляет взвешенное среднее значение для набора значений.
        
        :param values: словарь значений
        :param weights: словарь весов для каждого значения
        :return: взвешенное среднее значение
        """
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
        """
        Выполняет сопоставление двух списков записей и консолидирует результаты.
        
        :param list1: первый список записей для сопоставления
        :param list2: второй список записей для сопоставления
        :return: кортеж (список совпадений, список консолидированных записей)
        """
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

                    similarity = self._weighted_average(values, self.weights)/100

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
        unmatched1 = [c for c in list1 if c['id'] not in matched_1]
        unmatched2 = [c for c in list2 if c['id'] not in matched_2]
        consolidated.extend(unmatched1 + unmatched2)

        return matches, consolidated
