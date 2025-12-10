"""
ТЕСТ БЕЗ 2GIS - только HH.ru и парсинг
Проверяем работу бесплатных источников
"""

from contacts_search_engine import ContactsSearchEngine
from datetime import datetime
import json


def main():
    print("=" * 70)
    print("🆓 ТЕСТ БЕЗ 2GIS (только HH.ru + парсинг)")
    print("=" * 70)
    print()
    
    # Загружаем вакансии из проекта
    print("📖 Загрузка вакансий...")
    
    try:
        with open('vacancies_all.json', 'r', encoding='utf-8') as f:
            vacancies = json.load(f)
        print(f"✓ Загружено {len(vacancies)} вакансий")
    except:
        print("❌ Не удалось загрузить vacancies_all.json")
        return
    
    # Извлекаем компании с их вакансиями
    print("\n📊 Извлечение компаний с вакансиями...")
    
    companies_with_links = {}
    
    for vacancy in vacancies[:100]:  # Берем первые 100
        company = vacancy.get('компания', '').strip()
        link = vacancy.get('ссылка', '')
        
        if company and link and company not in companies_with_links:
            companies_with_links[company] = link
        
        if len(companies_with_links) >= 10:
            break
    
    print(f"✓ Найдено {len(companies_with_links)} компаний с вакансиями")
    
    for i, company in enumerate(list(companies_with_links.keys()), 1):
        print(f"  {i}. {company}")
    
    # Инициализация БЕЗ 2GIS
    print("\n🔧 Инициализация (БЕЗ 2GIS)...")
    
    engine = ContactsSearchEngine(
        api_key_2gis=None,  # Отключаем 2GIS
        enable_2gis=False,  # Отключаем 2GIS
        enable_hh=True,     # Включаем HH.ru
        enable_website_parsing=True  # Включаем парсинг
    )
    
    print("✓ Готово!")
    print("  - 2GIS: ✗ ОТКЛЮЧЕН")
    print("  - HH.ru: ✓")
    print("  - Парсинг сайтов: ✓")
    
    # Поиск
    print("\n" + "=" * 70)
    print("🔍 ПОИСК КОНТАКТОВ (HH.ru + парсинг сайтов)")
    print("=" * 70)
    print()
    
    results = []
    start_time = datetime.now()
    
    for i, (company, vacancy_link) in enumerate(companies_with_links.items(), 1):
        print(f"[{i}/10] {company}...", end=" ", flush=True)
        
        try:
            result = engine.search_company(
                company_name=company,
                city="Москва",
                vacancy_link=vacancy_link  # Передаем ссылку на вакансию!
            )
            
            results.append(result)
            
            if result['found']:
                sources = ', '.join(result['sources'])
                
                info_parts = []
                if result['contacts']['phones']:
                    info_parts.append(f"📞{len(result['contacts']['phones'])}")
                if result['contacts']['emails']:
                    info_parts.append(f"📧{len(result['contacts']['emails'])}")
                if result['contacts']['telegram']:
                    info_parts.append(f"💬{len(result['contacts']['telegram'])}")
                if result['contacts']['websites']:
                    info_parts.append(f"🌐{len(result['contacts']['websites'])}")
                
                info = f"✓ [{sources}] {' '.join(info_parts)}"
                print(info)
            else:
                print("✗")
        
        except Exception as e:
            print(f"⚠️ {e}")
            results.append({
                'company_name': company,
                'found': False,
                'error': str(e)
            })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Детальные результаты
    print("\n" + "=" * 70)
    print("📋 НАЙДЕННЫЕ КОНТАКТЫ")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        if not result.get('found'):
            continue
        
        print(f"\n{i}. {result['company_name']}")
        print(f"   Источники: {', '.join(result['sources'])}")
        
        contacts = result['contacts']
        
        if contacts.get('websites'):
            print(f"   🌐 Сайты: {', '.join(contacts['websites'])}")
        
        if contacts.get('emails'):
            print(f"   📧 Email: {', '.join(contacts['emails'][:3])}")
        
        if contacts.get('phones'):
            print(f"   📞 Телефоны: {', '.join(contacts['phones'][:2])}")
        
        if contacts.get('telegram'):
            print(f"   💬 Telegram: {', '.join(contacts['telegram'])}")
        
        if contacts.get('whatsapp'):
            print(f"   📱 WhatsApp: {', '.join(contacts['whatsapp'])}")
        
        if result['additional_info'].get('hh_company_url'):
            print(f"   🔗 HH.ru: {result['additional_info']['hh_company_url']}")
    
    # Статистика
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    
    found = len([r for r in results if r.get('found')])
    success_rate = found / len(results) * 100 if results else 0
    
    print(f"\n✅ Найдено контактов: {found}/{len(results)} ({success_rate:.1f}%)")
    print(f"⏱️ Время выполнения: {duration:.1f} сек")
    
    # По типам
    with_websites = len([r for r in results if r.get('found') and r['contacts']['websites']])
    with_emails = len([r for r in results if r.get('found') and r['contacts']['emails']])
    with_phones = len([r for r in results if r.get('found') and r['contacts']['phones']])
    with_telegram = len([r for r in results if r.get('found') and r['contacts']['telegram']])
    
    print(f"\nНайденные контакты:")
    print(f"  🌐 Сайты: {with_websites}")
    print(f"  📧 Email: {with_emails}")
    print(f"  📞 Телефоны: {with_phones}")
    print(f"  💬 Telegram: {with_telegram}")
    
    # API вызовы
    stats = engine.get_stats()
    print(f"\nAPI вызовы:")
    print(f"  HH.ru: {stats['api_calls']['hh_ru']}")
    print(f"  Парсинг сайтов: {stats['api_calls']['website_parses']}")
    
    # Итог
    print("\n" + "=" * 70)
    if success_rate >= 50:
        print("🎉 ОТЛИЧНО! Система работает БЕЗ 2GIS!")
        print("📊 Найдены сайты компаний через HH.ru")
    elif success_rate >= 30:
        print("👍 ХОРОШО! Частично работает")
    else:
        print("⚠️ Низкая успешность без 2GIS")
    print("=" * 70)
    
    print(f"\n💡 С API ключом 2GIS успешность была бы выше на 30-40%")
    print(f"💾 Результаты: test_free_results.json")
    
    # Сохранение
    with open("test_free_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()


if __name__ == "__main__":
    main()

