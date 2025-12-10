"""
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ API ПОИСКА КОНТАКТОВ
Простые и понятные примеры для быстрого старта
"""

import requests
import json


# ================================================================
# БАЗОВАЯ НАСТРОЙКА
# ================================================================

# URL вашего API (локальный или Railway)
API_URL = "http://localhost:8000"  # Для локального тестирования
# API_URL = "https://your-app.railway.app"  # Для продакшена


# ================================================================
# ПРИМЕР 1: Простой поиск контактов одной компании
# ================================================================

def example_1_simple_search():
    """Самый простой пример - ищем контакты одной компании"""
    
    print("=" * 70)
    print("ПРИМЕР 1: Простой поиск контактов")
    print("=" * 70)
    
    response = requests.post(
        f"{API_URL}/api/contacts/search-quick",
        params={
            "company_name": "Яндекс",
            "city": "Москва"
        }
    )
    
    data = response.json()
    
    if data['found']:
        print(f"\n✓ Найдены контакты для компании: {data['company_name']}")
        print(f"Источники: {', '.join(data['sources'])}")
        
        contacts = data['contacts']
        
        if contacts['phones']:
            print(f"\n📞 Телефоны:")
            for phone in contacts['phones']:
                print(f"   {phone}")
        
        if contacts['emails']:
            print(f"\n📧 Email:")
            for email in contacts['emails']:
                print(f"   {email}")
        
        if contacts['telegram']:
            print(f"\n💬 Telegram:")
            for tg in contacts['telegram']:
                print(f"   {tg}")
        
        if contacts['whatsapp']:
            print(f"\n📱 WhatsApp:")
            for wa in contacts['whatsapp']:
                print(f"   {wa}")
        
        if contacts['websites']:
            print(f"\n🌐 Сайты:")
            for site in contacts['websites']:
                print(f"   {site}")
        
        if contacts['address']:
            print(f"\n📍 Адрес: {contacts['address']}")
    else:
        print(f"✗ Контакты не найдены")
    
    print()


# ================================================================
# ПРИМЕР 2: Поиск контактов из списка вакансий
# ================================================================

def example_2_from_vacancies():
    """Ищем вакансии, затем контакты компаний"""
    
    print("=" * 70)
    print("ПРИМЕР 2: Поиск вакансий + контакты компаний")
    print("=" * 70)
    
    # Шаг 1: Ищем вакансии
    print("\nШаг 1: Ищем вакансии...")
    
    response = requests.post(
        f"{API_URL}/api/search-quick",
        params={
            "keywords": "Python разработчик",
            "region": 1,
            "max_results": 20  # Рекомендуется 20
        }
    )
    
    vacancies_data = response.json()
    vacancies = vacancies_data['vacancies']
    
    print(f"✓ Найдено вакансий: {len(vacancies)}")
    
    # Шаг 2: Извлекаем уникальные компании
    print("\nШаг 2: Извлекаем уникальные компании...")
    
    unique_companies = list(set([v['компания'] for v in vacancies]))
    print(f"✓ Уникальных компаний: {len(unique_companies)}")
    
    # Шаг 3: Ищем контакты для каждой компании
    print("\nШаг 3: Ищем контакты компаний...")
    
    contacts_results = []
    
    for i, company in enumerate(unique_companies[:5], 1):  # Первые 5 для примера
        print(f"  [{i}/5] {company}...", end=" ")
        
        response = requests.post(
            f"{API_URL}/api/contacts/search-quick",
            params={
                "company_name": company,
                "city": "Москва"
            }
        )
        
        contact_data = response.json()
        
        if contact_data['found']:
            print("✓")
            contacts_results.append(contact_data)
        else:
            print("✗")
    
    # Шаг 4: Показываем результаты
    print(f"\n✓ Найдены контакты для {len(contacts_results)} компаний")
    
    for contact in contacts_results[:3]:  # Показываем первые 3
        print(f"\n{contact['company_name']}:")
        if contact['contacts']['phones']:
            print(f"  Тел: {contact['contacts']['phones'][0]}")
        if contact['contacts']['emails']:
            print(f"  Email: {contact['contacts']['emails'][0]}")
    
    print()


# ================================================================
# ПРИМЕР 3: Пакетный поиск контактов
# ================================================================

def example_3_batch_search():
    """Пакетный поиск контактов для нескольких компаний сразу"""
    
    print("=" * 70)
    print("ПРИМЕР 3: Пакетный поиск контактов")
    print("=" * 70)
    
    # Список компаний для поиска
    companies = [
        {"company_name": "Яндекс", "city": "Москва"},
        {"company_name": "Сбер", "city": "Москва"},
        {"company_name": "МТС", "city": "Москва"},
        {"company_name": "ВКонтакте", "city": "Санкт-Петербург"},
        {"company_name": "Тинькoff", "city": "Москва"},
    ]
    
    print(f"\nИщем контакты для {len(companies)} компаний...")
    
    response = requests.post(
        f"{API_URL}/api/contacts/batch",
        json=companies
    )
    
    data = response.json()
    
    if data['success']:
        results = data['results']
        found_count = len([r for r in results if r['found']])
        
        print(f"✓ Найдены контакты: {found_count}/{len(results)}")
        
        for result in results:
            if result['found']:
                print(f"\n✓ {result['company_name']}")
                
                contacts = result['contacts']
                info = []
                
                if contacts['phones']:
                    info.append(f"тел: {len(contacts['phones'])}")
                if contacts['emails']:
                    info.append(f"email: {len(contacts['emails'])}")
                if contacts['telegram']:
                    info.append(f"TG: {len(contacts['telegram'])}")
                
                if info:
                    print(f"  Найдено: {', '.join(info)}")
            else:
                print(f"\n✗ {result['company_name']} - не найдено")
    
    print()


# ================================================================
# ПРИМЕР 4: Поиск с указанием вакансии
# ================================================================

def example_4_with_vacancy_link():
    """Поиск контактов с использованием ссылки на вакансию"""
    
    print("=" * 70)
    print("ПРИМЕР 4: Поиск контактов с ссылкой на вакансию")
    print("=" * 70)
    
    # Полный запрос с дополнительными параметрами
    response = requests.post(
        f"{API_URL}/api/contacts/search",
        json={
            "company_name": "Яндекс",
            "city": "Москва",
            "vacancy_link": "https://hh.ru/vacancy/123456"  # Опционально
        }
    )
    
    data = response.json()
    
    if data['found']:
        print(f"\n✓ {data['company_name']}")
        print(f"Источники данных: {', '.join(data['sources'])}")
        print(f"Из кеша: {'Да' if data['from_cache'] else 'Нет'}")
        
        # Дополнительная информация
        if data['additional_info']['full_name']:
            print(f"\nПолное название: {data['additional_info']['full_name']}")
        
        if data['additional_info']['hh_company_url']:
            print(f"HH.ru профиль: {data['additional_info']['hh_company_url']}")
        
        # Контакты
        contacts = data['contacts']
        
        print("\nКонтакты:")
        for contact_type in ['phones', 'emails', 'telegram', 'whatsapp', 'websites']:
            if contacts.get(contact_type):
                print(f"  {contact_type}: {contacts[contact_type]}")
    
    print()


# ================================================================
# ПРИМЕР 5: Статистика работы API
# ================================================================

def example_5_stats():
    """Получение статистики работы движка поиска контактов"""
    
    print("=" * 70)
    print("ПРИМЕР 5: Статистика API")
    print("=" * 70)
    
    response = requests.get(f"{API_URL}/api/contacts/stats")
    
    data = response.json()
    
    if data['success']:
        stats = data['stats']
        
        print(f"\n📊 Статистика:")
        print(f"  Всего поисков: {stats['total_searches']}")
        print(f"  Попаданий в кеш: {stats['cache_hits']} ({stats['cache_hit_rate']}%)")
        print(f"  Промахов кеша: {stats['cache_misses']}")
        print(f"  Размер кеша: {stats['cache_size']} записей")
        
        print(f"\n  API вызовы:")
        print(f"    - 2GIS: {stats['api_calls']['2gis']}")
        print(f"    - HH.ru: {stats['api_calls']['hh_ru']}")
        print(f"    - Парсинг сайтов: {stats['api_calls']['website_parses']}")
    
    print()


# ================================================================
# ПРИМЕР 6: Интеграция с N8N (симуляция)
# ================================================================

def example_6_n8n_simulation():
    """Симуляция работы N8N workflow"""
    
    print("=" * 70)
    print("ПРИМЕР 6: Симуляция N8N Workflow")
    print("=" * 70)
    
    # Симулируем получение сообщения от пользователя
    user_message = "Python разработчик Москва"
    
    print(f"\n1. Пользователь написал боту: '{user_message}'")
    
    # Шаг 1: Поиск вакансий
    print("\n2. Ищем вакансии через API...")
    vacancies_response = requests.post(
        f"{API_URL}/api/search-quick",
        params={
            "keywords": user_message,
            "max_results": 20
        }
    )
    
    vacancies = vacancies_response.json()['vacancies']
    print(f"   ✓ Найдено {len(vacancies)} вакансий")
    
    # Шаг 2: Извлекаем компании
    print("\n3. Извлекаем уникальные компании...")
    unique_companies = list(set([v['компания'] for v in vacancies]))
    print(f"   ✓ {len(unique_companies)} уникальных компаний")
    
    # Шаг 3: Ищем контакты
    print("\n4. Ищем контакты компаний...")
    
    companies_data = [
        {"company_name": company, "city": "Москва"}
        for company in unique_companies[:5]  # Первые 5 для примера
    ]
    
    contacts_response = requests.post(
        f"{API_URL}/api/contacts/batch",
        json=companies_data
    )
    
    contacts_results = contacts_response.json()['results']
    print(f"   ✓ Найдены контакты для {len([r for r in contacts_results if r['found']])} компаний")
    
    # Шаг 4: Формируем сообщение для пользователя
    print("\n5. Формируем ответ для пользователя...")
    
    message = f"🎉 Найдено {len(vacancies)} вакансий от {len(unique_companies)} компаний!\n\n"
    
    # Показываем первые 3 вакансии с контактами
    for i, vacancy in enumerate(vacancies[:3], 1):
        company_name = vacancy['компания']
        
        # Находим контакты для этой компании
        company_contacts = next(
            (r for r in contacts_results if r['company_name'] == company_name),
            None
        )
        
        message += f"📍 Вакансия {i}:\n"
        message += f"   {vacancy['название']}\n"
        message += f"   💼 {vacancy['компания']}\n"
        message += f"   💰 {vacancy['оплата']}\n"
        message += f"   🔗 {vacancy['ссылка']}\n"
        
        if company_contacts and company_contacts['found']:
            message += f"\n   📞 Контакты:\n"
            
            contacts = company_contacts['contacts']
            if contacts['phones']:
                message += f"   Тел: {contacts['phones'][0]}\n"
            if contacts['emails']:
                message += f"   Email: {contacts['emails'][0]}\n"
            if contacts['telegram']:
                message += f"   Telegram: {contacts['telegram'][0]}\n"
            if contacts['websites']:
                message += f"   Сайт: {contacts['websites'][0]}\n"
        
        message += "\n"
    
    print("\n6. Отправляем сообщение пользователю:")
    print("-" * 70)
    print(message)
    print("-" * 70)
    
    print("\n✅ Workflow выполнен успешно!")
    print()


# ================================================================
# ЗАПУСК ВСЕХ ПРИМЕРОВ
# ================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ API КОНТАКТОВ" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    try:
        # Проверяем доступность API
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API недоступен! Запустите сервер: python api.py")
            exit(1)
    except:
        print(f"❌ Не могу подключиться к {API_URL}")
        print("Запустите API сервер: python api.py")
        exit(1)
    
    print("✅ API работает!")
    print()
    
    # Запускаем примеры
    input("Нажмите Enter для запуска Примера 1...")
    example_1_simple_search()
    
    input("Нажмите Enter для запуска Примера 2...")
    example_2_from_vacancies()
    
    input("Нажмите Enter для запуска Примера 3...")
    example_3_batch_search()
    
    input("Нажмите Enter для запуска Примера 4...")
    example_4_with_vacancy_link()
    
    input("Нажмите Enter для запуска Примера 5...")
    example_5_stats()
    
    input("Нажмите Enter для запуска Примера 6...")
    example_6_n8n_simulation()
    
    print("=" * 70)
    print("✅ ВСЕ ПРИМЕРЫ ВЫПОЛНЕНЫ!")
    print("=" * 70)
    print()
    print("📖 Больше информации:")
    print("   - README.md - Общая документация")
    print("   - N8N_CONTACTS_INTEGRATION.md - Интеграция с N8N")
    print("   - API_ИНСТРУКЦИЯ.md - Полная документация API")
    print()

