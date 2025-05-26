import unittest
import os
import tempfile
import sys
from fuzzy_matching.core.match_config_classes import MatchConfig, MatchFieldConfig, TransliterationConfig
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.utils.data_generator import DataGenerator, Language
import fuzzy_matching.utils.transliteration.transliteration_utils as translit

# Цвета для вывода (как в main.py)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.transliteration_config = TransliterationConfig(
            enabled=True,
            standard="Passport",
            normalize_names=True
        )
        self.config = MatchConfig(
            fields=[MatchFieldConfig(field='name', weight=1.0, transliterate=True)],
            threshold=0.7,
            transliteration=self.transliteration_config
        )
        self.matcher = DataMatcher(config=self.config)

    def test_nonexistent_file(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Проверка загрузки несуществующего файла (.load_from_csv(), .load_from_json()){Colors.ENDC}")
        print(f"  {Colors.YELLOW}Параметры: 'nonexistent_file.csv', 'nonexistent_file.json'{Colors.ENDC}")
        with self.assertRaises(FileNotFoundError):
            self.matcher.load_from_csv('nonexistent_file.csv', {'name': 'name'})
        with self.assertRaises(FileNotFoundError):
            self.matcher.load_from_json('nonexistent_file.json', {'name': 'name'})
        print(f"  {Colors.GREEN}Ожидаемый результат: FileNotFoundError{Colors.ENDC}")

    def test_invalid_field_in_record(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Проверка обработки записи с отсутствующим полем (._weighted_average()){Colors.ENDC}")
        record1 = {'name': 'Иванов'}
        record2 = {'wrong_field': 'Ivanov'}
        print(f"  {Colors.YELLOW}Параметры: --record1={record1}, --record2={record2}{Colors.ENDC}")
        sim = self.matcher._weighted_average(record1, record2)
        print(f"  {Colors.GREEN}Результат: {sim}{Colors.ENDC}")
        self.assertIsInstance(sim, tuple)
        print(f"  {Colors.GREEN}Ожидаемый результат: корректная обработка, не выбрасывается исключение{Colors.ENDC}")

    def test_invalid_transliteration_standard(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Некорректный стандарт транслитерации (TransliterationConfig){Colors.ENDC}")
        config = MatchConfig(
            fields=[MatchFieldConfig(field='name', weight=1.0, transliterate=True)],
            threshold=0.7,
            transliteration=TransliterationConfig(enabled=True, standard="NonExistentStandard")
        )
        matcher = DataMatcher(config=config)
        print(f"  {Colors.YELLOW}Параметры: --standard='NonExistentStandard'{Colors.ENDC}")
        result = matcher._process_transliteration('Иванов', 'Ivanov')
        print(f"  {Colors.GREEN}Результат: {result}{Colors.ENDC}")
        self.assertIsInstance(result, tuple)
        print(f"  {Colors.GREEN}Ожидаемый результат: используется стандарт PASSPORT по умолчанию, не выбрасывается исключение{Colors.ENDC}")

    def test_invalid_language_for_generator(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Некорректный язык для генератора данных (DataGenerator){Colors.ENDC}")
        print(f"  {Colors.YELLOW}Параметры: --language='xx'{Colors.ENDC}")
        with self.assertRaises(AttributeError):
            DataGenerator(language="xx")
        print(f"  {Colors.RED}Ожидаемый результат: AttributeError{Colors.ENDC}")
        
    def test_data_generator_swap_char(self):
        print(f"{Colors.CYAN}{Colors.BOLD}[TEST] Перестановка при генерации данных{Colors.ENDC}")
        probabilities = {
            'double_char_probability': 0.0,
            'change_char_probability': 0.0,
            'swap_char_probability': 1.0,  # всегда переставлять
            'change_name_probability': 0.0,
            'change_domain_probability': 0.0,
            'double_number_probability': 0.0,
            'suffix_probability': 0.0
        }
        dg = DataGenerator(language=Language.RUS, probabilities=probabilities)
        name = "Алексей"
        swapped, _ = dg.vary_name(name, 'first', gender='м')
        print(f"  {Colors.YELLOW}Исходное имя: {name}{Colors.ENDC}")
        print(f"  {Colors.GREEN}Результат после swap: {swapped}{Colors.ENDC}")
        self.assertNotEqual(name, swapped)
        self.assertEqual(len(name), len(swapped))
        self.assertEqual(name[0], swapped[0])  # первый символ не меняется
        # Проверяем, что swap не ломает короткие строки
        short = "Ан"
        swapped_short, _ = dg.vary_name(short, 'first', gender='м')
        print(f"  {Colors.YELLOW}Короткое имя: {short}{Colors.ENDC}")
        print(f"  {Colors.GREEN}Результат после swap: {swapped_short}{Colors.ENDC}")
        self.assertEqual(short, swapped_short)

    def test_invalid_probability_keys(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Некорректные ключи вероятностей (DataGenerator){Colors.ENDC}")
        print(f"  {Colors.YELLOW}Параметры: probabilities={{'wrong_key': 0.5}}{Colors.ENDC}")
        dg = DataGenerator(language=Language.RUS, probabilities={'wrong_key': 0.5})
        print(f"  {Colors.GREEN}Результат: DataGenerator успешно создан, language={dg.language}, double_char_probability={dg.double_char_probability}{Colors.ENDC}")
        self.assertIsInstance(dg, DataGenerator)
        print(f"  {Colors.GREEN}Ожидаемый результат: игнорируются лишние ключи, не выбрасывается исключение{Colors.ENDC}")

    def test_invalid_transliterate_data_field(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Некорректное поле для транслитерации (.transliterate_data()){Colors.ENDC}")
        data = [{'name': 'Иванов', 'other': 'Test'}]
        print(f"  {Colors.YELLOW}Параметры: --fields=['not_exist'], --data={data}{Colors.ENDC}")
        result = self.matcher.transliterate_data(data, target_lang='en', fields=['not_exist'])
        print(f"  {Colors.GREEN}Результат: {result}{Colors.ENDC}")
        self.assertEqual(result[0]['name'], 'Иванов')
        print(f"  {Colors.GREEN}Ожидаемый результат: исходные данные не изменяются, не выбрасывается исключение{Colors.ENDC}")

    def test_invalid_format_in_cli_utils(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] ValueError при неверном формате файла (.generate_and_save_test_data()){Colors.ENDC}")
        from fuzzy_matching.utils.cli_utils import generate_and_save_test_data
        print(f"  {Colors.YELLOW}Параметры: --file_format='txt'{Colors.ENDC}")
        with self.assertRaises(ValueError):
            generate_and_save_test_data({}, ['name'], 1, file_format='txt')
        print(f"  {Colors.RED}Ожидаемый результат: ValueError{Colors.ENDC}")

    def test_invalid_output_format_in_cli_utils(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] ValueError при неверном формате вывода (.save_results()){Colors.ENDC}")
        from fuzzy_matching.utils.cli_utils import save_results
        print(f"  {Colors.YELLOW}Параметры: --file_format='txt'{Colors.ENDC}")
        with self.assertRaises(ValueError):
            save_results(self.matcher, [], [], file_format='txt')
        print(f"  {Colors.RED}Ожидаемый результат: ValueError{Colors.ENDC}")

    def test_invalid_algorithm_in_match_field(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}[TEST] Некорректный алгоритм для поля ({Colors.GREEN}--fuzzy_algorithm{Colors.ENDC}){Colors.ENDC}")
        config = MatchConfig(
            fields=[MatchFieldConfig(field='name', weight=1.0, transliterate=True, fuzzy_algorithm=None)],
            threshold=0.7,
            transliteration=self.transliteration_config
        )
        matcher = DataMatcher(config=config)
        print(f"  {Colors.YELLOW}Параметры: --fuzzy_algorithm='NON_EXISTENT'{Colors.ENDC}")
        sim = matcher._get_similarity('a', 'b', fuzzy_algorithm='NON_EXISTENT')
        print(f"  {Colors.GREEN}Результат: {sim}{Colors.ENDC}")
        self.assertIsInstance(sim, float)
        print(f"  {Colors.GREEN}Ожидаемый результат: используется алгоритм по умолчанию, не выбрасывается исключение{Colors.ENDC}")

if __name__ == "__main__":
    unittest.main() 