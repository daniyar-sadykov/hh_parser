"""
УМНЫЙ ПОИСК КОНТАКТОВ С ПРИОРИТИЗАЦИЕЙ
Оптимизирован для работы с ограничением API (1000 запросов 2GIS)
"""

import json
import csv
import time
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from collections import Counter


class SmartContactsFinder:
    """Умный поиск контактов с приоритизацией и альтернативными методами"""
    
    def __init__(self, api_key_2gis: str, cache_file: str = "contacts_cache.json"):
        """
        Инициализация умного поисковика
        
        Args:
            api_key_2gis: API ключ 2GIS
            cache_file: Файл для кеширования результатов
        """
        self.api_key_2gis = api_key_2gis
        self.base_url_2gis = "https://catalog.api.2gis.com/3.0/items"
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.request_delay = 0.5
        self.api_calls_count = 0
        self.api_limit = 1000  # Лимит бесплатных запросов
        
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
    
    def analyze_vacancies(self, json_file: str) -> Tuple[List[Dict], Dict]:
        """
        Анализ вакансий и создание приоритетного списка компаний
        
        Args:
            json_file: Путь к JSON файлу с вакансиями
            
        Returns:
            Tuple[List[Dict], Dict]: (приоритетный список компаний, статистика)
        """
        print("📊 Анализ вакансий для приоритизации...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                vacancies = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return [], {}
        
        # Подсчитываем количество вакансий по компаниям
        company_vacancies = {}
        company_details = {}
        
        for vacancy in vacancies:
            company = vacancy.get('компания', '').strip()
            if not company:
                continue
            
            if company not in company_vacancies:
                company_vacancies[company] = []
                company_details[company] = {
                    'vacancies_count': 0,
                    'has_salary': False,
                    'avg_salary': 0,
                    'sample_vacancy': vacancy.get('название', '')
                }
            
            company_vacancies[company].append(vacancy)
            company_details[company]['vacancies_count'] += 1
            
            # Проверяем наличие зарплаты
            salary = vacancy.get('оплата', 'Не указана')
            if salary != 'Не указана' and 'руб' in salary:
                company_details[company]['has_salary'] = True
        
        # Создаем приоритетный список
        prioritized = []
        for company, details in company_details.items():
            priority_score = details['vacancies_count']
            
            # Бонус за указанную зарплату (более серьезные компании)
            if details['has_salary']:
                priority_score *= 1.5
            
            prioritized.append({
                'company': company,
                'vacancies_count': details['vacancies_count'],
                'has_salary': details['has_salary'],
                'sample_vacancy': details['sample_vacancy'],
                'priority_score': priority_score
            })
        
        # Сортируем по приоритету
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        
        stats = {
            'total_vacancies': len(vacancies),
            'total_companies': len(prioritized),
            'companies_with_salary': len([c for c in prioritized if c['has_salary']]),
            'top_10_companies': prioritized[:10]
        }
        
        return prioritized, stats
    
    def search_company_2gis(self, company_name: str, city: str = "Москва") -> Optional[Dict]:
        """
        Поиск компании в 2GIS
        
        Args:
            company_name: Название компании
            city: Город поиска
            
        Returns:
            Словарь с контактами или None
        """
        # Проверяем кеш
        cache_key = f"2gis_{company_name}_{city}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Проверяем лимит
        if self.api_calls_count >= self.api_limit:
            print(f"⚠️ Достигнут лимит API 2GIS ({self.api_limit} запросов)")
            return None
        
        # Делаем запрос к API
        try:
            params = {
                'q': company_name,
                'key': self.api_key_2gis,
                'locale': 'ru_RU',
                'fields': 'items.contact_groups,items.address,items.org',
                'region_id': self._get_region_id(city)
            }
            
            response = requests.get(self.base_url_2gis, params=params, timeout=10)
            self.api_calls_count += 1
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') and data['result'].get('items'):
                    item = data['result']['items'][0]
                    contacts = self._extract_contacts_2gis(item, company_name)
                    
                    # Сохраняем в кеш
                    self.cache[cache_key] = contacts
                    self._save_cache()
                    
                    time.sleep(self.request_delay)
                    return contacts
                else:
                    result = {
                        'company_name': company_name,
                        'found': False,
                        'source': '2gis',
                        'search_date': datetime.now().isoformat()
                    }
                    self.cache[cache_key] = result
                    self._save_cache()
                    return result
            else:
                print(f"⚠️ Ошибка API 2GIS: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Ошибка при запросе к 2GIS: {e}")
            return None
        finally:
            time.sleep(self.request_delay)
    
    def search_company_alternative(self, company_name: str, vacancy_link: str = None) -> Optional[Dict]:
        """
        Альтернативный метод поиска контактов (парсинг HH.ru)
        
        Args:
            company_name: Название компании
            vacancy_link: Ссылка на вакансию (может содержать контакты)
            
        Returns:
            Словарь с найденными контактами или None
        """
        cache_key = f"alt_{company_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        contacts = {
            'company_name': company_name,
            'found': False,
            'source': 'alternative',
            'search_date': datetime.now().isoformat(),
            'phones': [],
            'emails': [],
            'websites': []
        }
        
        # Пытаемся извлечь контакты из HH.ru (из описания компании)
        if vacancy_link:
            try:
                # Получаем ID вакансии
                vacancy_id = vacancy_link.split('/')[-1]
                
                # Запрос к API HH.ru для получения информации о компании
                response = requests.get(
                    f"https://api.hh.ru/vacancies/{vacancy_id}",
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    employer = data.get('employer', {})
                    
                    # Сайт компании
                    if employer.get('alternate_url'):
                        contacts['websites'].append(employer['alternate_url'])
                        contacts['found'] = True
                    
                    # Если есть описание, ищем email
                    description = data.get('description', '')
                    import re
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', description)
                    if emails:
                        contacts['emails'].extend(emails)
                        contacts['found'] = True
                
                time.sleep(0.3)  # Задержка между запросами
                
            except Exception as e:
                pass  # Тихо игнорируем ошибки альтернативного метода
        
        # Сохраняем в кеш
        self.cache[cache_key] = contacts
        self._save_cache()
        
        return contacts if contacts['found'] else None
    
    def _get_region_id(self, city: str) -> int:
        """Получить ID региона для города"""
        regions = {
            'москва': 1,
            'санкт-петербург': 2,
            'новосибирск': 32,
            'екатеринбург': 48,
            'нижний новгород': 43,
        }
        return regions.get(city.lower(), 1)
    
    def _extract_contacts_2gis(self, item: Dict, company_name: str) -> Dict:
        """Извлечь контактную информацию из результата 2GIS"""
        contacts = {
            'company_name': company_name,
            'found': True,
            'source': '2gis',
            'search_date': datetime.now().isoformat(),
            'phones': [],
            'emails': [],
            'websites': [],
            'address': '',
            'full_name': item.get('name', company_name)
        }
        
        # Телефоны и контакты
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
        address_name = item.get('address_name')
        if address_name:
            contacts['address'] = address_name
        
        return contacts
    
    def process_with_limit(
        self, 
        json_file: str, 
        city: str = "Москва",
        api_limit: int = 900,  # Оставляем запас
        use_alternative: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Обработка файла с учетом лимита API
        
        Args:
            json_file: Путь к JSON файлу с вакансиями
            city: Город для поиска
            api_limit: Максимальное количество API запросов
            use_alternative: Использовать альтернативные методы
            
        Returns:
            Tuple[List[Dict], Dict]: (результаты, статистика)
        """
        print("=" * 70)
        print("🎯 УМНЫЙ ПОИСК КОНТАКТОВ С ПРИОРИТИЗАЦИЕЙ")
        print("=" * 70)
        print()
        
        # Анализируем и приоритизируем компании
        prioritized, stats = self.analyze_vacancies(json_file)
        
        print(f"📊 Статистика вакансий:")
        print(f"   Всего вакансий: {stats['total_vacancies']}")
        print(f"   Уникальных компаний: {stats['total_companies']}")
        print(f"   Компаний с указанной ЗП: {stats['companies_with_salary']}")
        print()
        
        print(f"🎯 ТОП-10 приоритетных компаний:")
        for i, comp in enumerate(stats['top_10_companies'][:10], 1):
            salary_mark = "💰" if comp['has_salary'] else "  "
            print(f"   {i}. {salary_mark} {comp['company']} ({comp['vacancies_count']} вакансий)")
        print()
        
        print(f"🔍 Лимит 2GIS API: {api_limit} запросов")
        print(f"📦 В кеше уже есть: {len([k for k in self.cache.keys() if k.startswith('2gis_')])} компаний")
        print()
        
        # Определяем сколько компаний будем обрабатывать
        companies_to_process = prioritized[:api_limit]
        
        response = input(f"Обработать {len(companies_to_process)} приоритетных компаний? (да/нет): ").strip().lower()
        if response not in ['да', 'yes', 'y', 'д']:
            print("Отменено.")
            return [], {}
        
        print()
        print("🚀 Начинаем поиск контактов...")
        print()
        
        results = []
        total = len(companies_to_process)
        
        # Загружаем вакансии для альтернативного поиска
        with open(json_file, 'r', encoding='utf-8') as f:
            vacancies = json.load(f)
        
        vacancy_links = {}
        for v in vacancies:
            company = v.get('компания', '')
            if company and company not in vacancy_links:
                vacancy_links[company] = v.get('ссылка', '')
        
        for i, company_data in enumerate(companies_to_process, 1):
            company = company_data['company']
            
            print(f"[{i}/{total}] {company}...", end=' ')
            
            # Сначала пробуем 2GIS
            contacts = self.search_company_2gis(company, city)
            
            if contacts and contacts.get('found'):
                print(f"✓ 2GIS (тел: {len(contacts.get('phones', []))}, email: {len(contacts.get('emails', []))})")
                results.append(contacts)
            elif use_alternative:
                # Пробуем альтернативный метод
                alt_contacts = self.search_company_alternative(company, vacancy_links.get(company))
                if alt_contacts and alt_contacts.get('found'):
                    print(f"✓ ALT (email: {len(alt_contacts.get('emails', []))}, web: {len(alt_contacts.get('websites', []))})")
                    results.append(alt_contacts)
                else:
                    print("✗ не найдено")
                    if contacts:
                        results.append(contacts)
            else:
                print("✗ не найдено")
                if contacts:
                    results.append(contacts)
            
            # Проверка лимита
            if self.api_calls_count >= api_limit:
                print()
                print(f"⚠️ Достигнут лимит API ({api_limit} запросов)")
                print(f"Обработано компаний: {i}/{total}")
                break
        
        print()
        print(f"✅ Использовано API запросов: {self.api_calls_count}/{api_limit}")
        
        # Финальная статистика
        final_stats = {
            'total_processed': len(results),
            'found_in_2gis': len([r for r in results if r.get('source') == '2gis' and r.get('found')]),
            'found_alternative': len([r for r in results if r.get('source') == 'alternative' and r.get('found')]),
            'not_found': len([r for r in results if not r.get('found')]),
            'api_calls_used': self.api_calls_count,
            'with_phones': len([r for r in results if r.get('phones')]),
            'with_emails': len([r for r in results if r.get('emails')]),
            'with_websites': len([r for r in results if r.get('websites')])
        }
        
        return results, final_stats
    
    def export_to_csv(self, results: List[Dict], output_file: str):
        """Экспорт результатов в CSV"""
        try:
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = [
                    'company_name', 'full_name', 'found', 'source',
                    'phones', 'emails', 'websites', 'address', 'search_date'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {
                        'company_name': result.get('company_name', ''),
                        'full_name': result.get('full_name', result.get('company_name', '')),
                        'found': result.get('found', False),
                        'source': result.get('source', ''),
                        'phones': '; '.join(result.get('phones', [])),
                        'emails': '; '.join(result.get('emails', [])),
                        'websites': '; '.join(result.get('websites', [])),
                        'address': result.get('address', ''),
                        'search_date': result.get('search_date', '')
                    }
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
    
    # API ключ 2GIS
    API_KEY_2GIS = "75730e35-2767-46d6-b42b-548b4acae13e"
    
    # Входной файл
    INPUT_FILE = "vacancies_all.json"
    
    # Город для поиска
    CITY = "Москва"
    
    # Лимит API запросов (оставляем запас)
    API_LIMIT = 900  # Из 1000 доступных
    
    # Использовать альтернативные методы
    USE_ALTERNATIVE = True
    
    # Выходные файлы
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT_CSV = f"smart_contacts_{timestamp}.csv"
    OUTPUT_JSON = f"smart_contacts_{timestamp}.json"
    
    # =====================================
    
    # Создаем умный поисковик
    finder = SmartContactsFinder(API_KEY_2GIS)
    
    # Обрабатываем с учетом лимита
    results, stats = finder.process_with_limit(
        INPUT_FILE, 
        CITY, 
        API_LIMIT,
        USE_ALTERNATIVE
    )
    
    if results:
        print()
        print("=" * 70)
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        print("=" * 70)
        print(f"Обработано компаний: {stats['total_processed']}")
        print(f"Найдено через 2GIS: {stats['found_in_2gis']}")
        print(f"Найдено альтернативно: {stats['found_alternative']}")
        print(f"Не найдено: {stats['not_found']}")
        print(f"Использовано API запросов: {stats['api_calls_used']}/{API_LIMIT}")
        print()
        print("Контакты:")
        print(f"  📞 С телефонами: {stats['with_phones']}")
        print(f"  📧 С email: {stats['with_emails']}")
        print(f"  🌐 С сайтами: {stats['with_websites']}")
        print("=" * 70)
        print()
        
        # Экспортируем
        finder.export_to_csv(results, OUTPUT_CSV)
        finder.export_to_json(results, OUTPUT_JSON)
        
        print()
        print("✅ ГОТОВО!")
        print()
        print("💡 Совет: Кеш сохранен. Повторные запуски не будут тратить API лимит!")
    else:
        print("❌ Нет результатов")


if __name__ == "__main__":
    main()

