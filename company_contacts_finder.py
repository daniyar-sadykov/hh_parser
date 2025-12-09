"""
Автоматизированный поиск контактов компаний через 2GIS API
Простой и надежный вариант с кешированием и обработкой ошибок
"""

import json
import csv
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class CompanyContactsFinder:
    """Класс для поиска контактов компаний через 2GIS API"""
    
    def __init__(self, api_key: str, cache_file: str = "contacts_cache.json"):
        """
        Инициализация поисковика
        
        Args:
            api_key: API ключ 2GIS (получить на https://dev.2gis.com/)
            cache_file: Файл для кеширования результатов
        """
        self.api_key = api_key
        self.base_url = "https://catalog.api.2gis.com/3.0/items"
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.request_delay = 0.5  # Задержка между запросами (секунды)
        
    def _load_cache(self) -> Dict:
        """Загрузить кеш из файла"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки кеша: {e}")
        return {}
    
    def _save_cache(self):
        """Сохранить кеш в файл"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения кеша: {e}")
    
    def search_company(self, company_name: str, city: str = "Москва") -> Optional[Dict]:
        """
        Поиск компании в 2GIS
        
        Args:
            company_name: Название компании
            city: Город поиска (по умолчанию Москва)
            
        Returns:
            Словарь с контактами компании или None
        """
        # Проверяем кеш
        cache_key = f"{company_name}_{city}"
        if cache_key in self.cache:
            print(f"✓ {company_name} - из кеша")
            return self.cache[cache_key]
        
        # Делаем запрос к API
        try:
            params = {
                'q': company_name,
                'key': self.api_key,
                'locale': 'ru_RU',
                'fields': 'items.contact_groups,items.address,items.org',
                'region_id': self._get_region_id(city)
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') and data['result'].get('items'):
                    item = data['result']['items'][0]  # Берем первый результат
                    
                    contacts = self._extract_contacts(item, company_name)
                    
                    # Сохраняем в кеш
                    self.cache[cache_key] = contacts
                    self._save_cache()
                    
                    print(f"✓ {company_name} - найдено")
                    time.sleep(self.request_delay)
                    return contacts
                else:
                    print(f"✗ {company_name} - не найдено")
                    result = {
                        'company_name': company_name,
                        'found': False,
                        'search_date': datetime.now().isoformat()
                    }
                    self.cache[cache_key] = result
                    self._save_cache()
                    return result
            else:
                print(f"⚠️ {company_name} - ошибка API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ {company_name} - ошибка: {e}")
            return None
        
        finally:
            time.sleep(self.request_delay)
    
    def _get_region_id(self, city: str) -> int:
        """Получить ID региона для города"""
        regions = {
            'москва': 1,
            'санкт-петербург': 2,
            'новосибирск': 32,
            'екатеринбург': 48,
            'нижний новгород': 43,
            'казань': 88,
            'челябинск': 82,
            'омск': 20,
            'самара': 51,
            'ростов-на-дону': 38
        }
        return regions.get(city.lower(), 1)  # По умолчанию Москва
    
    def _extract_contacts(self, item: Dict, company_name: str) -> Dict:
        """Извлечь контактную информацию из результата 2GIS"""
        contacts = {
            'company_name': company_name,
            'found': True,
            'search_date': datetime.now().isoformat(),
            'phones': [],
            'emails': [],
            'websites': [],
            'address': '',
            'full_name': item.get('name', company_name)
        }
        
        # Телефоны
        contact_groups = item.get('contact_groups', [])
        for group in contact_groups:
            for contact in group.get('contacts', []):
                if contact.get('type') == 'phone':
                    phone = contact.get('text', '')
                    if phone and phone not in contacts['phones']:
                        contacts['phones'].append(phone)
                elif contact.get('type') == 'email':
                    email = contact.get('text', '')
                    if email and email not in contacts['emails']:
                        contacts['emails'].append(email)
                elif contact.get('type') == 'website':
                    website = contact.get('url', '')
                    if website and website not in contacts['websites']:
                        contacts['websites'].append(website)
        
        # Адрес
        address_comment = item.get('address_comment')
        address_name = item.get('address_name')
        if address_comment and address_name:
            contacts['address'] = f"{address_name}, {address_comment}"
        elif address_name:
            contacts['address'] = address_name
        elif address_comment:
            contacts['address'] = address_comment
        
        # Сайт из org
        if 'org' in item:
            org = item['org']
            if 'contact_groups' in org:
                for group in org['contact_groups']:
                    for contact in group.get('contacts', []):
                        if contact.get('type') == 'website':
                            website = contact.get('url', '')
                            if website and website not in contacts['websites']:
                                contacts['websites'].append(website)
        
        return contacts
    
    def process_vacancies_file(self, json_file: str, city: str = "Москва", 
                               limit: Optional[int] = None) -> List[Dict]:
        """
        Обработать файл с вакансиями
        
        Args:
            json_file: Путь к JSON файлу с вакансиями
            city: Город для поиска
            limit: Ограничение количества компаний (None = все)
            
        Returns:
            Список с контактами компаний
        """
        print(f"📖 Загрузка вакансий из {json_file}...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                vacancies = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return []
        
        # Извлекаем уникальные названия компаний
        companies = list(set([v.get('компания', '') for v in vacancies if v.get('компания')]))
        companies = [c for c in companies if c.strip()]  # Убираем пустые
        
        print(f"📊 Найдено уникальных компаний: {len(companies)}")
        
        if limit:
            companies = companies[:limit]
            print(f"🔍 Обрабатываем первые {limit} компаний")
        
        # Поиск контактов
        results = []
        total = len(companies)
        
        print(f"\n🔍 Начинаем поиск контактов...\n")
        
        for i, company in enumerate(companies, 1):
            print(f"[{i}/{total}] ", end='')
            contacts = self.search_company(company, city)
            if contacts:
                results.append(contacts)
        
        print(f"\n✅ Обработано компаний: {total}")
        print(f"✅ Найдено контактов: {len([r for r in results if r.get('found')])} ")
        
        return results
    
    def export_to_csv(self, results: List[Dict], output_file: str):
        """Экспорт результатов в CSV"""
        try:
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = [
                    'company_name', 'full_name', 'found', 'phones', 
                    'emails', 'websites', 'address', 'search_date'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = result.copy()
                    # Преобразуем списки в строки
                    row['phones'] = '; '.join(row.get('phones', []))
                    row['emails'] = '; '.join(row.get('emails', []))
                    row['websites'] = '; '.join(row.get('websites', []))
                    writer.writerow(row)
            
            print(f"💾 Результаты сохранены в {output_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения CSV: {e}")
    
    def export_to_json(self, results: List[Dict], output_file: str):
        """Экспорт результатов в JSON"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 Результаты сохранены в {output_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")


def main():
    """Основная функция"""
    
    # ============= НАСТРОЙКИ =============
    
    # API ключ 2GIS (получить на https://dev.2gis.com/)
    API_KEY = "ВАШ_API_КЛЮЧ_ЗДЕСЬ"  # 🔑 ЗАМЕНИТЕ НА СВОЙ КЛЮЧ!
    
    # Файл с вакансиями
    INPUT_FILE = "vacancies_all.json"
    
    # Город для поиска
    CITY = "Москва"
    
    # Ограничение количества компаний (None = все)
    # Для теста можно поставить 10-20
    LIMIT = None
    
    # Выходные файлы
    OUTPUT_CSV = f"company_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    OUTPUT_JSON = f"company_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # =====================================
    
    print("=" * 60)
    print("🔍 АВТОМАТИЗИРОВАННЫЙ ПОИСК КОНТАКТОВ КОМПАНИЙ")
    print("=" * 60)
    print()
    
    # Проверка API ключа
    if API_KEY == "ВАШ_API_КЛЮЧ_ЗДЕСЬ":
        print("❌ ОШИБКА: Укажите API ключ 2GIS!")
        print("📖 Получить ключ: https://dev.2gis.com/")
        print("🔧 Измените значение API_KEY в коде")
        return
    
    # Создаем поисковик
    finder = CompanyContactsFinder(API_KEY)
    
    # Обрабатываем файл
    results = finder.process_vacancies_file(INPUT_FILE, CITY, LIMIT)
    
    if results:
        # Экспортируем результаты
        print()
        finder.export_to_csv(results, OUTPUT_CSV)
        finder.export_to_json(results, OUTPUT_JSON)
        
        # Статистика
        print()
        print("=" * 60)
        print("📊 СТАТИСТИКА")
        print("=" * 60)
        found = [r for r in results if r.get('found')]
        print(f"Всего компаний обработано: {len(results)}")
        print(f"Найдено в 2GIS: {len(found)}")
        print(f"Не найдено: {len(results) - len(found)}")
        
        if found:
            with_phones = len([r for r in found if r.get('phones')])
            with_emails = len([r for r in found if r.get('emails')])
            with_websites = len([r for r in found if r.get('websites')])
            
            print(f"\nКонтакты:")
            print(f"  - С телефонами: {with_phones}")
            print(f"  - С email: {with_emails}")
            print(f"  - С сайтами: {with_websites}")
        
        print("=" * 60)
        print("✅ ГОТОВО!")
    else:
        print("❌ Нет результатов для сохранения")


if __name__ == "__main__":
    main()
