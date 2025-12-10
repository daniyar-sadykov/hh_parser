"""
ПРОСТОЙ ТЕСТ - прямой вызов HH.ru API
"""

import requests
import json


def test_hh_api():
    print("=" * 70)
    print("🧪 ТЕСТ HH.ru API")
    print("=" * 70)
    print()
    
    # Загружаем первую вакансию
    with open('vacancies_all.json', 'r', encoding='utf-8') as f:
        vacancies = json.load(f)
    
    vacancy = vacancies[0]
    
    print(f"📋 Тестовая вакансия:")
    print(f"   Название: {vacancy['название']}")
    print(f"   Компания: {vacancy['компания']}")
    print(f"   Ссылка: {vacancy['ссылка']}")
    
    # Извлекаем ID
    vacancy_id = vacancy['ссылка'].split('/')[-1].split('?')[0]
    print(f"\n🔑 ID вакансии: {vacancy_id}")
    
    # Запрос к API
    print(f"\n🌐 Запрос к HH.ru API...")
    
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✓ Ответ получен!")
            
            # Данные работодателя
            employer = data.get('employer', {})
            
            print(f"\n📌 Работодатель:")
            print(f"   Название: {employer.get('name', 'N/A')}")
            print(f"   Сайт: {employer.get('site_url', 'N/A')}")
            print(f"   HH.ru: {employer.get('alternate_url', 'N/A')}")
            
            # Ищем контакты в описании
            description = data.get('description', '')
            
            print(f"\n📝 Описание:")
            print(f"   Длина: {len(description)} символов")
            
            # Email
            import re
            emails = re.findall(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                description
            )
            
            if emails:
                print(f"\n📧 Найденные email:")
                for email in emails[:3]:
                    print(f"   {email}")
            
            # Телефоны
            phones = re.findall(
                r'(?:\+7|8)[\s-]?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}',
                description
            )
            
            if phones:
                print(f"\n📞 Найденные телефоны:")
                for phone in phones[:3]:
                    print(f"   {phone}")
            
            print(f"\n✅ HH.ru API РАБОТАЕТ!")
            
        else:
            print(f"\n❌ Ошибка: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")
    
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
    
    print("\n" + "=" * 70)
    print()


if __name__ == "__main__":
    test_hh_api()

