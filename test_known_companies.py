"""
ТЕСТ С ИЗВЕСТНЫМИ КОМПАНИЯМИ
Проверяем работу с крупными брендами
"""

from contacts_search_engine import ContactsSearchEngine
from datetime import datetime
import json


def main():
    print("=" * 70)
    print("🧪 ТЕСТ С ИЗВЕСТНЫМИ КОМПАНИЯМИ")
    print("=" * 70)
    print()
    
    # Известные компании для теста
    test_companies = [
        "Яндекс",
        "Сбер",
        "МТС",
        "ВКонтакте",
        "Тинькофф",
        "Ozon",
        "Wildberries",
        "X5 Group",
        "Магнит",
        "Авито"
    ]
    
    print(f"📋 Тестовые компании ({len(test_companies)} шт):")
    for i, company in enumerate(test_companies, 1):
        print(f"  {i}. {company}")
    
    # Инициализация
    print("\n🔧 Инициализация движка...")
    
    API_KEY_2GIS = "75730e35-2767-46d6-b42b-548b4acae13e"
    
    engine = ContactsSearchEngine(
        api_key_2gis=API_KEY_2GIS,
        enable_2gis=True,
        enable_hh=True,
        enable_website_parsing=True
    )
    
    print("✓ Готово!")
    
    # Поиск
    print("\n" + "=" * 70)
    print("🔍 ПОИСК КОНТАКТОВ")
    print("=" * 70)
    print()
    
    results = []
    start_time = datetime.now()
    
    for i, company in enumerate(test_companies, 1):
        print(f"[{i}/10] {company}...", end=" ", flush=True)
        
        try:
            result = engine.search_company(
                company_name=company,
                city="Москва"
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
                if result['from_cache']:
                    info += " [cache]"
                
                print(info)
            else:
                print("✗")
        
        except Exception as e:
            print(f"⚠️ {e}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Показываем первые 3 найденных
    print("\n" + "=" * 70)
    print("📋 ПРИМЕРЫ НАЙДЕННЫХ КОНТАКТОВ")
    print("=" * 70)
    
    shown = 0
    for result in results:
        if not result.get('found') or shown >= 3:
            continue
        
        shown += 1
        print(f"\n{shown}. {result['company_name']}")
        print(f"   Источники: {', '.join(result['sources'])}")
        
        contacts = result['contacts']
        
        if contacts['phones']:
            print(f"   📞 {', '.join(contacts['phones'][:2])}")
        if contacts['emails']:
            print(f"   📧 {', '.join(contacts['emails'][:2])}")
        if contacts['telegram']:
            print(f"   💬 {', '.join(contacts['telegram'][:2])}")
        if contacts['websites']:
            print(f"   🌐 {contacts['websites'][0]}")
        if contacts['address']:
            print(f"   📍 {contacts['address'][:50]}...")
    
    # Итоговая статистика
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    
    found = len([r for r in results if r.get('found')])
    success_rate = found / len(results) * 100
    
    print(f"\n✅ Найдено контактов: {found}/{len(results)} ({success_rate:.1f}%)")
    print(f"⏱️ Время выполнения: {duration:.1f} сек")
    print(f"⚡ Среднее время: {duration/len(results):.1f} сек/компания")
    
    # Статистика по типам
    with_phones = len([r for r in results if r.get('found') and r['contacts']['phones']])
    with_emails = len([r for r in results if r.get('found') and r['contacts']['emails']])
    with_telegram = len([r for r in results if r.get('found') and r['contacts']['telegram']])
    with_websites = len([r for r in results if r.get('found') and r['contacts']['websites']])
    
    print(f"\n📊 По типам контактов:")
    print(f"   📞 Телефоны: {with_phones}")
    print(f"   📧 Email: {with_emails}")
    print(f"   💬 Telegram: {with_telegram}")
    print(f"   🌐 Сайты: {with_websites}")
    
    # Статистика API
    stats = engine.get_stats()
    print(f"\n📡 API вызовы:")
    print(f"   2GIS: {stats['api_calls']['2gis']}")
    print(f"   HH.ru: {stats['api_calls']['hh_ru']}")
    print(f"   Парсинг: {stats['api_calls']['website_parses']}")
    
    # Оценка
    print("\n" + "=" * 70)
    if success_rate >= 70:
        print("🎉 ОТЛИЧНО! Система работает на 70%+")
    elif success_rate >= 50:
        print("👍 ХОРОШО! Система работает на 50%+")
    elif success_rate >= 30:
        print("⚠️ СРЕДНЕ. Возможно проблемы с API ключом 2GIS")
    else:
        print("❌ ПЛОХО. API ключ 2GIS не работает или недействителен")
    print("=" * 70)
    
    # Сохранение
    output_file = "test_known_companies_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты: {output_file}")
    print()


if __name__ == "__main__":
    main()

