"""
🧪 ТЕСТ API - Простой пример
"""

import requests
import json

print("=" * 60)
print("🧪 ТЕСТИРУЕМ API")
print("=" * 60)

# 1. Проверка здоровья API
print("\n1️⃣ Проверка здоровья API...")
response = requests.get("http://localhost:8000/health")
print(f"   Статус: {response.status_code}")
print(f"   Ответ: {response.json()}")

# 2. Быстрый поиск
print("\n2️⃣ Быстрый поиск вакансий...")
response = requests.post(
    "http://localhost:8000/api/search-quick",
    params={
        "keywords": "оператор CRM входящие",
        "max_results": 5
    }
)

data = response.json()

if data['success']:
    print(f"   ✅ Найдено: {data['count']} вакансий")
    print(f"\n{'='*60}")
    print("📋 РЕЗУЛЬТАТЫ:")
    print('='*60)
    
    for i, vacancy in enumerate(data['vacancies'], 1):
        print(f"\n{i}. {vacancy['название']}")
        print(f"   🏢 Компания: {vacancy['компания']}")
        print(f"   💰 Зарплата: {vacancy['оплата']}")
        print(f"   📅 Опыт: {vacancy['опыт']}")
        print(f"   🔗 Ссылка: {vacancy['ссылка']}")
        print(f"   📝 Описание: {vacancy['описание'][:150]}...")
else:
    print(f"   ❌ Ошибка: {data}")

print(f"\n{'='*60}")
print("✅ ТЕСТ ЗАВЕРШЕН!")
print('='*60)
print("\n💡 API работает! Теперь можно:")
print("   1. Открыть http://localhost:8000/docs")
print("   2. Тестировать через Swagger UI")
print("   3. Интегрировать с GPT")
print("   4. Использовать в n8n")

