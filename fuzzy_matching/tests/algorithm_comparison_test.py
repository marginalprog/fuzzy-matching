from thefuzz import fuzz

def compare_algorithms(str1, str2):
    print(f"\nСравнение: \"{str1}\" vs \"{str2}\"")
    print(f"Левенштейн (ratio):     {fuzz.ratio(str1, str2)}%")
    print(f"PARTIAL_RATIO:          {fuzz.partial_ratio(str1, str2)}%")
    print(f"TOKEN_SORT_RATIO:       {fuzz.token_sort_ratio(str1, str2)}%")
    print(f"TOKEN_SET_RATIO:        {fuzz.token_set_ratio(str1, str2)}%")
    print(f"WRatio:                 {fuzz.WRatio(str1, str2)}%")

# Тест 1: Перестановка слов
compare_algorithms("Ivan Petrov", "Petrov Ivan")

# Тест 2: Сокращения
compare_algorithms("Moscow State University named after Lomonosov", "Lomonosov MSU")

# Тест 3: Уменьшительные имена
compare_algorithms("Alexander", "Alex")

# Тест 4: Разные форматы написания
compare_algorithms("Saint-Petersburg State University", "St. Petersburg University")

# Тест 5: Опечатки
compare_algorithms("programming", "programing") 