"""
Тесты для модуля транслитерации
"""

import unittest
import sys
import os

# Добавляем корневую директорию проекта в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.core.data_matcher import DataMatcher
import fuzzy_matching.utils.transliteration.transliteration_utils as translit


class TestTransliteration(unittest.TestCase):
    """Тесты для проверки функционала транслитерации"""

    def setUp(self):
        """Подготовка для тестов"""
        # Создаем конфигурацию с включенной транслитерацией
        transliteration_config = TransliterationConfig(
            enabled=True,
            standard="Passport",
            normalize_names=True
        )
        
        self.config = MatchConfig(
            fields=[
                MatchFieldConfig(field='name', weight=1.0, transliterate=True)
            ],
            threshold=0.7,
            transliteration=transliteration_config
        )
        
        self.matcher = DataMatcher(config=self.config)

    def test_process_transliteration_basic(self):
        """Тест базового функционала транслитерации"""
        # Тестовые данные (русский - английский)
        test_pairs = [
            ("Иванов", "Ivanov"),
            ("Михаил", "Mikhail"),
            ("Санкт-Петербург", "Sankt-Peterburg")
        ]
        
        for ru, en in test_pairs:
            # Проверяем транслитерацию с русского на английский
            result_en, _, quality = self.matcher._process_transliteration(ru, en)
            self.assertGreater(quality, 0.7, f"Низкое качество транслитерации для {ru} -> {en}: {quality}")
            
            # Проверяем обратную транслитерацию с английского на русский
            _, result_ru, quality = self.matcher._process_transliteration(en, ru)
            self.assertGreater(quality, 0.7, f"Низкое качество транслитерации для {en} -> {ru}: {quality}")

    def test_process_transliteration_empty(self):
        """Тест транслитерации с пустыми строками"""
        # Тестовые данные с пустыми строками
        test_cases = [
            ("", "Test"),
            ("Тест", ""),
            ("", ""),
            (None, "Test"),
            ("Тест", None),
            (None, None)
        ]
        
        for value1, value2 in test_cases:
            result1, result2, quality = self.matcher._process_transliteration(value1, value2)
            self.assertEqual(quality, 0, f"Качество должно быть 0 для пустых строк: {value1}, {value2}")
            self.assertEqual(result1, value1, "Первая строка должна остаться без изменений")
            self.assertEqual(result2, value2, "Вторая строка должна остаться без изменений")

    def test_evaluate_transliteration_quality(self):
        """Тест метода оценки качества транслитерации"""
        # Тест с нормальными данными
        quality = self.matcher._evaluate_transliteration_quality(
            "Иванов", "Ivanov", "Ivanov"
        )
        self.assertGreater(quality, 0.8, "Качество должно быть высоким для правильной транслитерации")
        
        # Тест с пустыми строками
        empty_cases = [
            ("", "Ivanov", "Ivanov"),
            ("Иванов", "", "Ivanov"),
            ("Иванов", "Ivanov", ""),
            ("", "", "")
        ]
        
        for source, transliterated, target in empty_cases:
            quality = self.matcher._evaluate_transliteration_quality(source, transliterated, target)
            self.assertEqual(quality, 0.0, f"Качество должно быть 0 для пустых строк: {source}, {transliterated}, {target}")

    def test_detect_language(self):
        """Тест определения языка"""
        # Проверяем определение русского языка
        self.assertEqual(translit.detect_language("Привет, мир!"), "ru")
        # Проверяем определение английского языка
        self.assertEqual(translit.detect_language("Hello, world!"), "en")
        # Проверяем смешанный текст
        self.assertEqual(translit.detect_language("Hello, Привет!"), "mixed")
        # Проверяем пустую строку
        self.assertIsNone(translit.detect_language(""))
        # Проверяем None
        self.assertIsNone(translit.detect_language(None))
        # Проверяем строку без букв
        self.assertIsNone(translit.detect_language("123 !@#$%"))


if __name__ == "__main__":
    unittest.main() 