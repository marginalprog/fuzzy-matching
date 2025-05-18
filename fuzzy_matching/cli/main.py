#!/usr/bin/env python
"""
Основной CLI скрипт для запуска библиотеки fuzzy_matching.
Этот скрипт служит точкой входа для пользователей и показывает интерактивное меню.
"""

import os
import sys

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
    print(f"{Colors.CYAN}5. Запустить пример с техническими данными{Colors.ENDC}")
    print(f"{Colors.CYAN}6. Показать справку и рекомендации{Colors.ENDC}")
    print(f"{Colors.RED}0. Выход{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}==================================={Colors.ENDC}")
    choice = input(f"{Colors.YELLOW}Выберите опцию (0-6): {Colors.ENDC}")
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
                from fuzzy_matching.cli.demo import main as demo_main
                demo_main()
            
            elif choice == '2':
                # Вызываем CLI для сопоставления данных
                print(f"\n{Colors.BOLD}Запуск утилиты сопоставления данных...{Colors.ENDC}")
                print(f"{Colors.YELLOW}Пример команды (скопируйте и вставьте в терминал):{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode match --input1 data/input/original.json --format1 json --input2 data/input/variant.json --format2 json --match-fields \"Фамилия:0.4:false:TOKEN_SORT,Имя:0.3:false:PARTIAL_RATIO,Отчество:0.2:false:RATIO,email:0.1:false:RATIO\" --threshold 0.7 --output-matches data/output/matches.json --output-consolidated data/output/consolidated.json --verbose{Colors.ENDC}")
                cmd = input(f"\n{Colors.YELLOW}Введите команду или нажмите Enter для возврата в меню: {Colors.ENDC}")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '3':
                # Вызываем CLI для транслитерации данных
                print(f"\n{Colors.BOLD}Запуск утилиты транслитерации данных...{Colors.ENDC}")
                print(f"{Colors.YELLOW}Пример 1: Транслитерация с русского на английский (поддерживаются стандарты ГОСТ, Научная, Паспортная):{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/russian_data.json --format1 json --target-lang en --transliterate-fields \"Фамилия,Имя,Отчество\" --output-consolidated data/output/transliterated_en.json --verbose{Colors.ENDC}")
                
                print(f"\n{Colors.YELLOW}Пример 2: Обратная транслитерация с английского на русский (поддерживается только Паспортный стандарт):{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode transliterate --input1 data/input/english_data.json --format1 json --target-lang ru --transliteration-standard \"Паспортная\" --transliterate-fields \"last_name,first_name,middle_name\" --name-fields \"last_name:Фамилия,first_name:Имя,middle_name:Отчество,email:email\" --output-consolidated data/output/transliterated_ru.json --verbose{Colors.ENDC}")
                
                cmd = input(f"\n{Colors.YELLOW}Введите команду или нажмите Enter для возврата в меню: {Colors.ENDC}")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '4':
                # Вызываем CLI для генерации тестовых данных
                print(f"\n{Colors.BOLD}Запуск утилиты генерации тестовых данных...{Colors.ENDC}")
                print(f"{Colors.YELLOW}Пример 1: Генерация данных на русском языке с русскими названиями полей:{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --record-count 5 --double-char-probability 0.05 --change-char-probability 0.02 --change-name-probability 0.1 --change-domain-probability 0.3 --double-number-probability 0.3 --suffix-probability 0.1 --generate-fields \"id,Фамилия,Имя,Отчество,Email\" --output-original data/input/test_original_ru.json --output-variant data/input/test_variant_ru.json --language ru --field-names-format ru --verbose{Colors.ENDC}")
                
                print(f"\n{Colors.YELLOW}Пример 2: Генерация данных на английском языке с английскими названиями полей:{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --record-count 5 --double-char-probability 0.05 --change-char-probability 0.02 --change-name-probability 0.1 --change-domain-probability 0.3 --double-number-probability 0.3 --suffix-probability 0.1 --generate-fields \"id,LastName,FirstName,MiddleName,Email\" --output-original data/input/test_original_en.json --output-variant data/input/test_variant_en.json --language en --field-names-format en --verbose{Colors.ENDC}")
                
                print(f"\n{Colors.YELLOW}Пример 3: Генерация данных на английском языке с русскими названиями полей:{Colors.ENDC}")
                print(f"{Colors.GREEN}python -m fuzzy_matching.cli.process_data --mode generate --record-count 5 --double-char-probability 0.05 --change-char-probability 0.02 --change-name-probability 0.1 --change-domain-probability 0.3 --double-number-probability 0.3 --suffix-probability 0.1 --generate-fields \"id,Фамилия,Имя,Отчество,Email\" --output-original data/input/test_original_en_ru.json --output-variant data/input/test_variant_en_ru.json --language en --field-names-format ru --verbose{Colors.ENDC}")
                
                cmd = input(f"\n{Colors.YELLOW}Введите команду или нажмите Enter для возврата в меню: {Colors.ENDC}")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '5':
                # Запуск примера с техническими данными
                print(f"\n{Colors.BOLD}Запуск примера с техническими данными...{Colors.ENDC}")
                os.system("python -m fuzzy_matching.examples.technical_example")
            
            elif choice == '6':
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
                
                input(f"\n{Colors.YELLOW}Нажмите Enter для возврата в меню...{Colors.ENDC}")
            
            else:
                print(f"\n{Colors.RED}Неверный выбор. Пожалуйста, выберите опцию от 0 до 6.{Colors.ENDC}")
                input(f"{Colors.YELLOW}Нажмите Enter для продолжения...{Colors.ENDC}")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Программа прервана пользователем.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Произошла ошибка: {str(e)}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main() 