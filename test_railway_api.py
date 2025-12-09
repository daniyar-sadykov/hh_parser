"""
🧪 ТЕСТ RAILWAY API
Проверка работы API на https://hhparser-production.up.railway.app
"""

import requests
import json

RAILWAY_URL = "https://hhparser-production.up.railway.app"

print("=" * 70)
print("🚀 ПРОВЕРКА RAILWAY API")
print("=" * 70)
print(f"📍 URL: {RAILWAY_URL}")
print("=" * 70)

# ========================================
# ТЕСТ 1: Health Check
# ========================================
print("\n1️⃣ ТЕСТ: Health Check...")
try:
    response = requests.get(f"{RAILWAY_URL}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Статус: {response.status_code}")
        print(f"   ✅ Ответ: {json.dumps(data, ensure_ascii=False)}")
    else:
        print(f"   ⚠️ Статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# ========================================
# ТЕСТ 2: Главная страница
# ========================================
print("\n2️⃣ ТЕСТ: Главная страница...")
try:
    response = requests.get(f"{RAILWAY_URL}/", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Статус: {response.status_code}")
        print(f"   ✅ API Version: {data.get('version')}")
    else:
        print(f"   ⚠️ Статус: {response.status_code}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# ========================================
# ТЕСТ 3: Список регионов
# ========================================
print("\n3️⃣ ТЕСТ: Список регионов...")
try:
    response = requests.get(f"{RAILWAY_URL}/api/regions", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Статус: {response.status_code}")
        print(f"   ✅ Регионов доступно: {len(data.get('regions', []))}")
        for region in data.get('regions', [])[:3]:
            print(f"      • {region['name']} (ID: {region['id']})")
    else:
        print(f"   ⚠️ Статус: {response.status_code}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# ========================================
# ТЕСТ 4: Быстрый поиск вакансий
# ========================================
print("\n4️⃣ ТЕСТ: Быстрый поиск вакансий...")
print("   🔍 Ищем: 'Python разработчик', макс 3 вакансии")
try:
    response = requests.post(
        f"{RAILWAY_URL}/api/search-quick",
        params={
            "keywords": "Python разработчик",
            "region": 1,
            "max_results": 3
        },
        timeout=60  # Парсинг может занять время
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Статус: {response.status_code}")
        print(f"   ✅ Найдено вакансий: {data.get('count', 0)}")
        
        if data.get('vacancies'):
            print(f"\n   {'='*66}")
            print("   📋 ПРИМЕРЫ ВАКАНСИЙ:")
            print(f"   {'='*66}")
            
            for i, vacancy in enumerate(data['vacancies'][:3], 1):
                print(f"\n   {i}. {vacancy.get('название', 'N/A')}")
                print(f"      🏢 Компания: {vacancy.get('компания', 'N/A')}")
                print(f"      💰 Зарплата: {vacancy.get('оплата', 'N/A')}")
                print(f"      📅 Опыт: {vacancy.get('опыт', 'N/A')}")
                print(f"      🔗 {vacancy.get('ссылка', 'N/A')}")
    else:
        print(f"   ⚠️ Статус: {response.status_code}")
        print(f"   Ответ: {response.text[:200]}")
except requests.exceptions.Timeout:
    print(f"   ⚠️ Timeout: Запрос занял больше 60 секунд")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# ========================================
# ИТОГИ
# ========================================
print("\n" + "=" * 70)
print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
print("=" * 70)
print(f"\n📍 Ваш API работает на: {RAILWAY_URL}")
print(f"📚 Документация Swagger: {RAILWAY_URL}/docs")
print(f"📖 Альтернативная документация: {RAILWAY_URL}/redoc")
print("\n💡 Теперь можно:")
print("   1. Открыть документацию в браузере")
print("   2. Использовать API из Python/JavaScript")
print("   3. Интегрировать с GPT")
print("   4. Подключить к n8n")
print("=" * 70)

