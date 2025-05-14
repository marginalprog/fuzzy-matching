import re
import json
import csv
from typing import Optional, List, Dict, Tuple, Any

from rapidfuzz import fuzz
from collections import defaultdict

from fuzzy_matching.core.match_config_classes import MatchConfig, TransliterationConfig
import fuzzy_matching.utils.transliteration_utils as translit


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
        
        # Настройки транслитерации
        self.transliteration = config.transliteration
        self.transliterate_fields = {f.field: f.transliterate for f in config.fields}
        
        # Если включена транслитерация, получаем соответствующий стандарт
        if self.transliteration.enabled:
            self.transliteration_standard = translit.get_standard_by_name(
                self.transliteration.standard
            )
        else:
            self.transliteration_standard = None

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
    
    def _process_transliteration(self, value1, value2, field):
        """
        Обрабатывает транслитерацию для двух значений поля.
        
        :param value1: первое значение
        :param value2: второе значение
        :param field: имя поля
        :return: кортеж (обработанное_значение1, обработанное_значение2, коэффициент_схожести)
        """
        if not self.transliteration.enabled or not self.transliterate_fields.get(field, False):
            # Если транслитерация отключена или не нужна для этого поля
            return value1, value2, fuzz.token_sort_ratio(value1, value2)
        
        # Определяем язык каждого значения
        lang1 = translit.detect_language(value1)
        lang2 = translit.detect_language(value2)
        
        # Нормализуем имена, если настроено
        if self.transliteration.normalize_names:
            if lang1 == 'ru':
                value1 = translit.normalize_name_ru(value1)
            elif lang1 == 'en':
                value1 = translit.normalize_name_en(value1)
                
            if lang2 == 'ru':
                value2 = translit.normalize_name_ru(value2)
            elif lang2 == 'en':
                value2 = translit.normalize_name_en(value2)
        
        # Определяем наилучший вариант сопоставления
        similarity_original = fuzz.token_sort_ratio(value1, value2)
        
        # Русский --> Английский
        if lang1 == 'ru' and lang2 == 'en':
            value1_trans = translit.transliterate_ru_to_en(value1, self.transliteration_standard)
            similarity_trans = fuzz.token_sort_ratio(value1_trans, value2)
            
            if similarity_trans > similarity_original:
                return value1_trans, value2, similarity_trans
        
        # Английский --> Русский
        elif lang1 == 'en' and lang2 == 'ru':
            value1_trans = translit.transliterate_en_to_ru(value1, self.transliteration_standard)
            similarity_trans = fuzz.token_sort_ratio(value1_trans, value2)
            
            if similarity_trans > similarity_original:
                return value1_trans, value2, similarity_trans
        
        # Оба русские или оба английские - транслитерация не нужна
        return value1, value2, similarity_original
            
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
                            if self.transliteration.enabled and self.transliterate_fields.get(field, False):
                                # Применяем транслитерацию с учетом языка
                                _, _, similarity = self._process_transliteration(v1, v2, field)
                                values[field] = similarity
                            else:
                                # Обычное сопоставление без транслитерации
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
    
    def translate_data(self, data_list, target_lang='ru', fields=None):
        """
        Транслитерирует данные из одного языка в другой.
        
        :param data_list: список записей для транслитерации
        :param target_lang: целевой язык ('ru' или 'en')
        :param fields: список полей для транслитерации (если None, используются поля из конфигурации)
        :return: список транслитерированных записей
        """
        if not self.transliteration.enabled:
            return data_list
        
        if not fields:
            fields = [f for f, v in self.transliterate_fields.items() if v]
        
        result = []
        for item in data_list:
            new_item = item.copy()
            for field in fields:
                if field in item and item[field]:
                    source_value = item[field]
                    lang = translit.detect_language(source_value)
                    
                    if lang == 'ru' and target_lang == 'en':
                        new_item[field] = translit.transliterate_ru_to_en(
                            source_value, self.transliteration_standard
                        )
                    elif lang == 'en' and target_lang == 'ru':
                        new_item[field] = translit.transliterate_en_to_ru(
                            source_value, self.transliteration_standard
                        )
            result.append(new_item)
        
        return result
        
    def select_best_transliteration_variant(self, variants, target_lang='ru'):
        """
        Выбирает наилучший вариант из нескольких вариантов транслитерации.
        
        :param variants: список вариантов имени
        :param target_lang: целевой язык ('ru' или 'en')
        :return: наилучший вариант имени
        """
        if not variants:
            return None
            
        if len(variants) == 1:
            return variants[0]
            
        # Определяем языки всех вариантов
        langs = [translit.detect_language(v) for v in variants]
        
        # Если уже есть вариант на целевом языке, возвращаем его
        for i, lang in enumerate(langs):
            if lang == target_lang:
                return variants[i]
        
        # Иначе выбираем вариант, который лучше всего транслитерируется в целевой язык
        best_variant = variants[0]
        best_score = 0
        
        for variant in variants:
            if translit.detect_language(variant) == target_lang:
                # Если вариант уже на целевом языке, возвращаем его
                return variant
                
            # Транслитерируем и вычисляем "качество" варианта
            if target_lang == 'ru':
                translated = translit.transliterate_en_to_ru(variant, self.transliteration_standard)
            else:
                translated = translit.transliterate_ru_to_en(variant, self.transliteration_standard)
                
            # Подсчитываем, сколько символов успешно транслитерировалось
            success_rate = len(re.findall(r'[а-яА-ЯёЁ]' if target_lang == 'ru' else r'[a-zA-Z]', translated)) / (len(translated) or 1)
            
            if success_rate > best_score:
                best_score = success_rate
                best_variant = variant
                
        return best_variant
