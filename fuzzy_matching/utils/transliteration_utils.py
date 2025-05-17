"""
Модуль для работы с транслитерацией имён и других строк между русским и английским языками.
Поддерживает различные стандарты транслитерации.
"""

import re


class TransliterationStandard:
    """Класс, представляющий стандарт транслитерации"""
    
    def __init__(self, name, description, ru_to_en_map, en_to_ru_map=None):
        """
        Инициализирует стандарт транслитерации.
        
        :param name: название стандарта
        :param description: описание стандарта
        :param ru_to_en_map: словарь для транслитерации с русского на английский
        :param en_to_ru_map: словарь для транслитерации с английского на русский (если None, будет создан на основе ru_to_en_map)
        """
        self.name = name
        self.description = description
        self.ru_to_en_map = ru_to_en_map
        
        if en_to_ru_map is None:
            # Создаем обратный словарь, но только для однозначных соответствий
            self.en_to_ru_map = {}
            for ru, en in ru_to_en_map.items():
                if en not in self.en_to_ru_map:
                    self.en_to_ru_map[en] = ru
        else:
            self.en_to_ru_map = en_to_ru_map


# Определение стандартов транслитерации

# Стандарт ГОСТ 7.79-2000 (ISO 9:1995)
GOST_779_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'shh', 'ъ': '', 
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

# Научная транслитерация
SCIENTIFIC_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'ë', 
    'ж': 'ž', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 
    'ф': 'f', 'х': 'x', 'ц': 'c', 'ч': 'č', 'ш': 'š', 'щ': 'šč', 'ъ': '', 
    'ы': 'y', 'ь': '′', 'э': 'è', 'ю': 'ju', 'я': 'ja'
}

# Упрощенная транслитерация (используется в паспортах и на практике)
PASSPORT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'iu', 'я': 'ia'
}

# Обратное отображение для упрощенной транслитерации
PASSPORT_EN_TO_RU_MAP = {
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 
    'zh': 'ж', 'z': 'з', 'i': 'и', 'k': 'к', 'l': 'л', 'm': 'м', 
    'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 
    'u': 'у', 'f': 'ф', 'kh': 'х', 'ts': 'ц', 'ch': 'ч', 'sh': 'ш', 
    'shch': 'щ', 'y': 'ы', 'yu': 'ю', 'iu': 'ю', 'ya': 'я', 'ia': 'я'
}

# Создаем экземпляры стандартов
GOST_STANDARD = TransliterationStandard(
    "ГОСТ", # 7.79-2000
    "Российский стандарт транслитерации, соответствующий ISO 9:1995",
    GOST_779_MAP
)

SCIENTIFIC_STANDARD = TransliterationStandard(
    "Научная", 
    "Используется в лингвистике и научных работах",
    SCIENTIFIC_MAP
)

PASSPORT_STANDARD = TransliterationStandard(
    "Паспортная", 
    "Упрощенная транслитерация, используемая в загранпаспортах РФ",
    PASSPORT_MAP,
    PASSPORT_EN_TO_RU_MAP
)

# Список всех доступных стандартов
STANDARDS = [GOST_STANDARD, SCIENTIFIC_STANDARD, PASSPORT_STANDARD]


def get_standard_by_name(name):
    """
    Возвращает стандарт транслитерации по его названию.
    
    :param name: название стандарта
    :return: объект TransliterationStandard или None, если стандарт не найден
    """
    for standard in STANDARDS:
        if standard.name.lower() == name.lower():
            return standard
    return None


def transliterate_ru_to_en(text, standard=PASSPORT_STANDARD):
    """
    Транслитерирует текст с русского на английский согласно указанному стандарту.
    
    :param text: исходный текст на русском
    :param standard: стандарт транслитерации (объект TransliterationStandard)
    :return: транслитерированный текст
    """
    result = ""
    text = text.lower()
    i = 0
    while i < len(text):
        char = text[i]
        # Проверяем составные символы (например, 'щ' -> 'shch')
        found = False
        for ru_seq in sorted(standard.ru_to_en_map.keys(), key=len, reverse=True):
            if i + len(ru_seq) <= len(text) and text[i:i+len(ru_seq)] == ru_seq:
                result += standard.ru_to_en_map[ru_seq]
                i += len(ru_seq)
                found = True
                break
        
        if not found:
            if char in standard.ru_to_en_map:
                result += standard.ru_to_en_map[char]
            else:
                result += char
            i += 1
            
    return result


def transliterate_en_to_ru(text, standard=PASSPORT_STANDARD):
    """
    Транслитерирует текст с английского на русский согласно указанному стандарту.
    
    :param text: исходный текст на английском
    :param standard: стандарт транслитерации (объект TransliterationStandard)
    :return: транслитерированный текст
    """
    result = ""
    text = text.lower()
    i = 0
    while i < len(text):
        # Проверяем составные символы (например, 'sh' -> 'ш')
        found = False
        for en_seq in sorted(standard.en_to_ru_map.keys(), key=len, reverse=True):
            if i + len(en_seq) <= len(text) and text[i:i+len(en_seq)] == en_seq:
                result += standard.en_to_ru_map[en_seq]
                i += len(en_seq)
                found = True
                break
        
        if not found:
            char = text[i]
            if char in standard.en_to_ru_map:
                result += standard.en_to_ru_map[char]
            else:
                result += char
            i += 1
            
    return result


def detect_language(text):
    """
    Определяет язык текста (русский или английский).
    
    :param text: анализируемый текст
    :return: 'ru' для русского, 'en' для английского, 'mixed' для смешанного
    """
    if not text:
        return None
        
    # Считаем символы
    ru_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
    en_chars = len(re.findall(r'[a-zA-Z]', text))
    
    total_chars = ru_chars + en_chars
    
    if total_chars == 0:
        return None
    
    ru_ratio = ru_chars / total_chars
    en_ratio = en_chars / total_chars
    
    # Определяем язык по преобладающим символам
    if ru_ratio > 0.7:
        return 'ru'
    elif en_ratio > 0.7:
        return 'en'
    else:
        return 'mixed'


def is_valid_transliteration(ru_text, en_text, standard=PASSPORT_STANDARD, threshold=0.8):
    """
    Проверяет, является ли английский текст транслитерацией русского.
    
    :param ru_text: текст на русском языке
    :param en_text: потенциальная транслитерация на английском
    :param standard: стандарт транслитерации
    :param threshold: порог схожести (0-1)
    :return: True если en_text является транслитерацией ru_text, иначе False
    """
    # Транслитерируем русский текст
    expected_en = transliterate_ru_to_en(ru_text, standard)
    
    # Нормализуем строки для сравнения
    expected_en = expected_en.lower().replace(' ', '')
    actual_en = en_text.lower().replace(' ', '')
    
    # Вычисляем схожесть
    from rapidfuzz import fuzz
    similarity = fuzz.ratio(expected_en, actual_en) / 100.0
    
    return similarity >= threshold


def normalize_name_ru(name):
    """
    Нормализует русское имя, удаляя лишние символы и приводя к нижнему регистру.
    
    :param name: исходное имя
    :return: нормализованное имя
    """
    # Удаляем все, кроме русских букв и пробелов
    name = re.sub(r'[^а-яА-ЯёЁ\s]', '', name)
    # Приводим к нижнему регистру
    name = name.lower()
    # Заменяем ё на е (распространенный вариант)
    name = name.replace('ё', 'е')
    # Удаляем лишние пробелы
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def normalize_name_en(name):
    """
    Нормализует английское имя, удаляя лишние символы и приводя к нижнему регистру.
    
    :param name: исходное имя
    :return: нормализованное имя
    """
    # Удаляем все, кроме латинских букв и пробелов
    name = re.sub(r'[^a-zA-Z\s]', '', name)
    # Приводим к нижнему регистру
    name = name.lower()
    # Удаляем лишние пробелы
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def get_all_possible_transliterations(text, from_lang='ru'):
    """
    Возвращает все возможные варианты транслитерации текста.
    
    :param text: исходный текст
    :param from_lang: исходный язык ('ru' или 'en')
    :return: список возможных транслитераций
    """
    result = []
    
    if from_lang == 'ru':
        for standard in STANDARDS:
            trans = transliterate_ru_to_en(text, standard)
            if trans and trans not in result:
                result.append(trans)
    else:  # from_lang == 'en'
        for standard in STANDARDS:
            trans = transliterate_en_to_ru(text, standard)
            if trans and trans not in result:
                result.append(trans)
                
    return result


def get_best_transliteration_match(source_text, target_texts, from_lang='ru'):
    """
    Находит наилучшее соответствие среди возможных транслитераций.
    
    :param source_text: исходный текст
    :param target_texts: список текстов для сравнения
    :param from_lang: исходный язык ('ru' или 'en')
    :return: кортеж (лучший вариант, коэффициент схожести)
    """
    from rapidfuzz import fuzz
    
    # Получаем все возможные транслитерации
    transliterations = get_all_possible_transliterations(source_text, from_lang)
    
    best_match = None
    best_score = 0
    
    for target in target_texts:
        for trans in transliterations:
            score = fuzz.token_sort_ratio(trans.lower(), target.lower()) / 100.0
            if score > best_score:
                best_score = score
                best_match = target
                
    return best_match, best_score 