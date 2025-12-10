"""
УМНЫЙ ДВИЖОК ПОИСКА КОНТАКТОВ КОМПАНИЙ
Объединяет все методы: 2GIS, HH.ru, парсинг сайтов
Каскадный поиск с кешированием
"""

import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from website_parser import WebsiteParser


class ContactsSearchEngine:
    """
    Главный класс для поиска контактов компаний
    Использует каскадную стратегию: Кеш → 2GIS → HH.ru → Парсинг сайтов
    """
    
    def __init__(
        self,
        api_key_2gis: Optional[str] = None,
        cache_file: str = "contacts_search_cache.json",
        enable_2gis: bool = True,
        enable_hh: bool = True,
        enable_website_parsing: bool = True
    ):
        """
        Инициализация движка поиска
        
        Args:
            api_key_2gis: API ключ 2GIS (опционально)
            cache_file: Файл для кеширования
            enable_2gis: Использовать 2GIS API
            enable_hh: Использовать HH.ru API
            enable_website_parsing: Парсить сайты компаний
        """
        self.api_key_2gis = api_key_2gis
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
        # Включение/выключение источников
        self.enable_2gis = enable_2gis and api_key_2gis
        self.enable_hh = enable_hh
        self.enable_website_parsing = enable_website_parsing
        
        # Парсер сайтов
        self.website_parser = WebsiteParser() if enable_website_parsing else None
        
        # Статистика
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            '2gis_calls': 0,
            'hh_calls': 0,
            'website_parses': 0
        }
        
        # Настройки
        self.request_delay = 0.5
        self.base_url_2gis = "https://catalog.api.2gis.com/3.0/items"
    
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
    
    def search_company(
        self,
        company_name: str,
        city: str = "Москва",
        vacancy_link: Optional[str] = None
    ) -> Dict:
        """
        ГЛАВНЫЙ МЕТОД: Поиск контактов компании
        
        Args:
            company_name: Название компании
            city: Город поиска
            vacancy_link: Ссылка на вакансию HH.ru (опционально)
            
        Returns:
            Словарь с контактами компании
        """
        # Шаг 1: Проверяем кеш
        cache_key = f"{company_name.lower().strip()}_{city.lower()}"
        
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            cached_result = self.cache[cache_key]
            cached_result['from_cache'] = True
            return cached_result
        
        self.stats['cache_misses'] += 1
        
        # Инициализируем результат
        result = {
            'company_name': company_name,
            'city': city,
            'found': False,
            'sources': [],
            'contacts': {
                'phones': [],
                'emails': [],
                'telegram': [],
                'whatsapp': [],
                'websites': [],
                'address': ''
            },
            'additional_info': {
                'full_name': '',
                'hh_company_url': '',
                'vacancies_count': 0
            },
            'search_date': datetime.now().isoformat(),
            'from_cache': False,
            'api_calls_used': 0
        }
        
        # Шаг 2: Ищем в 2GIS
        if self.enable_2gis:
            gis_result = self._search_2gis(company_name, city)
            if gis_result:
                result = self._merge_results(result, gis_result, '2gis')
        
        # Шаг 3: Ищем на HH.ru
        if self.enable_hh:
            hh_result = self._search_hh(company_name, vacancy_link)
            if hh_result:
                result = self._merge_results(result, hh_result, 'hh.ru')
        
        # Шаг 4: Парсим сайты компании
        if self.enable_website_parsing and result['contacts']['websites']:
            for website in result['contacts']['websites'][:2]:  # Максимум 2 сайта
                web_result = self._parse_website(website)
                if web_result:
                    result = self._merge_results(result, web_result, 'website')
        
        # Удаляем дубликаты
        result = self._deduplicate_contacts(result)
        
        # Определяем успешность
        result['found'] = any([
            result['contacts']['phones'],
            result['contacts']['emails'],
            result['contacts']['websites']
        ])
        
        # Сохраняем в кеш
        self.cache[cache_key] = result
        self._save_cache()
        
        return result
    
    def _search_2gis(self, company_name: str, city: str) -> Optional[Dict]:
        """Поиск в 2GIS"""
        try:
            params = {
                'q': company_name,
                'key': self.api_key_2gis,
                'locale': 'ru_RU',
                'fields': 'items.contact_groups,items.address,items.org',
                'region_id': self._get_region_id(city)
            }
            
            response = requests.get(
                self.base_url_2gis,
                params=params,
                timeout=10
            )
            
            self.stats['2gis_calls'] += 1
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') and data['result'].get('items'):
                    item = data['result']['items'][0]
                    return self._extract_2gis_contacts(item, company_name)
            
            time.sleep(self.request_delay)
            
        except Exception as e:
            print(f"⚠️ Ошибка 2GIS для {company_name}: {e}")
        
        return None
    
    def _search_hh(
        self,
        company_name: str,
        vacancy_link: Optional[str] = None
    ) -> Optional[Dict]:
        """Поиск на HH.ru"""
        try:
            # Если есть ссылка на вакансию, используем её
            if vacancy_link:
                vacancy_id = vacancy_link.split('/')[-1].split('?')[0]
                
                url = f"https://api.hh.ru/vacancies/{vacancy_id}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                self.stats['hh_calls'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    return self._extract_hh_contacts(data, company_name)
                
                time.sleep(self.request_delay)
            
        except Exception as e:
            print(f"⚠️ Ошибка HH.ru для {company_name}: {e}")
        
        return None
    
    def _parse_website(self, url: str) -> Optional[Dict]:
        """Парсинг сайта компании"""
        try:
            if not self.website_parser:
                return None
            
            result = self.website_parser.parse_website(url)
            self.stats['website_parses'] += 1
            
            if result['success']:
                return {
                    'contacts': {
                        'phones': result.get('phones', []),
                        'emails': result.get('emails', []),
                        'telegram': result.get('telegram', []),
                        'whatsapp': result.get('whatsapp', []),
                        'websites': []
                    }
                }
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга {url}: {e}")
        
        return None
    
    def _extract_2gis_contacts(self, item: Dict, company_name: str) -> Dict:
        """Извлечь контакты из 2GIS"""
        result = {
            'contacts': {
                'phones': [],
                'emails': [],
                'telegram': [],
                'whatsapp': [],
                'websites': [],
                'address': ''
            },
            'additional_info': {
                'full_name': item.get('name', company_name)
            }
        }
        
        # Контакты
        contact_groups = item.get('contact_groups', [])
        for group in contact_groups:
            for contact in group.get('contacts', []):
                contact_type = contact.get('type')
                
                if contact_type == 'phone':
                    phone = contact.get('text', '')
                    if phone:
                        result['contacts']['phones'].append(phone)
                
                elif contact_type == 'email':
                    email = contact.get('text', '')
                    if email:
                        result['contacts']['emails'].append(email)
                
                elif contact_type == 'website':
                    website = contact.get('url', '')
                    if website:
                        result['contacts']['websites'].append(website)
        
        # Адрес
        address_name = item.get('address_name', '')
        if address_name:
            result['contacts']['address'] = address_name
        
        return result
    
    def _extract_hh_contacts(self, data: Dict, company_name: str) -> Dict:
        """Извлечь контакты из HH.ru"""
        import re
        
        result = {
            'contacts': {
                'phones': [],
                'emails': [],
                'telegram': [],
                'whatsapp': [],
                'websites': [],
                'address': ''
            },
            'additional_info': {
                'hh_company_url': ''
            }
        }
        
        employer = data.get('employer', {})
        
        # URL компании на HH.ru
        if employer.get('alternate_url'):
            result['additional_info']['hh_company_url'] = employer['alternate_url']
        
        # Сайт компании
        if employer.get('site_url'):
            result['contacts']['websites'].append(employer['site_url'])
        
        # Описание вакансии
        description = data.get('description', '')
        
        # Ищем email
        emails = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            description
        )
        result['contacts']['emails'].extend(emails)
        
        # Ищем телефоны
        phones = re.findall(
            r'(?:\+7|8)[\s-]?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}',
            description
        )
        result['contacts']['phones'].extend(phones)
        
        # Адрес
        address_data = data.get('address')
        if address_data:
            city = address_data.get('city', '')
            street = address_data.get('street', '')
            building = address_data.get('building', '')
            
            address_parts = [p for p in [city, street, building] if p]
            if address_parts:
                result['contacts']['address'] = ', '.join(address_parts)
        
        return result
    
    def _merge_results(
        self,
        main_result: Dict,
        new_data: Dict,
        source: str
    ) -> Dict:
        """Объединить результаты из разных источников"""
        # Добавляем источник
        if source not in main_result['sources']:
            main_result['sources'].append(source)
        
        # Объединяем контакты
        if 'contacts' in new_data:
            for key in ['phones', 'emails', 'telegram', 'whatsapp', 'websites']:
                if key in new_data['contacts']:
                    main_result['contacts'][key].extend(new_data['contacts'][key])
            
            # Адрес (берем первый непустой)
            if new_data['contacts'].get('address') and not main_result['contacts']['address']:
                main_result['contacts']['address'] = new_data['contacts']['address']
        
        # Дополнительная информация
        if 'additional_info' in new_data:
            for key, value in new_data['additional_info'].items():
                if value and not main_result['additional_info'].get(key):
                    main_result['additional_info'][key] = value
        
        return main_result
    
    def _deduplicate_contacts(self, result: Dict) -> Dict:
        """Удалить дубликаты контактов"""
        for key in ['phones', 'emails', 'telegram', 'whatsapp', 'websites']:
            if key in result['contacts']:
                # Удаляем дубликаты, сохраняя порядок
                seen = set()
                unique = []
                for item in result['contacts'][key]:
                    item_lower = item.lower().strip()
                    if item_lower not in seen:
                        seen.add(item_lower)
                        unique.append(item.strip())
                
                result['contacts'][key] = unique
        
        return result
    
    def _get_region_id(self, city: str) -> int:
        """Получить ID региона для 2GIS"""
        regions = {
            'москва': 1,
            'санкт-петербург': 2,
            'новосибирск': 32,
            'екатеринбург': 48,
            'нижний новгород': 43,
            'казань': 88,
        }
        return regions.get(city.lower(), 1)
    
    def get_stats(self) -> Dict:
        """Получить статистику работы"""
        total_searches = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (
            (self.stats['cache_hits'] / total_searches * 100)
            if total_searches > 0 else 0
        )
        
        return {
            'total_searches': total_searches,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'cache_hit_rate': round(cache_hit_rate, 1),
            'api_calls': {
                '2gis': self.stats['2gis_calls'],
                'hh_ru': self.stats['hh_calls'],
                'website_parses': self.stats['website_parses']
            },
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """Очистить кеш"""
        self.cache = {}
        self._save_cache()
        print("✅ Кеш очищен")


def main():
    """Тестовый запуск"""
    print("=" * 70)
    print("🔍 ТЕСТ ДВИЖКА ПОИСКА КОНТАКТОВ")
    print("=" * 70)
    print()
    
    # Инициализация (с API ключом 2GIS или без)
    API_KEY_2GIS = "75730e35-2767-46d6-b42b-548b4acae13e"
    
    engine = ContactsSearchEngine(
        api_key_2gis=API_KEY_2GIS,
        enable_2gis=True,
        enable_hh=True,
        enable_website_parsing=True
    )
    
    # Тестовые компании
    test_companies = [
        {"name": "Яндекс", "city": "Москва"},
        {"name": "Сбер", "city": "Москва"},
        {"name": "МТС", "city": "Москва"},
    ]
    
    for company in test_companies:
        print(f"🔍 Ищем: {company['name']}")
        
        result = engine.search_company(
            company_name=company['name'],
            city=company['city']
        )
        
        if result['found']:
            print(f"  ✓ Найдено! Источники: {', '.join(result['sources'])}")
            
            contacts = result['contacts']
            if contacts['phones']:
                print(f"  📞 Телефоны: {', '.join(contacts['phones'][:2])}")
            if contacts['emails']:
                print(f"  📧 Email: {', '.join(contacts['emails'][:2])}")
            if contacts['telegram']:
                print(f"  💬 Telegram: {', '.join(contacts['telegram'])}")
            if contacts['whatsapp']:
                print(f"  📱 WhatsApp: {', '.join(contacts['whatsapp'])}")
            if contacts['websites']:
                print(f"  🌐 Сайты: {contacts['websites'][0]}")
        else:
            print("  ✗ Не найдено")
        
        print()
    
    # Статистика
    print("=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    stats = engine.get_stats()
    print(f"Всего поисков: {stats['total_searches']}")
    print(f"Попаданий в кеш: {stats['cache_hits']} ({stats['cache_hit_rate']}%)")
    print(f"API вызовы:")
    print(f"  - 2GIS: {stats['api_calls']['2gis']}")
    print(f"  - HH.ru: {stats['api_calls']['hh_ru']}")
    print(f"  - Парсинг сайтов: {stats['api_calls']['website_parses']}")
    print(f"Размер кеша: {stats['cache_size']} записей")


if __name__ == "__main__":
    main()

