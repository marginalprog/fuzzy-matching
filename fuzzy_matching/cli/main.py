#!/usr/bin/env python
"""
Основной CLI скрипт для запуска библиотеки fuzzy_matching.
Этот скрипт служит точкой входа для пользователей и показывает интерактивное меню.
"""

import os
import sys


def show_menu():
    """Отображает интерактивное меню с доступными опциями."""
    print("\n========== Fuzzy Matching ==========")
    print("1. Запустить интерактивное демо")
    print("2. Сопоставить данные из CSV/JSON")
    print("3. Транслитерировать данные")
    print("4. Сгенерировать тестовые данные")
    print("5. Запустить пример с техническими данными")
    print("6. Показать справку и рекомендации")
    print("0. Выход")
    print("===================================")
    choice = input("Выберите опцию (0-6): ")
    return choice


def main():
    """Основная функция обработки меню."""
    try:
        while True:
            choice = show_menu()
            
            if choice == '0':
                print("До свидания!")
                sys.exit(0)
            
            elif choice == '1':
                # Запуск интерактивного демо
                from fuzzy_matching.cli.demo import main as demo_main
                demo_main()
            
            elif choice == '2':
                # Вызываем CLI для сопоставления данных
                print("\nЗапуск утилиты сопоставления данных...")
                print("Пример команды:")
                print("""python -m fuzzy_matching.cli.process_data --mode match \\
    --input1 data/file1.json --format1 json \\
    --input2 data/file2.json --format2 json \\
    --match-fields "Фамилия:0.6:true:TOKEN_SORT,Имя:0.3:true:PARTIAL_RATIO,Отчество:0.1:true:RATIO" \\
    --threshold 0.7 \\
    --output-matches matches.json \\
    --output-consolidated consolidated.json \\
    --verbose""")
                cmd = input("\nВведите команду или нажмите Enter для возврата в меню: ")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '3':
                # Вызываем CLI для транслитерации данных
                print("\nЗапуск утилиты транслитерации данных...")
                print("Пример команды:")
                print("""python -m fuzzy_matching.cli.process_data --mode transliterate \\
    --input1 data/input.json --format1 json \\
    --target-lang en \\
    --transliterate-fields "Фамилия,Имя,Отчество" \\
    --output-consolidated transliterated.json \\
    --verbose""")
                cmd = input("\nВведите команду или нажмите Enter для возврата в меню: ")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '4':
                # Вызываем CLI для генерации тестовых данных
                print("\nЗапуск утилиты генерации тестовых данных...")
                print("Пример команды:")
                print("""python -m fuzzy_matching.cli.process_data --mode generate \\
    --output-original original.json \\
    --output-variant variant.json \\
    --record-count 100 \\
    --typo-probability 0.1 \\
    --field-swap-probability 0.05 \\
    --verbose""")
                cmd = input("\nВведите команду или нажмите Enter для возврата в меню: ")
                if cmd.strip():
                    os.system(cmd)
            
            elif choice == '5':
                # Запуск примера с техническими данными
                print("\nЗапуск примера с техническими данными...")
                os.system("python -m fuzzy_matching.examples.technical_example")
            
            elif choice == '6':
                # Показываем справку и рекомендации
                print("\n=== Рекомендации по выбору алгоритмов ===")
                print("В библиотеке доступны следующие алгоритмы нечеткого сопоставления:")
                print("- RATIO: Базовый алгоритм Левенштейна (хорош для коротких строк и точных совпадений)")
                print("- PARTIAL_RATIO: Находит наилучшее совпадение подстроки (подходит для имен: Иван/Ваня)")
                print("- TOKEN_SORT: Сортирует слова перед сравнением (хорош для адресов, двойных фамилий)")
                print("- TOKEN_SET: Сравнивает множества слов (лучший для перемешанных слов и порядка)")
                print("- WRatio: Взвешенный комбинированный результат (универсальный алгоритм)")
                
                print("\nРекомендуемые алгоритмы для разных типов данных:")
                print("Персональные данные:")
                print("- Имена: PARTIAL_RATIO (учитывает уменьшительные формы)")
                print("- Фамилии: TOKEN_SORT (хорошо работает с составными фамилиями)")
                print("- Отчества: RATIO (обычно требуется точное совпадение)")
                print("- Адреса: TOKEN_SET (учитывает перестановку слов)")
                
                print("\nБизнес-данные:")
                print("- Названия компаний: TOKEN_SET (порядок слов часто меняется, например 'ООО Ромашка' и 'Ромашка ООО')")
                print("- Юридические названия: TOKEN_SORT (важен порядок слов, но могут быть сокращения)")
                print("- ИНН/КПП/ОГРН: RATIO (требуется точное совпадение)")
                
                print("\nТехнические данные:")
                print("- Серийные номера: RATIO (требуется точность, допустимы небольшие опечатки)")
                print("- Артикулы товаров: RATIO (требуется точность)")
                print("- Технические описания: TOKEN_SET (порядок элементов может варьироваться)")
                
                input("\nНажмите Enter для возврата в меню...")
            
            else:
                print("\nНеверный выбор. Пожалуйста, выберите опцию от 0 до 6.")
                input("Нажмите Enter для продолжения...")
    
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"\nПроизошла ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 