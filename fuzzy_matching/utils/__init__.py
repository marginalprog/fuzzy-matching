"""
Утилиты для работы с нечетким сопоставлением данных.
"""

# Обеспечиваем доступ к модулю transliteration_utils через более короткий путь
from fuzzy_matching.utils.transliteration.transliteration_utils import *

# Примечание: функции из cli_utils не импортируются здесь напрямую
# для избежания циклических импортов. Их следует импортировать
# непосредственно из модуля cli_utils:
# from fuzzy_matching.utils.cli_utils import generate_test_data, save_results, etc.
