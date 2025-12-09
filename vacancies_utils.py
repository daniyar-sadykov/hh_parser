"""
Конвертер текстового файла с вакансиями в JSON формат
Для использования с company_contacts_finder.py
"""

import json
import re
from typing import List, Dict


def parse_vacancies_txt(txt_file: str) -> List[Dict]:
    """
    Парсинг текстового файла с вакансиями
    
    Args:
        txt_file: Путь к текстовому файлу
        
    Returns:
        Список словарей с вакансиями
    """
    print(f"📖 Читаем файл {txt_file}...")
    
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return []
    
    # Разделяем на блоки вакансий
    vacancy_blocks = re.split(r'={80,}', content)
    vacancies = []
    
    for block in vacancy_blocks:
        block = block.strip()
        if not block or 'ВАКАНСИЯ' not in block:
            continue
        
        vacancy = {}
        
        # Извлекаем поля
        name_match = re.search(r'Название:\s*(.+?)(?:\n|$)', block)
        if name_match:
            vacancy['название'] = name_match.group(1).strip()
        
        company_match = re.search(r'Компания:\s*(.+?)(?:\n|$)', block)
        if company_match:
            vacancy['компания'] = company_match.group(1).strip()
        
        salary_match = re.search(r'Оплата:\s*(.+?)(?:\n|$)', block)
        if salary_match:
            vacancy['оплата'] = salary_match.group(1).strip()
        
        link_match = re.search(r'Ссылка:\s*(.+?)(?:\n|$)', block)
        if link_match:
            vacancy['ссылка'] = link_match.group(1).strip()
        
        desc_match = re.search(r'Описание:\s*(.+?)(?:\n-{80,}|\n={80,}|$)', block, re.DOTALL)
        if desc_match:
            vacancy['описание'] = desc_match.group(1).strip()
        
        if vacancy.get('компания'):  # Добавляем только если есть компания
            vacancies.append(vacancy)
    
    print(f"✅ Найдено вакансий: {len(vacancies)}")
    return vacancies


def convert_txt_to_json(txt_file: str, json_file: str):
    """
    Конвертировать TXT файл в JSON
    
    Args:
        txt_file: Входной текстовый файл
        json_file: Выходной JSON файл
    """
    print("=" * 60)
    print("🔄 КОНВЕРТЕР TXT → JSON")
    print("=" * 60)
    print()
    
    vacancies = parse_vacancies_txt(txt_file)
    
    if vacancies:
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(vacancies, f, ensure_ascii=False, indent=2)
            print(f"💾 Сохранено в {json_file}")
            print()
            print("=" * 60)
            print("✅ ГОТОВО!")
            print("=" * 60)
            print()
            print(f"Теперь можно использовать файл {json_file}")
            print("с company_contacts_finder.py")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    else:
        print("❌ Вакансии не найдены")


def extract_companies_list(json_file: str, output_file: str = "companies_list.txt"):
    """
    Извлечь список уникальных компаний из JSON файла
    
    Args:
        json_file: JSON файл с вакансиями
        output_file: Текстовый файл со списком компаний
    """
    print("=" * 60)
    print("📋 ИЗВЛЕЧЕНИЕ СПИСКА КОМПАНИЙ")
    print("=" * 60)
    print()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            vacancies = json.load(f)
        
        companies = set()
        for vacancy in vacancies:
            company = vacancy.get('компания', '').strip()
            if company:
                companies.add(company)
        
        companies = sorted(list(companies))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, company in enumerate(companies, 1):
                f.write(f"{i}. {company}\n")
        
        print(f"✅ Найдено уникальных компаний: {len(companies)}")
        print(f"💾 Список сохранен в {output_file}")
        print()
        print("=" * 60)
        print("✅ ГОТОВО!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def main():
    """Основная функция"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "УТИЛИТЫ ДЛЯ РАБОТЫ С ВАКАНСИЯМИ" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    print("Выберите действие:")
    print()
    print("1. Конвертировать TXT в JSON")
    print("2. Извлечь список компаний из JSON")
    print("3. Выход")
    print()
    
    choice = input("Ваш выбор (1-3): ").strip()
    print()
    
    if choice == '1':
        txt_file = input("Путь к TXT файлу [vacancies_all.txt]: ").strip()
        if not txt_file:
            txt_file = "vacancies_all.txt"
        
        json_file = input("Имя JSON файла [vacancies_converted.json]: ").strip()
        if not json_file:
            json_file = "vacancies_converted.json"
        
        print()
        convert_txt_to_json(txt_file, json_file)
        
    elif choice == '2':
        json_file = input("Путь к JSON файлу [vacancies_all.json]: ").strip()
        if not json_file:
            json_file = "vacancies_all.json"
        
        output_file = input("Имя выходного файла [companies_list.txt]: ").strip()
        if not output_file:
            output_file = "companies_list.txt"
        
        print()
        extract_companies_list(json_file, output_file)
        
    elif choice == '3':
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()
