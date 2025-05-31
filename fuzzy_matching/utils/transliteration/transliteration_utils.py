"""
Модуль для работы с транслитерацией имён и других строк между русским и английским языками.
Поддерживает различные стандарты транслитерации:

1. ГОСТ 7.79-2000 (ISO 9:1995) - основной стандарт
   - Полностью обратимый (биективный)
   - Поддерживает все особенности русского алфавита
   - Рекомендуется для использования в научных и официальных документах
   - Поддерживает обратную транслитерацию

2. Научная транслитерация (стандарт Библиотеки Конгресса США)
   - Используется в научных публикациях и библиографических описаниях
   - Содержит специальные символы для точной передачи фонетики
   - Не полностью обратима из-за неоднозначности некоторых символов

3. Паспортная транслитерация (Приказ МИД РФ от 12.02.2020 № 2113)
   - Используется в загранпаспортах и других документах
   - Упрощенная система без диакритических знаков
   - Не является полностью обратимой
   - Поддерживает ограниченную обратную транслитерацию для однозначных соответствий

Рекомендации по использованию:
- Для систем, требующих точной обратимости, используйте ГОСТ 7.79-2000
- Для документов и паспортов используйте паспортную транслитерацию
- Для научных публикаций используйте научную транслитерацию

Примечание: При обратной транслитерации с английского на русский рекомендуется
использовать ГОСТ 7.79-2000, так как он обеспечивает однозначное соответствие
между символами и является полностью обратимым.
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

# Стандарт ГОСТ 7.79-2000 система А (с диакритическими знаками)
GOST_779_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'ё', 
    'ж': 'ž', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'č', 'ш': 'š', 'щ': 'ŝ', 'ъ': 'ʺ', 
    'ы': 'y', 'ь': 'ʹ', 'э': 'è', 'ю': 'û', 'я': 'â',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Ё', 
    'Ж': 'Ž', 'З': 'Z', 'И': 'I', 'Й': 'J', 'К': 'K', 'Л': 'L', 'М': 'M', 
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 
    'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'Č', 'Ш': 'Š', 'Щ': 'Ŝ', 'Ъ': 'ʺ', 
    'Ы': 'Y', 'Ь': 'ʹ', 'Э': 'È', 'Ю': 'Û', 'Я': 'Â'
}

# Обратное отображение для ГОСТ
GOST_EN_TO_RU_MAP = {
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 
    'ž': 'ж', 'z': 'з', 'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 
    'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 
    't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х', 'c': 'ц', 'č': 'ч', 
    'š': 'ш', 'ŝ': 'щ', 'ʺ': 'ъ', 'y': 'ы', 'ʹ': 'ь', 'è': 'э', 
    'û': 'ю', 'â': 'я', 'ё': 'ё',
    # Заглавные буквы
    'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Е', 
    'Ž': 'Ж', 'Z': 'З', 'I': 'И', 'J': 'Й', 'K': 'К', 'L': 'Л', 
    'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р', 'S': 'С', 
    'T': 'Т', 'U': 'У', 'F': 'Ф', 'H': 'Х', 'C': 'Ц', 'Č': 'Ч', 
    'Š': 'Ш', 'Ŝ': 'Щ', 'Y': 'Ы', 'È': 'Э', 'Û': 'Ю', 'Â': 'Я', 
    'Ё': 'Ё'
}

# Научная транслитерация (ISO/R 9:1995)
SCIENTIFIC_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'ë', 
    'ж': 'ž', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 
    'ф': 'f', 'х': 'x', 'ц': 'c', 'ч': 'č', 'ш': 'š', 'щ': 'ŝ', 'ъ': '″', 
    'ы': 'y', 'ь': '′', 'э': 'è', 'ю': 'ju', 'я': 'ja',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Ë', 
    'Ж': 'Ž', 'З': 'Z', 'И': 'I', 'Й': 'J', 'К': 'K', 'Л': 'L', 'М': 'M', 
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 
    'Ф': 'F', 'Х': 'X', 'Ц': 'C', 'Ч': 'Č', 'Ш': 'Š', 'Щ': 'Ŝ', 'Ъ': '″', 
    'Ы': 'Y', 'Ь': '′', 'Э': 'È', 'Ю': 'Ju', 'Я': 'Ja'
}

# Обратное отображение для научной транслитерации
SCIENTIFIC_EN_TO_RU_MAP = {
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е',
    'ž': 'ж', 'z': 'з', 'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л',
    'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с',
    't': 'т', 'u': 'у', 'f': 'ф', 'x': 'х', 'c': 'ц', 'č': 'ч',
    'š': 'ш', 'ŝ': 'щ', '″': 'ъ', 'y': 'ы', '′': 'ь', 'è': 'э',
    'ju': 'ю', 'ja': 'я', 'ë': 'ё',
    # Заглавные буквы
    'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Е',
    'Ž': 'Ж', 'Z': 'З', 'I': 'И', 'J': 'Й', 'K': 'К', 'L': 'Л',
    'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р', 'S': 'С',
    'T': 'Т', 'U': 'У', 'F': 'Ф', 'X': 'Х', 'C': 'Ц', 'Č': 'Ч',
    'Š': 'Ш', 'Ŝ': 'Щ', 'Y': 'Ы', 'È': 'Э', 'Ju': 'Ю', 'Ja': 'Я',
    'Ë': 'Ё'
}

# Паспортная транслитерация (Приказ МИД РФ от 12.02.2020 № 2113)
PASSPORT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': 'ie', 
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'iu', 'я': 'ia',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E', 
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'I', 'К': 'K', 'Л': 'L', 'М': 'M', 
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': 'Ie', 
    'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Iu', 'Я': 'Ia'
}

# Обратное отображение для паспортной транслитерации
PASSPORT_EN_TO_RU_MAP = {
    # Составные символы (в порядке убывания длины)
    'shch': 'щ', 'Shch': 'Щ',
    'zh': 'ж', 'Zh': 'Ж',
    'kh': 'х', 'Kh': 'Х',
    'ts': 'ц', 'Ts': 'Ц',
    'ch': 'ч', 'Ch': 'Ч',
    'sh': 'ш', 'Sh': 'Ш',
    'yu': 'ю', 'Yu': 'Ю',
    'ya': 'я', 'Ya': 'Я',
    'iu': 'ю', 'Iu': 'Ю',
    'ia': 'я', 'Ia': 'Я',
    # Одиночные символы
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 
    'z': 'з', 'i': 'и', 'k': 'к', 'l': 'л', 'm': 'м', 
    'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 
    't': 'т', 'u': 'у', 'f': 'ф', 'e': 'е', 'y': 'й',
    # Заглавные буквы
    'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 
    'Z': 'З', 'I': 'И', 'K': 'К', 'L': 'Л', 'M': 'М',
    'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р', 'S': 'С', 
    'T': 'Т', 'U': 'У', 'F': 'Ф', 'E': 'Е', 'Y': 'Й'
}

# Создаем экземпляры стандартов
GOST_STANDARD = TransliterationStandard(
    "GOST", # 7.79-2000 система А
    "Российский стандарт транслитерации (система А с диакритическими знаками), ГОСТ 7.79-2000",
    GOST_779_MAP,
    GOST_EN_TO_RU_MAP
)

SCIENTIFIC_STANDARD = TransliterationStandard(
    "Scientific", 
    "Научная транслитерация (ISO/R 9:1995), используемая в лингвистике и научных работах",
    SCIENTIFIC_MAP,
    SCIENTIFIC_EN_TO_RU_MAP
)

PASSPORT_STANDARD = TransliterationStandard(
    "Passport", 
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
    if not text:
        return ""
        
    result = ""
    i = 0
    text_len = len(text)
    
    while i < text_len:
        # Проверяем составные символы (например, 'sh' -> 'ш')
        found = False
        # Сортируем ключи по длине в убывающем порядке для правильной обработки составных символов
        for en_seq in sorted(standard.en_to_ru_map.keys(), key=len, reverse=True):
            seq_len = len(en_seq)
            if i + seq_len <= text_len and text[i:i+seq_len].lower() == en_seq.lower():
                # Сохраняем регистр первой буквы
                if text[i].isupper():
                    result += standard.en_to_ru_map[en_seq].capitalize()
                else:
                    result += standard.en_to_ru_map[en_seq]
                i += seq_len
                found = True
                break
        
        if not found:
            # Если не нашли составной символ, обрабатываем одиночный
            char = text[i]
            char_lower = char.lower()
            if char_lower in standard.en_to_ru_map:
                if char.isupper():
                    result += standard.en_to_ru_map[char_lower].upper()
                else:
                    result += standard.en_to_ru_map[char_lower]
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
    Проверяет, является ли en_text валидной транслитерацией ru_text.
    
    :param ru_text: исходный текст на русском
    :param en_text: транслитерированный текст на английском
    :param standard: стандарт транслитерации (объект TransliterationStandard)
    :param threshold: порог схожести (от 0 до 1)
    :return: True, если транслитерация валидна, иначе False
    """
    if not ru_text or not en_text:
        return False
    
    # Определяем языки текстов
    ru_lang = detect_language(ru_text)
    en_lang = detect_language(en_text)
    
    if ru_lang != 'ru' or en_lang != 'en':
        return False
    
    # Транслитерируем русский текст и сравниваем с английским
    transliterated = transliterate_ru_to_en(ru_text, standard)
    
    # Нормализуем для сравнения
    transliterated = transliterated.lower().replace(' ', '')
    en_normalized = en_text.lower().replace(' ', '')
    
    # Вычисляем схожесть как отношение совпадающих символов
    match_count = sum(1 for a, b in zip(transliterated, en_normalized) if a == b)
    max_length = max(len(transliterated), len(en_normalized))
    
    if max_length == 0:
        return False
    
    similarity = match_count / max_length
    return similarity >= threshold


def normalize_name_ru(name):
    """
    Нормализует русское имя: приводит к нижнему регистру, удаляет лишние пробелы,
    заменяет 'ё' на 'е' и т.д.
    
    :param name: имя для нормализации
    :return: нормализованное имя
    """
    if not name:
        return ""
    
    # Приводим к нижнему регистру и удаляем лишние пробелы
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Заменяем 'ё' на 'е'
    normalized = normalized.replace('ё', 'е')
    
    return normalized


def normalize_name_en(name):
    """
    Нормализует английское имя: приводит к нижнему регистру, удаляет лишние пробелы и т.д.
    
    :param name: имя для нормализации
    :return: нормализованное имя
    """
    if not name:
        return ""
    
    # Приводим к нижнему регистру и удаляем лишние пробелы
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def get_all_possible_transliterations(text, from_lang='ru'):
    """
    Возвращает все возможные варианты транслитерации текста по всем доступным стандартам.
    
    :param text: исходный текст
    :param from_lang: язык исходного текста ('ru' или 'en')
    :return: словарь {название_стандарта: транслитерированный_текст}
    """
    result = {}
    
    for standard in STANDARDS:
        if from_lang == 'ru':
            result[standard.name] = transliterate_ru_to_en(text, standard)
        else:
            result[standard.name] = transliterate_en_to_ru(text, standard)
    
    return result


def get_best_transliteration_match(source_text, target_texts, from_lang='ru'):
    """
    Находит наиболее вероятный вариант транслитерации из списка возможных.
    
    :param source_text: исходный текст
    :param target_texts: список возможных транслитераций
    :param from_lang: язык исходного текста ('ru' или 'en')
    :return: кортеж (лучший_вариант, оценка_схожести)
    """
    if not source_text or not target_texts:
        return None, 0.0
    
    best_match = None
    best_score = 0.0
    
    # Получаем все возможные транслитерации исходного текста
    all_transliterations = {}
    for standard in STANDARDS:
        if from_lang == 'ru':
            trans_text = transliterate_ru_to_en(source_text, standard)
        else:
            trans_text = transliterate_en_to_ru(source_text, standard)
        
        all_transliterations[standard.name] = trans_text.lower()
    
    # Для каждого текста из target_texts находим наилучшее соответствие
    for target in target_texts:
        if not target:
            continue
            
        target_lower = target.lower()
        
        for standard_name, trans_text in all_transliterations.items():
            # Вычисляем схожесть как отношение совпадающих символов
            match_count = sum(1 for a, b in zip(trans_text, target_lower) if a == b)
            max_length = max(len(trans_text), len(target_lower))
            
            if max_length == 0:
                continue
                
            similarity = match_count / max_length
            
            if similarity > best_score:
                best_score = similarity
                best_match = target
    
    return best_match, best_score 