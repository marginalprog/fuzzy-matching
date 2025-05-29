"""
Основной модуль для сопоставления данных.
"""

import os
import csv
import json
import re
import pandas as pd
from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple, Any, Optional, Union

import fuzzy_matching.utils.transliteration.transliteration_utils as translit
from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig, 
    FuzzyAlgorithm
)

from collections import defaultdict


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
    def __init__(self, config: MatchConfig):
        """
        Инициализирует экземпляр класса DataMatcher.
        
        :param config: объект конфигурации MatchConfig, содержащий настройки для сопоставления
        """
        self.config = config
        
        # Создаем удобные атрибуты для часто используемых параметров
        self.threshold = config.threshold
        self.block_field = config.block_field
        self.transliteration = config.transliteration
        self.sort_before_match = config.sort_before_match
        
        # Создаем словарь весов полей для быстрого доступа
        self.weights = {field_config.field: field_config.weight for field_config in config.fields}
        
        # Список полей для сопоставления
        self.match_fields = [field_config.field for field_config in config.fields]
        
        # Словарь полей, для которых применяется транслитерация
        self.transliterate_fields = {field_config.field: field_config.transliterate for field_config in config.fields}
        
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
            if name_fields:
                # Если указан маппинг полей, используем его
                for orig_key, target_key in name_fields.items():
                    val = str(obj.get(orig_key, '')).strip()
                    if target_key in record and record[target_key]:
                        record[target_key] = f"{record[target_key]} {val}"
                    else:
                        record[target_key] = val
            else:
                # Если маппинг не указан, используем оригинальные имена полей
                for key, val in obj.items():
                    record[key] = str(val).strip()
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
            fieldnames = ['Оригинал', 'Вариант', 'Схожесть']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for match in matches:
                writer.writerow({
                    'Оригинал': str(match['Оригинал']),
                    'Вариант': str(match['Вариант']),
                    'Схожесть': f"{match['Схожесть']:.2f}"
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

    def _sort_data(self, records):
        """
        Сортирует список записей по полям сопоставления или заданному полю сортировки.
        
        :param records: список записей для сортировки
        :return: отсортированный список записей
        """
        if self.config.sort_field:
            # Если задано конкретное поле для сортировки, используем его
            sort_keys = [self.config.sort_field]
        else:
            # Иначе сортируем по всем полям сопоставления
            sort_keys = [field_config.field for field_config in self.config.fields]
            
        return sorted(records, key=lambda x: tuple(x.get(k, '') for k in sort_keys))

    def _weighted_average_similarity(self, record1, record2):
        """
        Вычисляет взвешенную среднюю схожесть между двумя записями
        
        :param record1: первая запись
        :param record2: вторая запись
        :return: кортеж (общая схожесть, список схожестей по полям)
        """
        similarities = []
        weights = []
        field_sims = []
        
        # Проходим по всем полям конфигурации
        for field_config in self.config.fields:
            field = field_config.field
            weight = field_config.weight
            
            # Получаем значения полей
            value1 = record1.get(field, "")
            value2 = record2.get(field, "")
            
            # Если задана транслитерация, обрабатываем поля
            if field_config.transliterate and self.config.transliteration.enabled:
                value1_trans, value2_trans, _ = self._process_transliteration(value1, value2)
                value1, value2 = value1_trans, value2_trans
            
            # Вычисляем схожесть с учетом выбранного алгоритма для данного поля
            similarity = self._get_similarity(value1, value2, field_config.fuzzy_algorithm)
            
            field_sims.append((field, value1, value2, similarity))
            similarities.append(similarity)
            weights.append(weight)
        
        # Если нет полей для сравнения, возвращаем 0
        if not similarities:
            return 0, []
        
        # Вычисляем взвешенную среднюю схожесть
        total_weight = sum(weights)
        weighted_sum = sum(sim * weight for sim, weight in zip(similarities, weights))
        
        # Предотвращаем деление на ноль
        avg_similarity = weighted_sum / total_weight if total_weight > 0 else 0
        
        return avg_similarity, field_sims

    def _block_by_fields(self, recs):
        """
        Блокирует записи по первому символу поля block_field,
        с дополнительной группировкой по полям group_fields.
        Если дополнительные поля группировки (group_fields) указаны:
            Создает вложенную структуру с блоками и подгруппами
            Первый уровень: первая буква значения блокирующего поля (в верхнем регистре)
            Второй уровень: кортеж значений полей из group_fields
        """
        if self.block_field is None:
            return {'ALL': recs}
        if self.config.group_fields:
            blocks = defaultdict(lambda: defaultdict(list))
            for rec in recs:
                val = rec.get(self.block_field, '')
                if not val:
                    continue
                key = val[0].upper()
                group_key = tuple(rec.get(f, '') for f in self.config.group_fields)
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

    def select_cleaner_record(self, record1, record2):
        """
        Выбирает запись с меньшим 'шумом' (спецсимволы + длина).
        """
        def cleanliness_score(record):
            combined = ' '.join(str(record.get(f, '')) for f in self.match_fields)
            special_chars = len(re.findall(r'[^a-zA-Zа-яА-Я0-9\s]', combined))
            length = len(combined)
            return special_chars + length * self.weights.get('length', 0)

        score1 = cleanliness_score(record1)
        score2 = cleanliness_score(record2)
        if score1 < score2:
            return record1
        elif score2 < score1:
            return record2
        # Если равны, выбираем более короткую запись
        length1 = sum(len(str(record1.get(f, ''))) for f in self.match_fields)
        length2 = sum(len(str(record2.get(f, ''))) for f in self.match_fields)
        return record1 if length1 <= length2 else record2
    
    def _evaluate_transliteration_quality(self, source_text, transliterated_text, target_text):
        """
        Оценивает качество транслитерации по нескольким критериям.
        
        :param source_text: исходный текст
        :param transliterated_text: транслитерированный текст
        :param target_text: целевой текст для сравнения
        :return: оценка качества (0.0-1.0)
        """
        if not source_text or not transliterated_text or not target_text:
            return 0.0
        
        # Компонент 1: Семантическое сходство (используем token_sort_ratio)
        semantic_similarity = fuzz.token_sort_ratio(transliterated_text.lower(), target_text.lower()) / 100
        
        # Компонент 2: Символьное соответствие
        # Вычисляем, какой процент символов в transliterated_text соответствует ожидаемому языку
        expected_pattern = r'[а-яА-ЯёЁ]' if translit.detect_language(target_text) == 'ru' else r'[a-zA-Z]'
        total_chars = len(transliterated_text.strip())
        if total_chars == 0:
            return 0.0
            
        valid_chars = len(re.findall(expected_pattern, transliterated_text))
        char_quality = valid_chars / total_chars if total_chars > 0 else 0
        
        # Компонент 3: Длина (отношение длин текстов не должно сильно различаться)
        source_len = len(source_text.strip())
        target_len = len(target_text.strip())
        trans_len = len(transliterated_text.strip())
        
        # Сравниваем, насколько длина транслитерации ближе к длине целевого текста
        if target_len == 0:
            length_ratio = 0.0
        else:
            length_delta = abs(trans_len - target_len) / target_len
            length_ratio = max(0, 1 - length_delta)  # 1.0 - идентичная длина, 0.0 - сильно отличается
        
        # Взвешенная комбинация всех компонентов
        # Придаем больший вес семантическому сходству, так как оно наиболее важно
        weights = (0.6, 0.3, 0.1)  # Веса для semantic_similarity, char_quality, length_ratio
        weighted_score = (
            semantic_similarity * weights[0] + 
            char_quality * weights[1] + 
            length_ratio * weights[2]
        )
        
        return weighted_score
    
    def _process_transliteration(self, value1, value2, field=None):
        """
        Обрабатывает пару строк с транслитерацией, автоматически определяет язык и
        выбирает оптимальное сопоставление.
        
        :param value1: первая строка
        :param value2: вторая строка
        :param field: имя поля (опциональное)
        :return: кортеж (преобразованная_строка1, преобразованная_строка2, схожесть)
        """
        if not value1 or not value2:
            return value1, value2, 0
        
        # Определяем язык строк
        lang1 = translit.detect_language(value1)
        lang2 = translit.detect_language(value2)
        
        # Если язык не удалось определить для одной из строк, возвращаем оригинальные строки
        if lang1 is None or lang2 is None:
            similarity = fuzz.token_sort_ratio(value1.lower(), value2.lower()) / 100 if value1 and value2 else 0
            return value1, value2, similarity
        
        # Нормализуем имена, если это указано в настройках
        if self.transliteration.normalize_names:
            if lang1 == 'ru':
                value1 = translit.normalize_name_ru(value1)
            else:
                value1 = translit.normalize_name_en(value1)
                
            if lang2 == 'ru':
                value2 = translit.normalize_name_ru(value2)
            else:
                value2 = translit.normalize_name_en(value2)
        
        # Получаем стандарт транслитерации
        standard_name = self.transliteration.standard
        standard = translit.get_standard_by_name(standard_name)
        if not standard:
            standard = translit.PASSPORT_STANDARD  # По умолчанию используем паспортный стандарт
        
        # Если языки разные, выполняем транслитерацию
        if lang1 != lang2:
            # Выбираем направление транслитерации и обрабатываем строки
            if lang1 == 'ru' and lang2 == 'en':
                # Вариант 1: транслитерируем value1 с русского на английский
                value1_en = translit.transliterate_ru_to_en(value1, standard)
                # source_text=value1 (ru), transliterated_text=value1_en (en), target_text=value2 (en)
                quality1 = self._evaluate_transliteration_quality(value1, value1_en, value2)
                
                # Вариант 2: транслитерируем value2 с английского на русский
                value2_ru = translit.transliterate_en_to_ru(value2, standard)
                # source_text=value2 (en), transliterated_text=value2_ru (ru), target_text=value1 (ru)
                quality2 = self._evaluate_transliteration_quality(value2, value2_ru, value1)
                
                # Выбираем лучший вариант
                if quality1 >= quality2:
                    return value1_en, value2, quality1
                else:
                    return value1, value2_ru, quality2
            
            elif lang1 == 'en' and lang2 == 'ru':
                # Вариант 1: транслитерируем value1 с английского на русский
                value1_ru = translit.transliterate_en_to_ru(value1, standard)
                # source_text=value1 (en), transliterated_text=value1_ru (ru), target_text=value2 (ru)
                quality1 = self._evaluate_transliteration_quality(value1, value1_ru, value2)
                
                # Вариант 2: транслитерируем value2 с русского на английский
                value2_en = translit.transliterate_ru_to_en(value2, standard)
                # source_text=value2 (ru), transliterated_text=value2_en (en), target_text=value1 (en)
                quality2 = self._evaluate_transliteration_quality(value2, value2_en, value1)
                
                # Выбираем лучший вариант
                if quality1 >= quality2:
                    return value1_ru, value2, quality1
                else:
                    return value1, value2_en, quality2
        
        # Если языки одинаковые или не удалось определить, возвращаем оригинальные строки
        similarity = fuzz.token_sort_ratio(value1.lower(), value2.lower()) / 100
        return value1, value2, similarity
            
    def match_and_consolidate(self, data1, data2):
        """
        Сопоставляет два набора данных и консолидирует совпадения
        
        :param data1: первый набор данных
        :param data2: второй набор данных
        :return: кортеж (список совпадений, консолидированные данные)
        """
        matches = []
        consolidated = []
        
        # Копируем данные, чтобы не изменять оригиналы
        data1 = [record.copy() for record in data1]
        data2 = [record.copy() for record in data2]
        
        # Сортируем данные, если это указано в конфигурации
        if self.sort_before_match:
            data1 = self._sort_data(data1)
            data2 = self._sort_data(data2)
        
        # Если используется блокировка, группируем данные по блокирующему полю
        if self.block_field:
            blocks1 = self._block_by_fields(data1)
            blocks2 = self._block_by_fields(data2)
            
            # Обрабатываем каждый блок
            for block_key in blocks1:
                if block_key in blocks2:
                    # Блок существует в обоих наборах данных
                    block_matches = self.process_block(blocks1[block_key], blocks2[block_key])
                    matches.extend(block_matches)
        else:
            # Если блокировка не используется, обрабатываем все данные как один блок
            matches.extend(self.process_block(data1, data2))
        
        # Создаем множества для отслеживания использованных записей
        used_records1 = set()
        used_records2 = set()
        
        # Обрабатываем совпадения с высокой схожестью
        high_similarity_matches = []
        low_similarity_matches = []
        
        # Разделяем совпадения на группы по схожести
        for match in matches:
            if match["Схожесть"] >= self.threshold:
                high_similarity_matches.append(match)
            else:
                low_similarity_matches.append(match)
        
        # Обрабатываем совпадения с высокой схожестью
        for match in high_similarity_matches:
            record1 = match["Оригинал"]
            record2 = match["Вариант"]
            
            # Выбираем "лучшую" запись для консолидации
            consolidated_record = self.select_cleaner_record(record1, record2)
            consolidated.append(consolidated_record)
            
            # Отмечаем записи как использованные
            used_records1.add(id(record1))
            used_records2.add(id(record2))
        
        # Для совпадений с низкой схожестью сохраняем обе записи
        for match in low_similarity_matches:
            record1 = match["Оригинал"]
            record2 = match["Вариант"]
            
            # Добавляем обе записи, если они еще не были использованы
            if id(record1) not in used_records1:
                consolidated.append(record1.copy())
                used_records1.add(id(record1))
            if id(record2) not in used_records2:
                consolidated.append(record2.copy())
                used_records2.add(id(record2))
        
        # Добавляем оставшиеся несопоставленные записи из обоих наборов
        for record in data1:
            if id(record) not in used_records1:
                consolidated.append(record.copy())
                used_records1.add(id(record))
        
        for record in data2:
            if id(record) not in used_records2:
                consolidated.append(record.copy())
                used_records2.add(id(record))
        
        return matches, consolidated
    
    def transliterate_data(self, data_list, target_lang='ru', fields=None):
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
            new_item = item.copy()  # Копируем все поля из оригинальной записи
            for field in fields:
                if field in item and item[field]:
                    source_value = str(item[field])  # Преобразуем в строку для безопасности
                    lang = translit.detect_language(source_value)
                    
                    # Если язык не определен или совпадает с целевым, пропускаем
                    if lang == target_lang:
                        continue
                        
                    # Транслитерируем в зависимости от языка источника и цели
                    if (lang == 'ru' and target_lang == 'en') or (lang is None and target_lang == 'en'):
                        transliterated = translit.transliterate_ru_to_en(
                            source_value, self.transliteration_standard
                        )
                    elif (lang == 'en' and target_lang == 'ru') or (lang is None and target_lang == 'ru'):
                        transliterated = translit.transliterate_en_to_ru(
                            source_value, self.transliteration_standard
                        )
                    else:
                        transliterated = source_value
                    
                    # Сохраняем оригинальный регистр первой буквы
                    if source_value and source_value[0].isupper():
                        transliterated = transliterated.capitalize()
                    
                    new_item[field] = transliterated
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
                
            # Транслитерируем вариант и оцениваем качество
            if target_lang == 'ru':
                translated = translit.transliterate_en_to_ru(variant, self.transliteration_standard)
                # Создаем эталонный текст на русском для сравнения 
                # (используем первый вариант из списка как базовый)
                reference_text = translit.transliterate_en_to_ru(variants[0], self.transliteration_standard)
                # Оцениваем качество: исходный текст (en), транслитерированный текст (ru), целевой текст (ru)
                quality = self._evaluate_transliteration_quality(variant, translated, reference_text)
            else:
                translated = translit.transliterate_ru_to_en(variant, self.transliteration_standard)
                # Создаем эталонный текст на английском для сравнения
                reference_text = translit.transliterate_ru_to_en(variants[0], self.transliteration_standard)
                # Оцениваем качество: исходный текст (ru), транслитерированный текст (en), целевой текст (en)
                quality = self._evaluate_transliteration_quality(variant, translated, reference_text)
                
            if quality > best_score:
                best_score = quality
                best_variant = variant
                
        return best_variant

    def _get_similarity(self, str1, str2, fuzzy_algorithm=None):
        """
        Вычисляет нечеткую схожесть между двумя строками
        с использованием выбранного алгоритма.
        
        :param str1: первая строка
        :param str2: вторая строка
        :param fuzzy_algorithm: алгоритм нечёткого сопоставления (если None, используется из конфигурации)
        :return: степень схожести (0-1)
        """
        # Если строки пустые или обе None, возвращаем 0
        if (str1 is None and str2 is None) or (not str1 and not str2):
            return 0
        # Если одна из строк None или пустая, возвращаем 0
        if str1 is None or str2 is None or not str1 or not str2:
            return 0
        
        # Определяем алгоритм для использования
        algorithm = fuzzy_algorithm  # Приоритет 1: явно указанный алгоритм для поля
        
        # Если всё еще нет алгоритма, используем общий из конфигурации
        if algorithm is None:
            algorithm = self.config.fuzzy_algorithm
        
        # Используем соответствующий алгоритм
        if algorithm == FuzzyAlgorithm.RATIO:
            return fuzz.ratio(str1.lower(), str2.lower()) / 100
        elif algorithm == FuzzyAlgorithm.PARTIAL_RATIO:
            return fuzz.partial_ratio(str1.lower(), str2.lower()) / 100
        elif algorithm == FuzzyAlgorithm.TOKEN_SORT:
            return fuzz.token_sort_ratio(str1.lower(), str2.lower()) / 100
        elif algorithm == FuzzyAlgorithm.TOKEN_SET:
            return fuzz.token_set_ratio(str1.lower(), str2.lower()) / 100
        elif algorithm == FuzzyAlgorithm.WRatio:
            return fuzz.WRatio(str1.lower(), str2.lower()) / 100
        else:
            # По умолчанию используем обычный ratio
            return fuzz.ratio(str1.lower(), str2.lower()) / 100

    def process_block(self, block1, block2):
        """
        Обрабатывает блоки и находит соответствия
        
        :param block1: первый блок данных
        :param block2: второй блок данных
        :return: список найденных соответствий
        """
        block_matches = []
        matched_indices2 = set()  # Индексы из block2, которые уже сопоставлены

        for i, record1 in enumerate(block1):
            max_similarity = 0
            best_match = None
            best_j = None
            best_field_similarities = []

            for j, record2 in enumerate(block2):
                if j in matched_indices2:
                    continue  # Пропускаем уже сопоставленные записи из block2

                # Вычисляем схожесть между записями
                similarity, field_similarities = self._weighted_average_similarity(record1, record2)

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = record2
                    best_j = j
                    best_field_similarities = field_similarities

            # Добавляем соответствие только если оно выше порога
            if max_similarity >= self.threshold and best_match:
                # Форматируем для вывода
                record1_values = [record1.get(field_config.field, "") for field_config in self.config.fields]
                record2_values = [best_match.get(field_config.field, "") for field_config in self.config.fields]

                match_data = {
                    "Оригинал": record1,
                    "Вариант": best_match,
                    "Схожесть": max_similarity
                }

                block_matches.append(match_data)
                matched_indices2.add(best_j)  # Помечаем запись как уже сопоставленную

        return block_matches
