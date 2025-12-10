"""
ЛОКАЛЬНЫЙ ТЕСТ ПОИСКА КОНТАКТОВ
Использует существующие вакансии из проекта
"""

import json
from contacts_search_engine import ContactsSearchEngine
from datetime import datetime


def main():
    print("=" * 70)
    print("🧪 ЛОКАЛЬНЫЙ ТЕСТ ПОИСКА КОНТАКТОВ")
    print("=" * 70)
    print()
    
    # Загружаем вакансии
    print("📖 Загрузка вакансий из vacancies_all.json...")
    
    try:
        with open('vacancies_all.json', 'r', encoding='utf-8') as f:
            vacancies = json.load(f)
        
        print(f"✓ Загружено {len(vacancies)} вакансий")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return
    
    # Извлекаем уникальные компании
    print("\n📊 Извлечение уникальных компаний...")
    
    companies = []
    seen = set()
    
    for vacancy in vacancies:
        company = vacancy.get('компания', '').strip()
        if company and company not in seen:
            seen.add(company)
            companies.append(company)
        
        # Останавливаемся на 10 компаниях
        if len(companies) >= 10:
            break
    
    print(f"✓ Найдено {len(companies)} уникальных компаний")
    print("\nКомпании для теста:")
    for i, company in enumerate(companies, 1):
        print(f"  {i}. {company}")
    
    # Инициализируем движок поиска
    print("\n🔧 Инициализация движка поиска контактов...")
    
    API_KEY_2GIS = "75730e35-2767-46d6-b42b-548b4acae13e"
    
    engine = ContactsSearchEngine(
        api_key_2gis=API_KEY_2GIS,
        enable_2gis=True,
        enable_hh=True,
        enable_website_parsing=True
    )
    
    print("✓ Движок инициализирован")
    print(f"  - 2GIS: {'✓' if engine.enable_2gis else '✗'}")
    print(f"  - HH.ru: {'✓' if engine.enable_hh else '✗'}")
    print(f"  - Парсинг сайтов: {'✓' if engine.enable_website_parsing else '✗'}")
    
    # Ищем контакты
    print("\n" + "=" * 70)
    print("🔍 ПОИСК КОНТАКТОВ")
    print("=" * 70)
    print()
    
    results = []
    start_time = datetime.now()
    
    for i, company in enumerate(companies, 1):
        print(f"[{i}/10] {company}...", end=" ", flush=True)
        
        try:
            result = engine.search_company(
                company_name=company,
                city="Москва"
            )
            
            results.append(result)
            
            if result['found']:
                sources = ', '.join(result['sources'])
                
                contacts_info = []
                if result['contacts']['phones']:
                    contacts_info.append(f"тел:{len(result['contacts']['phones'])}")
                if result['contacts']['emails']:
                    contacts_info.append(f"email:{len(result['contacts']['emails'])}")
                if result['contacts']['telegram']:
                    contacts_info.append(f"TG:{len(result['contacts']['telegram'])}")
                if result['contacts']['whatsapp']:
                    contacts_info.append(f"WA:{len(result['contacts']['whatsapp'])}")
                if result['contacts']['websites']:
                    contacts_info.append(f"web:{len(result['contacts']['websites'])}")
                
                info = f"✓ [{sources}] {', '.join(contacts_info)}"
                if result['from_cache']:
                    info += " [cache]"
                
                print(info)
            else:
                print("✗ не найдено")
        
        except Exception as e:
            print(f"⚠️ ошибка: {e}")
            results.append({
                'company_name': company,
                'found': False,
                'error': str(e)
            })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Детальные результаты
    print("\n" + "=" * 70)
    print("📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        if not result.get('found'):
            continue
        
        print(f"\n{i}. {result['company_name']}")
        print(f"   Источники: {', '.join(result['sources'])}")
        
        contacts = result['contacts']
        
        if contacts['phones']:
            print(f"   📞 Телефоны:")
            for phone in contacts['phones'][:2]:
                print(f"      {phone}")
        
        if contacts['emails']:
            print(f"   📧 Email:")
            for email in contacts['emails'][:2]:
                print(f"      {email}")
        
        if contacts['telegram']:
            print(f"   💬 Telegram:")
            for tg in contacts['telegram']:
                print(f"      {tg}")
        
        if contacts['whatsapp']:
            print(f"   📱 WhatsApp:")
            for wa in contacts['whatsapp']:
                print(f"      {wa}")
        
        if contacts['websites']:
            print(f"   🌐 Сайты:")
            for site in contacts['websites'][:2]:
                print(f"      {site}")
        
        if contacts['address']:
            print(f"   📍 Адрес: {contacts['address']}")
    
    # Статистика
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    
    found_count = len([r for r in results if r.get('found')])
    not_found_count = len(results) - found_count
    
    print(f"\nОбщее:")
    print(f"  Обработано компаний: {len(results)}")
    print(f"  Найдены контакты: {found_count} ({found_count/len(results)*100:.1f}%)")
    print(f"  Не найдено: {not_found_count}")
    print(f"  Время выполнения: {duration:.1f} секунд")
    print(f"  Среднее время на компанию: {duration/len(results):.1f} сек")
    
    # Статистика по типам контактов
    with_phones = len([r for r in results if r.get('found') and r['contacts']['phones']])
    with_emails = len([r for r in results if r.get('found') and r['contacts']['emails']])
    with_telegram = len([r for r in results if r.get('found') and r['contacts']['telegram']])
    with_whatsapp = len([r for r in results if r.get('found') and r['contacts']['whatsapp']])
    with_websites = len([r for r in results if r.get('found') and r['contacts']['websites']])
    
    print(f"\nНайденные контакты:")
    print(f"  📞 С телефонами: {with_phones}")
    print(f"  📧 С email: {with_emails}")
    print(f"  💬 С Telegram: {with_telegram}")
    print(f"  📱 С WhatsApp: {with_whatsapp}")
    print(f"  🌐 С сайтами: {with_websites}")
    
    # Статистика движка
    print(f"\nСтатистика движка:")
    stats = engine.get_stats()
    print(f"  Всего поисков: {stats['total_searches']}")
    print(f"  Попаданий в кеш: {stats['cache_hits']} ({stats['cache_hit_rate']}%)")
    print(f"  Промахов кеша: {stats['cache_misses']}")
    print(f"  Размер кеша: {stats['cache_size']} записей")
    
    print(f"\n  API вызовы:")
    print(f"    - 2GIS: {stats['api_calls']['2gis']}")
    print(f"    - HH.ru: {stats['api_calls']['hh_ru']}")
    print(f"    - Парсинг сайтов: {stats['api_calls']['website_parses']}")
    
    # Сохраняем результаты
    print("\n" + "=" * 70)
    print("💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 70)
    
    output_file = f"test_contacts_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Результаты сохранены в: {output_file}")
    except Exception as e:
        print(f"\n⚠️ Ошибка сохранения: {e}")
    
    # Итог
    print("\n" + "=" * 70)
    print("✅ ТЕСТ ЗАВЕРШЕН!")
    print("=" * 70)
    
    success_rate = found_count / len(results) * 100
    
    if success_rate >= 70:
        print("\n🎉 ОТЛИЧНО! Успешность выше 70%")
    elif success_rate >= 50:
        print("\n👍 ХОРОШО! Успешность выше 50%")
    else:
        print("\n⚠️ Успешность ниже 50% - возможно нужен API ключ 2GIS")
    
    print(f"\nУспешность поиска: {success_rate:.1f}%")
    print(f"Время выполнения: {duration:.1f} секунд")
    print(f"Результаты сохранены в: {output_file}")
    
    print("\n💡 Совет: Повторный запуск будет быстрее благодаря кешу!")
    print()


if __name__ == "__main__":
    main()

