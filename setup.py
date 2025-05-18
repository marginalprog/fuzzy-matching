from setuptools import setup, find_packages

setup(
    name="fuzzy_matching",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rapidfuzz",
        "pandas",
        "prettytable",
        "faker",
        "gender_guesser",
        "matplotlib",
        "numpy",
    ],
    author="marginalprog",
    author_email="author@example.com",
    description="Библиотека для нечеткого сопоставления данных с поддержкой транслитерации",
    keywords="fuzzy matching, transliteration, data matching",
    python_requires=">=3.7",
) 