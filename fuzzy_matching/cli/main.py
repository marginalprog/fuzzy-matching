#!/usr/bin/env python
"""
Основной CLI скрипт для запуска библиотеки fuzzy_matching.
Этот скрипт служит точкой входа для пользователей и показывает интерактивное меню.
"""

import os
import sys
from prettytable import PrettyTable

from fuzzy_matching.core.match_config_classes import (
    MatchConfig, MatchFieldConfig, TransliterationConfig,
    FuzzyAlgorithm
)
from fuzzy_matching.core.data_matcher import DataMatcher
from fuzzy_matching.cli.demo import (
    run_personal_data_demo,
    run_business_data_demo,
    run_transliteration_demo,
    run_technical_data_demo
)

# Классы для цветного вывода в терминале
class Colors:
    """Класс с ANSI-кодами цветов для терминала"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def show_menu():
    """Отображает интерактивное меню с доступными опциями."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}========== Fuzzy Matching =========={Colors.ENDC}")
    print(f"{Colors.CYAN}1. Запустить интерактивное демо{Colors.ENDC}")
    print(f"{Colors.CYAN}2. Сопоставить данные из CSV/JSON{Colors.ENDC}")
    print(f"{Colors.CYAN}3. Транслитерировать данные{Colors.ENDC}")
    print(f"{Colors.CYAN}4. Сгенерировать тестовые данные{Colors.ENDC}")
    print(f"{Colors.CYAN}5. Показать справку и рекомендации{Colors.ENDC}")
    print(f"{Colors.RED}0. Выход{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}==================================={Colors.ENDC}")
    choice = input(f"{Colors.YELLOW}Выберите опцию (0-5): {Colors.ENDC}")
    return choice


def main():
    """Основная функция обработки меню."""
    try:
        while True:
            choice = show_menu()
            
            if choice == '0':
                print(f"{Colors.GREEN}До свидания!{Colors.ENDC}")
                sys.exit(0)
            
            elif choice == '1':
                # Запуск интерактивного демо
                show_demo_menu()
            
            elif choice == '2':
                # Вызываем CLI для сопоставления данных
                print(f"\n{Colors.BOLD}Запуск утилиты сопоставления данных...{Colors.ENDC}")
                print(f"{Colors.YELLOW}Пример 1: Сопоставление русскоязычных данных с русскоязычными полями{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/test_ru_ru_original.json --format1 json --input2 data/input/test_ru_ru_variant.json --format2 json --match-fields \"Фамилия:0.4:false:TOKEN_SORT,Имя:0.3:false:PARTIAL_RATIO,Отчество:0.2:false:RATIO,email:0.1:false:RATIO\" --threshold 0.7 --output-matches data/output/matches.json --output-path data/output/consolidated.json --transliteration-standard \"Passport\" --verbose{Colors.ENDC}", end="")

                print(f"\n\n{Colors.YELLOW}Пример 2: Сопоставление англоязычных данных с англоязычными полями{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/test_en_en_original.json --format1 json --input2 data/input/test_en_en_variant.json --format2 json --match-fields \"LastName:0.4:false:TOKEN_SORT,FirstName:0.3:false:PARTIAL_RATIO,MiddleName:0.2:false:RATIO,email:0.1:false:RATIO\" --threshold 0.7 --output-matches data/output/matches.json --output-path data/output/consolidated.json --transliteration-standard \"Passport\" --verbose{Colors.ENDC}", end="")

                cmd = input(f"\n\n{Colors.YELLOW}Введите команду или нажмите {Colors.BOLD}Enter{Colors.ENDC}{Colors.YELLOW} для возврата в меню: {Colors.ENDC}")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '3':
                # Вызываем CLI для транслитерации данных
                print(f"\n{Colors.BOLD}Запуск утилиты транслитерации данных...{Colors.ENDC}")
                print(f"\n{Colors.YELLOW}Пример 1: Транслитерация с русского на английский (поддерживаются стандарты ГОСТ, Научная, Паспортная):{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_ru_ru_original.json --format1 json --target-lang en --transliterate-fields \"Фамилия,Имя,Отчество\" --transliteration-standard \"Passport\" --output-path data/output/transliterated_en.json --verbose{Colors.ENDC}", end="")
                
                print(f"\n\n{Colors.YELLOW}Пример 2: Обратная транслитерация с английского на русский (поддерживается только ГОСТ):{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_en_en_original.json --format1 json --target-lang ru --transliterate-fields \"LastName,FirstName,MiddleName\" --transliteration-standard \"GOST\" --output-path data/output/transliterated_ru.json --verbose{Colors.ENDC}", end="")
                
                cmd = input(f"\n\n{Colors.YELLOW}Введите команду или нажмите {Colors.BOLD}Enter{Colors.ENDC}{Colors.YELLOW} для возврата в меню: {Colors.ENDC}")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '4':
                # Вызываем CLI для генерации тестовых данных
                print(f"\n{Colors.BOLD}Запуск утилиты генерации тестовых данных...{Colors.ENDC}")
                print(f"{Colors.YELLOW}Пример 1: Генерация данных на русском языке с русскими названиями полей:{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.12 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.15 --generate-fields \"id,Фамилия,Имя,Отчество,email\" --language ru --field-names-format ru --verbose{Colors.ENDC}", end="")
                
                print(f"\n\n{Colors.YELLOW}Пример 2: Генерация данных на русском языке с английскими названиями полей:{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.12 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.15 --generate-fields \"id,LastName,FirstName,MiddleName,email\" --language ru --field-names-format en --verbose{Colors.ENDC}", end="")
                
                print(f"\n\n{Colors.YELLOW}Пример 3: Генерация данных на английском языке с английскими названиями полей:{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.12 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.15 --generate-fields \"id,LastName,FirstName,MiddleName,email\" --language en --field-names-format en --verbose{Colors.ENDC}", end="")
                
                cmd = input(f"\n\n{Colors.YELLOW}Введите команду или нажмите {Colors.BOLD}Enter{Colors.ENDC}{Colors.YELLOW} для возврата в меню: {Colors.ENDC}")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '5':
                # Показываем справку и рекомендации
                print(f"\n{Colors.HEADER}{Colors.BOLD}=== Рекомендации по выбору алгоритмов ==={Colors.ENDC}")
                print(f"{Colors.BOLD}В библиотеке доступны следующие алгоритмы нечеткого сопоставления:{Colors.ENDC}")
                print(f"{Colors.CYAN}- RATIO: {Colors.ENDC}Базовый алгоритм Левенштейна (хорош для коротких строк и точных совпадений)")
                print(f"{Colors.CYAN}- PARTIAL_RATIO: {Colors.ENDC}Находит наилучшее совпадение подстроки (подходит для имен: Иван/Ваня)")
                print(f"{Colors.CYAN}- TOKEN_SORT: {Colors.ENDC}Сортирует слова перед сравнением (хорош для адресов, двойных фамилий)")
                print(f"{Colors.CYAN}- TOKEN_SET: {Colors.ENDC}Сравнивает множества слов (лучший для перемешанных слов и порядка)")
                print(f"{Colors.CYAN}- WRatio: {Colors.ENDC}Взвешенный комбинированный результат (универсальный алгоритм)")
                
                print(f"\n{Colors.BOLD}Рекомендуемые алгоритмы для разных типов данных:{Colors.ENDC}")
                print(f"{Colors.YELLOW}Персональные данные:{Colors.ENDC}")
                print(f"- Имена: {Colors.GREEN}PARTIAL_RATIO{Colors.ENDC} (учитывает уменьшительные формы)")
                print(f"- Фамилии: {Colors.GREEN}TOKEN_SORT{Colors.ENDC} (хорошо работает с составными фамилиями)")
                print(f"- Отчества: {Colors.GREEN}RATIO{Colors.ENDC} (обычно требуется точное совпадение)")
                print(f"- Адреса: {Colors.GREEN}TOKEN_SET{Colors.ENDC} (учитывает перестановку слов)")
                
                print(f"\n{Colors.YELLOW}Бизнес-данные:{Colors.ENDC}")
                print(f"- Названия компаний: {Colors.GREEN}TOKEN_SET{Colors.ENDC} (порядок слов часто меняется, например 'ООО Ромашка' и 'Ромашка ООО')")
                print(f"- Юридические названия: {Colors.GREEN}TOKEN_SORT{Colors.ENDC} (важен порядок слов, но могут быть сокращения)")
                print(f"- ИНН/КПП/ОГРН: {Colors.GREEN}RATIO{Colors.ENDC} (требуется точное совпадение)")
                
                print(f"\n{Colors.YELLOW}Технические данные:{Colors.ENDC}")
                print(f"- Серийные номера: {Colors.GREEN}RATIO{Colors.ENDC} (требуется точность, допустимы небольшие опечатки)")
                print(f"- Артикулы товаров: {Colors.GREEN}RATIO{Colors.ENDC} (требуется точность)")
                print(f"- Технические описания: {Colors.GREEN}TOKEN_SET{Colors.ENDC} (порядок элементов может варьироваться)")
                
                print(f"\n{Colors.HEADER}{Colors.BOLD}=== Параметры генератора тестовых данных ==={Colors.ENDC}")
                print(f"{Colors.BOLD}python -m fuzzy_matching.cli.process_data {Colors.RED}--mode generate*{Colors.ENDC}")
                print(f"  {Colors.RED}--output-original* {Colors.CYAN}[путь]{Colors.ENDC}          - путь сохранения оригинальных записей")
                print(f"  {Colors.RED}--output-variant* {Colors.CYAN}[путь]{Colors.ENDC}           - путь сохранения изменённых записей")
                print(f"  {Colors.RED}--output-format* {Colors.CYAN}[json|csv]{Colors.ENDC}        - формат сохранения данных")
                print(f"  {Colors.GREEN}--record-count {Colors.CYAN}[число]{Colors.ENDC}             - количество записей для генерации (по умолчанию 100)")
                print(f"  {Colors.GREEN}--double-char-probability {Colors.CYAN}[0-1]{Colors.ENDC}    - вероятность дублирования буквы (по умолчанию 0.1)")
                print(f"  {Colors.GREEN}--change-char-probability {Colors.CYAN}[0-1]{Colors.ENDC}    - вероятность замены буквы (по умолчанию 0.05)")
                print(f"  {Colors.GREEN}--change-name-probability {Colors.CYAN}[0-1]{Colors.ENDC}    - вероятность полной замены ФИО (по умолчанию 0.1)")
                print(f"  {Colors.GREEN}--change-domain-probability {Colors.CYAN}[0-1]{Colors.ENDC}  - вероятность изменения домена в email (по умолчанию 0.3)")
                print(f"  {Colors.GREEN}--double-number-probability {Colors.CYAN}[0-1]{Colors.ENDC}  - вероятность дублирования цифры в телефоне (по умолчанию 0.3)")
                print(f"  {Colors.GREEN}--suffix-probability {Colors.CYAN}[0-1]{Colors.ENDC}         - вероятность добавления суффикса к ФИО (по умолчанию 0.05)")
                print(f"  {Colors.GREEN}--swap-char-probability {Colors.CYAN}[0-1]{Colors.ENDC}      - вероятность перестановки символов (по умолчанию 0.1)")
                print(f"  {Colors.RED}--generate-fields* {Colors.CYAN}[список]{Colors.ENDC}        - список полей для генерации (например: id,Фамилия,Имя,Отчество,email)")
                print(f"  {Colors.GREEN}--language {Colors.CYAN}[ru|en]{Colors.ENDC}                 - язык генерируемых данных (по умолчанию ru)")
                print(f"  {Colors.GREEN}--field-names-format {Colors.CYAN}[ru|en]{Colors.ENDC}       - формат названий полей (по умолчанию соответствует языку)")
                print(f"  {Colors.GREEN}--verbose{Colors.ENDC}                          - показывает расширенные сведения о выполнении программы")

                print(f"\n{Colors.HEADER}{Colors.BOLD}=== Параметры транслитерации ==={Colors.ENDC}")
                print(f"{Colors.BOLD}python -m fuzzy_matching.cli.process_data {Colors.RED}--mode transliterate*{Colors.ENDC}")
                print(f"  {Colors.RED}--input1* {Colors.CYAN}[путь]{Colors.ENDC}                   - путь к входному файлу")
                print(f"  {Colors.RED}--format1* {Colors.CYAN}[json|csv]{Colors.ENDC}              - формат входного файла")
                print(f"  {Colors.RED}--target-lang* {Colors.CYAN}[ru|en]{Colors.ENDC}             - целевой язык транслитерации")
                print(f"  {Colors.RED}--transliterate-fields* {Colors.CYAN}[список]{Colors.ENDC}   - список полей для транслитерации")
                print(f"  {Colors.GREEN}--transliteration-standard {Colors.CYAN}[стандарт]{Colors.ENDC} - стандарт транслитерации (GOST/Passport, по умолчанию Passport)")
                print(f"  {Colors.RED}--output-path* {Colors.CYAN}[путь]{Colors.ENDC}              - путь для сохранения результата")
                print(f"  {Colors.GREEN}--verbose{Colors.ENDC}                          - показывает расширенные сведения о выполнении программы")

                print(f"\n{Colors.HEADER}{Colors.BOLD}=== Параметры сопоставления данных ==={Colors.ENDC}")
                print(f"{Colors.BOLD}python -m fuzzy_matching.cli.process_data {Colors.RED}--mode match*{Colors.ENDC}")
                print(f"  {Colors.RED}--input1* {Colors.CYAN}[путь]{Colors.ENDC}                   - путь к первому входному файлу")
                print(f"  {Colors.RED}--format1* {Colors.CYAN}[json|csv]{Colors.ENDC}              - формат первого входного файла")
                print(f"  {Colors.RED}--input2* {Colors.CYAN}[путь]{Colors.ENDC}                   - путь ко второму входному файлу")
                print(f"  {Colors.RED}--format2* {Colors.CYAN}[json|csv]{Colors.ENDC}              - формат второго входного файла")
                print(f"  {Colors.RED}--match-fields* {Colors.CYAN}[список]{Colors.ENDC}           - список полей для сопоставления в формате:")
                print(f"    {Colors.YELLOW}'поле:вес:транслитерация:алгоритм'{Colors.ENDC}")
                print(f"    где:")
                print(f"        - {Colors.RED}поле*{Colors.ENDC}: {Colors.CYAN}имя поля{Colors.ENDC}  (например, Фамилия)")
                print(f"        - {Colors.RED}вес*{Colors.ENDC}: {Colors.CYAN}вес поля от 0 до 1{Colors.ENDC}  (например, 0.4)")
                print(f"        - {Colors.GREEN}транслитерация{Colors.ENDC}: {Colors.CYAN}true/false{Colors.ENDC}  - применять ли транслитерацию (по умолчанию false)")
                print(f"        - {Colors.GREEN}алгоритм{Colors.ENDC}: {Colors.CYAN}RATIO/PARTIAL_RATIO/TOKEN_SORT/TOKEN_SET/WRatio{Colors.ENDC}  (по умолчанию TOKEN_SORT)")
                print(f"        Пример: {Colors.CYAN}\"Фамилия:0.4:true:TOKEN_SORT,Имя:0.3:false:PARTIAL_RATIO\"{Colors.ENDC}")
                print(f"  {Colors.GREEN}--threshold {Colors.CYAN}[0-1]{Colors.ENDC}                  - порог совпадения (по умолчанию 0.7)")
                print(f"  {Colors.GREEN}--transliteration-standard {Colors.CYAN}[стандарт]{Colors.ENDC} - стандарт транслитерации (GOST/Passport, по умолчанию Passport)")
                print(f"  {Colors.RED}--output-matches* {Colors.CYAN}[путь]{Colors.ENDC}           - путь для сохранения совпадений")
                print(f"  {Colors.RED}--output-path* {Colors.CYAN}[путь]{Colors.ENDC}              - путь для сохранения консолидированных данных")
                print(f"  {Colors.GREEN}--verbose{Colors.ENDC}                          - показывает расширенные сведения о выполнении программы")

                print(f"\n{Colors.YELLOW}Шаблоны команд:{Colors.ENDC}")
                print(f"\n{Colors.RED}Генерация данных:{Colors.ENDC}")
                print(f"1. Генерация русских данных:")
                print(f"   {Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.1 --generate-fields \"id,Фамилия,Имя,Отчество,email\" --language ru --field-names-format ru --verbose{Colors.ENDC}", end="")
                print(f"\n2. Генерация английских данных:")
                print(f"   {Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.1 --generate-fields \"id,LastName,FirstName,MiddleName,email\" --language ru --field-names-format en --verbose{Colors.ENDC}", end="")

                print(f"\n\n{Colors.RED}Транслитерация:{Colors.ENDC}")
                print(f"1. Транслитерация с русского на английский:")
                print(f"   {Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_ru_ru_original.json --format1 json --target-lang en --output-path data/output/transliterated_en.json --transliterate-fields \"Фамилия,Имя,Отчество\" --transliteration-standard \"Passport\" --verbose{Colors.ENDC}", end="")
                print(f"\n2. Обратная транслитерация с английского на русский:")
                print(f"   {Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_en_en_original.json --format1 json --target-lang ru --transliteration-standard \"Passport\" --transliterate-fields \"LastName,FirstName,MiddleName\" --output-path data/output/transliterated_ru.json --verbose{Colors.ENDC}", end="")

                print(f"\n\n{Colors.RED}Сопоставление данных:{Colors.ENDC}")
                print(f"1. Сопоставление персональных данных:")
                print(f"   {Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.json --format1 json --input2 data/input/variant.json --format2 json --output-matches data/output/matches.json --output-path data/output/consolidated.json --threshold 0.7 --match-fields \"Фамилия:0.4:true:TOKEN_SORT,Имя:0.3:true:PARTIAL_RATIO,Отчество:0.2:true:RATIO,email:0.1:false:RATIO\" --transliteration-standard \"Passport\" --verbose{Colors.ENDC}", end="")
                print(f"\n2. Сопоставление бизнес-данных:")
                print(f"   {Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/companies_original.json --format1 json --input2 data/input/companies_variant.json --format2 json --output-matches data/output/company_matches.json --output-path data/output/companies_consolidated.json --threshold 0.7 --transliteration-standard \"Passport\" --match-fields \"company_name:0.4:true:TOKEN_SET,legal_name:0.3:true:TOKEN_SORT,inn:0.2:false:RATIO,kpp:0.1:false:RATIO\" --verbose{Colors.ENDC}", end="")
                
                print(f"\n\n{Colors.YELLOW}Примечания:{Colors.ENDC}")
                print(f"1. Параметры, отмеченные {Colors.RED}красным цветом и *{Colors.ENDC}, являются обязательными")
                print(f"2. Параметры, отмеченные {Colors.GREEN}зеленым цветом{Colors.ENDC}, являются опциональными и имеют значения по умолчанию")
                print(f"3. В параметре {Colors.GREEN}--match-fields{Colors.ENDC} обязательными являются только {Colors.RED}поле{Colors.ENDC} и {Colors.RED}вес{Colors.ENDC}")
                print(f"4. Если не указан стандарт транслитерации ({Colors.GREEN}--transliteration-standard{Colors.ENDC}), используется {Colors.GREEN}Passport{Colors.ENDC}")
                print(f"5. Если не указан флаг транслитерации в {Colors.GREEN}--match-fields{Colors.ENDC}, используется {Colors.GREEN}false{Colors.ENDC}")
                print(f"6. Если не указан алгоритм в {Colors.GREEN}--match-fields{Colors.ENDC}, используется {Colors.GREEN}TOKEN_SORT{Colors.ENDC}")
                print(f"7. При генерации данных файлы именуются по шаблону: {Colors.CYAN}test_[формат_полей]_[язык]_[тип].json{Colors.ENDC}")
                print(f"   Например: {Colors.CYAN}test_ru_ru_original.json{Colors.ENDC}, {Colors.CYAN}test_en_ru_variant.json{Colors.ENDC}")
                
                input(f"\n{Colors.YELLOW}Нажмите {Colors.BOLD}Enter{Colors.ENDC}{Colors.YELLOW} для возврата в меню...{Colors.ENDC}")
            
            else:
                print(f"\n{Colors.RED}Неверный выбор. Пожалуйста, выберите опцию от 0 до 5.{Colors.ENDC}")
                input(f"{Colors.YELLOW}Нажмите {Colors.BOLD}Enter{Colors.ENDC}{Colors.YELLOW} для продолжения...{Colors.ENDC}")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Программа прервана пользователем.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Произошла ошибка: {str(e)}{Colors.ENDC}")
        sys.exit(1)


def show_demo_menu():
    """Показывает меню демо-режима"""
    while True:
        print(f"\n{Colors.CYAN}=== Демо-режим ==={Colors.ENDC}")
        print(f"{Colors.YELLOW}1. Запустить интерактивное демо{Colors.ENDC}")
        print(f"{Colors.YELLOW}2. Показать примеры использования{Colors.ENDC}")
        print(f"{Colors.YELLOW}3. Выход{Colors.ENDC}")
        
        choice = input(f"\n{Colors.GREEN}Выберите действие (1-3): {Colors.ENDC}")
        
        if choice == '1':
            show_interactive_demo()
        elif choice == '2':
            show_usage_examples()
        elif choice == '3':
            break
        else:
            print(f"{Colors.RED}Неверный выбор. Пожалуйста, выберите 1-3.{Colors.ENDC}")

def show_interactive_demo():
    """Показывает интерактивное демо"""
    while True:
        print(f"\n{Colors.CYAN}=== Интерактивное демо ==={Colors.ENDC}")
        print(f"{Colors.YELLOW}1. Демо сопоставления персональных данных{Colors.ENDC}")
        print(f"{Colors.YELLOW}2. Демо сопоставления бизнес-данных{Colors.ENDC}")
        print(f"{Colors.YELLOW}3. Демо сопоставления технических данных{Colors.ENDC}")
        print(f"{Colors.YELLOW}4. Демо транслитерации{Colors.ENDC}")
        print(f"{Colors.YELLOW}5. Назад{Colors.ENDC}")
        
        choice = input(f"\n{Colors.GREEN}Выберите тип демо (1-5): {Colors.ENDC}")
        
        if choice == '1':
            run_personal_data_demo()
        elif choice == '2':
            run_business_data_demo()
        elif choice == '3':
            run_technical_data_demo()
        elif choice == '4':
            run_transliteration_demo()
        elif choice == '5':
            break
        else:
            print(f"{Colors.RED}Неверный выбор. Пожалуйста, выберите 1-5.{Colors.ENDC}")

def show_usage_examples():
    """Показывает примеры использования"""
    print(f"\n{Colors.CYAN}=== Примеры использования ==={Colors.ENDC}")
    print(f"\n{Colors.YELLOW}1. Сопоставление персональных данных:{Colors.ENDC}")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.json --format1 json --input2 data/input/variant.json --format2 json --output-matches data/output/matches.json --output-path data/output/consolidated.json --threshold 0.7 --match-fields \"Фамилия:0.4:true:TOKEN_SORT,Имя:0.3:true:PARTIAL_RATIO,Отчество:0.2:true:RATIO,email:0.1:false:RATIO\" --transliteration-standard \"Passport\" --verbose{Colors.ENDC}", end="")
    
    print(f"\n\n{Colors.YELLOW}2. Сопоставление бизнес-данных:{Colors.ENDC}")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/companies_original.json --format1 json --input2 data/input/companies_variant.json --format2 json --output-matches data/output/company_matches.json --output-path data/output/companies_consolidated.json --threshold 0.7 --transliteration-standard \"Passport\" --match-fields \"company_name:0.4:true:TOKEN_SET,legal_name:0.3:true:TOKEN_SORT,inn:0.2:false:RATIO,kpp:0.1:false:RATIO\" --verbose{Colors.ENDC}", end="")
    
    print(f"\n\n{Colors.YELLOW}3. Транслитерация с русского на английский:{Colors.ENDC}")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_ru_ru_original.json --format1 json --target-lang en --output-path data/output/transliterated_en.json --transliterate-fields \"Фамилия,Имя,Отчество\" --transliteration-standard \"Passport\" --verbose{Colors.ENDC}", end="")
    
    print(f"\n2. Обратная транслитерация с английского на русский:")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/test_en_en_original.json --format1 json --target-lang ru --transliteration-standard \"GOST\" --transliterate-fields \"LastName,FirstName,MiddleName\" --name-fields \"LastName:LastName,FirstName:FirstName,MiddleName:MiddleName,email:email\" --output-path data/output/transliterated_ru.json --verbose{Colors.ENDC}", end="")
    
    print(f"\n\n{Colors.YELLOW}5. Генерация русских данных с русскими названиями полей:{Colors.ENDC}")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.1 --generate-fields \"id,Фамилия,Имя,Отчество,email\" --language ru --field-names-format ru --verbose{Colors.ENDC}", end="")
    print(f"\n{Colors.CYAN}# Результат: test_ru_ru_original.json и test_ru_ru_variant.json{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}6. Генерация русских данных с английскими названиями полей:{Colors.ENDC}")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.1 --generate-fields \"id,LastName,FirstName,MiddleName,email\" --language ru --field-names-format en --verbose{Colors.ENDC}", end="")
    print(f"\n{Colors.CYAN}# Результат: test_en_ru_original.json и test_en_ru_variant.json{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}7. Генерация английских данных с английскими названиями полей:{Colors.ENDC}")
    print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --output-original data/input --output-variant data/input --output-format json --record-count 100 --double-char-probability 0.2 --change-char-probability 0.2 --change-name-probability 0.05 --change-domain-probability 0.1 --double-number-probability 0.2 --suffix-probability 0.05 --swap-char-probability 0.1 --generate-fields \"id,LastName,FirstName,MiddleName,email\" --language en --field-names-format en --verbose{Colors.ENDC}", end="")
    print(f"\n{Colors.CYAN}# Результат: test_en_en_original.json и test_en_en_variant.json{Colors.ENDC}")
    
    print(f"\n\n{Colors.GREEN}Нажмите {Colors.BOLD}Enter{Colors.ENDC}{Colors.YELLOW} для возврата в главное меню...{Colors.ENDC}", end="")
    input()


if __name__ == "__main__":
    main() 