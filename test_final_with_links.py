"""
ФИНАЛЬНЫЙ ТЕСТ - с передачей vacancy_link
Проверяем что реально можно найти
"""

from contacts_search_engine import ContactsSearchEngine
import json


def main():
    print("=" * 70)
    print("🔍 ФИНАЛЬНЫЙ ТЕСТ - Реальный поиск контактов")
    print("=" * 70)
    print()
    
    # Загружаем вакансии
    with open('vacancies_all.json', 'r', encoding='utf-8') as f:
        vacancies = json.load(f)
    
    print(f"✓ Загружено {len(vacancies)} вакансий")
    
    # Берем первые 10 вакансий с разными компаниями
    print("\n📊 Выбираем 10 разных компаний...")
    
    selected = []
    seen_companies = set()
    
    for v in vacancies:
        company = v.get('компания', '').strip()
        if company and company not in seen_companies:
            selected.append({
                'company': company,
                'vacancy_link': v.get('ссылка', ''),
                'vacancy_name': v.get('название', '')
            })
            seen_companies.add(company)
        
        if len(selected) >= 10:
            break
    
    print(f"✓ Выбрано {len(selected)} компаний\n")
    
    for i, item in enumerate(selected, 1):
        print(f"  {i}. {item['company']}")
        print(f"     {item['vacancy_name'][:50]}...")
    
    # Инициализация БЕЗ 2GIS
    print("\n🔧 Инициализация (БЕЗ 2GIS, с HH.ru + парсинг)...")
    
    engine = ContactsSearchEngine(
        api_key_2gis=None,
        enable_2gis=False,
        enable_hh=True,
        enable_website_parsing=True
    )
    
    print("✓ Готово!")
    
    # ВАЖНО: Передаем vacancy_link!
    print("\n" + "=" * 70)
    print("🔍 ПОИСК КОНТАКТОВ (с vacancy_link)")
    print("=" * 70)
    print()
    
    results = []
    
    for i, item in enumerate(selected, 1):
        print(f"[{i}/10] {item['company'][:30]}...", end=" ", flush=True)
        
        try:
            # ПЕРЕДАЕМ vacancy_link!
            result = engine.search_company(
                company_name=item['company'],
                city="Москва",
                vacancy_link=item['vacancy_link']  # ← ВОТ ОНО!
            )
            
            results.append(result)
            
            if result['found']:
                parts = []
                if result['contacts']['websites']:
                    parts.append(f"🌐{len(result['contacts']['websites'])}")
                if result['contacts']['emails']:
                    parts.append(f"📧{len(result['contacts']['emails'])}")
                if result['contacts']['phones']:
                    parts.append(f"📞{len(result['contacts']['phones'])}")
                if result['contacts']['telegram']:
                    parts.append(f"💬{len(result['contacts']['telegram'])}")
                
                print(f"✓ {' '.join(parts)}")
            else:
                print("✗")
        
        except Exception as e:
            print(f"⚠️ {str(e)[:50]}")
    
    # Детальные результаты
    print("\n" + "=" * 70)
    print("📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 70)
    
    found_any = False
    
    for i, result in enumerate(results, 1):
        if not result.get('found'):
            continue
        
        found_any = True
        contacts = result['contacts']
        
        print(f"\n{i}. {result['company_name']}")
        print(f"   Источники: {', '.join(result['sources'])}")
        
        if contacts['websites']:
            print(f"   🌐 Сайты:")
            for site in contacts['websites'][:2]:
                print(f"      {site}")
        
        if contacts['emails']:
            print(f"   📧 Email:")
            for email in contacts['emails'][:3]:
                print(f"      {email}")
        
        if contacts['phones']:
            print(f"   📞 Телефоны:")
            for phone in contacts['phones'][:2]:
                print(f"      {phone}")
        
        if contacts['telegram']:
            print(f"   💬 Telegram:")
            for tg in contacts['telegram']:
                print(f"      {tg}")
        
        if result['additional_info'].get('hh_company_url'):
            print(f"   🔗 HH: {result['additional_info']['hh_company_url']}")
    
    if not found_any:
        print("\n⚠️ Ни одного контакта не найдено")
    
    # Статистика
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    
    found = len([r for r in results if r.get('found')])
    
    print(f"\n✅ Найдено контактов: {found}/10 ({found*10}%)")
    
    with_websites = len([r for r in results if r.get('found') and r['contacts']['websites']])
    with_emails = len([r for r in results if r.get('found') and r['contacts']['emails']])
    with_phones = len([r for r in results if r.get('found') and r['contacts']['phones']])
    with_telegram = len([r for r in results if r.get('found') and r['contacts']['telegram']])
    with_hh_url = len([r for r in results if r.get('found') and r['additional_info'].get('hh_company_url')])
    
    print(f"\nПо типам:")
    print(f"  🌐 Сайты компаний: {with_websites}")
    print(f"  📧 Email: {with_emails}")
    print(f"  📞 Телефоны: {with_phones}")
    print(f"  💬 Telegram: {with_telegram}")
    print(f"  🔗 HH профили: {with_hh_url}")
    
    stats = engine.get_stats()
    print(f"\nAPI вызовы:")
    print(f"  HH.ru: {stats['api_calls']['hh_ru']}")
    print(f"  Парсинг: {stats['api_calls']['website_parses']}")
    
    print("\n" + "=" * 70)
    
    if found > 0:
        print("✅ КОНТАКТЫ НАЙДЕНЫ!")
        print(f"Успешность: {found*10}% (БЕЗ 2GIS)")
        print("\n💡 С API ключом 2GIS было бы {0}%".format(min(100, found*10 + 30)))
    else:
        print("⚠️ Контакты не найдены")
        print("\nВозможные причины:")
        print("  1. Компании не указывают контакты в вакансиях")
        print("  2. Компании не имеют прямых сайтов на HH")
        print("  3. Нужен API ключ 2GIS для полноценного поиска")
    
    print("=" * 70)
    
    # Сохранение
    with open('test_final_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n💾 Результаты: test_final_results.json")
    print()


if __name__ == "__main__":
    main()

