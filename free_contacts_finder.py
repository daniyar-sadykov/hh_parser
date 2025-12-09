"""
БЕСПЛАТНЫЙ ПОИСК КОНТАКТОВ БЕЗ API
Использует только HH.ru и публичные данные
"""

import json
import csv
import time
import requests
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class FreeContactsFinder:
    """Поиск контактов без платных API - только бесплатные источники"""
    
    def __init__(self, hh_client_id: str = None, hh_client_secret: str = None):
        """
        Инициализация бесплатного поисковика
        
        Args:
            hh_client_id: Client ID для HH.ru API (опционально)
            hh_client_secret: Client Secret для HH.ru API (опционально)
        """
        self.hh_client_id = hh_client_id
        self.hh_client_secret = hh_client_secret
        self.cache_file = "free_contacts_cache.json"
        self.cache = self._load_cache()
        self.request_delay = 0.5
        
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
    
    def extract_contacts_from_hh(self, vacancy_id: str, company_name: str) -> Dict:
        """
        Извлечение контактов из вакансии HH.ru
        
        Args:
            vacancy_id: ID вакансии
            company_name: Название компании
            
        Returns:
            Словарь с контактами
        """
        contacts = {
            'company_name': company_name,
            'found': False,
            'source': 'hh.ru',
            'phones': [],
            'emails': [],
            'websites': [],
            'address': '',
            'hh_company_url': '',
            'search_date': datetime.now().isoformat()
        }
        
        try:
            # Запрос информации о вакансии
            url = f"https://api.hh.ru/vacancies/{vacancy_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                employer = data.get('employer', {})
                
                # URL компании на HH.ru
                if employer.get('alternate_url'):
                    contacts['hh_company_url'] = employer['alternate_url']
                    contacts['found'] = True
                
                # Официальный сайт компании
                if employer.get('site_url'):
                    contacts['websites'].append(employer['site_url'])
                    contacts['found'] = True
                
                # Описание вакансии (может содержать контакты)
                description = data.get('description', '')
                
                # Поиск email в описании
                emails = re.findall(
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    description
                )
                if emails:
                    contacts['emails'].extend(list(set(emails)))
                    contacts['found'] = True
                
                # Поиск телефонов в описании (российские форматы)
                phones = re.findall(
                    r'(?:\+7|8)[\s-]?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}',
                    description
                )
                if phones:
                    contacts['phones'].extend(list(set(phones)))
                    contacts['found'] = True
                
                # Адрес
                address_data = data.get('address')
                if address_data:
                    city = address_data.get('city', '')
                    street = address_data.get('street', '')
                    building = address_data.get('building', '')
                    
                    address_parts = [p for p in [city, street, building] if p]
                    if address_parts:
                        contacts['address'] = ', '.join(address_parts)
                        contacts['found'] = True
                
                time.sleep(self.request_delay)
                
        except Exception as e:
            print(f"⚠️ Ошибка при запросе {vacancy_id}: {e}")
        
        return contacts
    
    def search_company(self, company_name: str, vacancy_link: str = None) -> Optional[Dict]:
        """
        Поиск компании через бесплатные источники
        
        Args:
            company_name: Название компании
            vacancy_link: Ссылка на вакансию HH.ru
            
        Returns:
            Словарь с контактами или None
        """
        # Проверяем кеш
        cache_key = f"free_{company_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        contacts = {
            'company_name': company_name,
            'found': False,
            'source': 'free',
            'phones': [],
            'emails': [],
            'websites': [],
            'hh_company_url': '',
            'address': '',
            'search_date': datetime.now().isoformat()
        }
        
        # Извлекаем ID вакансии из ссылки
        if vacancy_link:
            try:
                vacancy_id = vacancy_link.split('/')[-1].split('?')[0]
                hh_contacts = self.extract_contacts_from_hh(vacancy_id, company_name)
                
                if hh_contacts.get('found'):
                    # Объединяем контакты
                    contacts['phones'].extend(hh_contacts.get('phones', []))
                    contacts['emails'].extend(hh_contacts.get('emails', []))
                    contacts['websites'].extend(hh_contacts.get('websites', []))
                    contacts['hh_company_url'] = hh_contacts.get('hh_company_url', '')
                    contacts['address'] = hh_contacts.get('address', '')
                    contacts['found'] = True
                    
            except Exception as e:
                pass
        
        # Сохраняем в кеш
        self.cache[cache_key] = contacts
        self._save_cache()
        
        return contacts if contacts['found'] else None
    
    def process_vacancies(self, json_file: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Обработка файла с вакансиями
        
        Args:
            json_file: Путь к JSON файлу с вакансиями
            limit: Ограничение количества компаний (None = все)
            
        Returns:
            Список с контактами
        """
        print("=" * 70)
        print("🆓 БЕСПЛАТНЫЙ ПОИСК КОНТАКТОВ")
        print("=" * 70)
        print()
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                vacancies = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return []
        
        # Группируем вакансии по компаниям
        companies_vacancies = {}
        for vacancy in vacancies:
            company = vacancy.get('компания', '').strip()
            if not company:
                continue
            
            if company not in companies_vacancies:
                companies_vacancies[company] = []
            
            companies_vacancies[company].append(vacancy)
        
        companies = list(companies_vacancies.keys())
        
        print(f"📊 Найдено уникальных компаний: {len(companies)}")
        
        if limit:
            companies = companies[:limit]
            print(f"🔍 Обрабатываем первые {limit} компаний")
        
        print()
        print("🚀 Начинаем бесплатный поиск контактов...")
        print("💡 Источник: HH.ru API (без лимитов)")
        print()
        
        results = []
        total = len(companies)
        
        for i, company in enumerate(companies, 1):
            print(f"[{i}/{total}] {company}...", end=' ')
            
            # Берем первую вакансию компании
            vacancy = companies_vacancies[company][0]
            vacancy_link = vacancy.get('ссылка', '')
            
            contacts = self.search_company(company, vacancy_link)
            
            if contacts and contacts.get('found'):
                has_phone = len(contacts.get('phones', [])) > 0
                has_email = len(contacts.get('emails', [])) > 0
                has_website = len(contacts.get('websites', [])) > 0
                
                info_parts = []
                if has_phone:
                    info_parts.append(f"тел: {len(contacts['phones'])}")
                if has_email:
                    info_parts.append(f"email: {len(contacts['emails'])}")
                if has_website:
                    info_parts.append(f"web: {len(contacts['websites'])}")
                
                print(f"✓ {', '.join(info_parts) if info_parts else 'базовая инфо'}")
                results.append(contacts)
            else:
                print("✗ не найдено")
                # Все равно добавляем с базовой информацией
                if contacts:
                    results.append(contacts)
        
        print()
        print(f"✅ Обработано компаний: {total}")
        print(f"✅ Найдены контакты: {len([r for r in results if r.get('found')])}")
        
        return results
    
    def export_to_csv(self, results: List[Dict], output_file: str):
        """Экспорт результатов в CSV"""
        try:
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = [
                    'company_name', 'found', 'phones', 'emails', 
                    'websites', 'hh_company_url', 'address', 'search_date'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {
                        'company_name': result.get('company_name', ''),
                        'found': result.get('found', False),
                        'phones': '; '.join(result.get('phones', [])),
                        'emails': '; '.join(result.get('emails', [])),
                        'websites': '; '.join(result.get('websites', [])),
                        'hh_company_url': result.get('hh_company_url', ''),
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
    
    # HH.ru API ключи (опционально, пока не используются)
    HH_CLIENT_ID = "P14G5BN3LVSKGOIF950ES9TF5GQRHMUUCH39Q5EH1UT6NECRCBMIE1B2DFK16PNN"
    HH_CLIENT_SECRET = "GSTLUNV4MRGJC9SVSQV20HQMTOU6DJMP3506Q0OPV3BISP2UO5QON0SPS6PHB0KC"
    
    # Входной файл
    INPUT_FILE = "vacancies_all.json"
    
    # Ограничение (None = все компании)
    LIMIT = None  # Можно начать с 100 для теста
    
    # Выходные файлы
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT_CSV = f"free_contacts_{timestamp}.csv"
    OUTPUT_JSON = f"free_contacts_{timestamp}.json"
    
    # =====================================
    
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🆓 БЕСПЛАТНЫЙ ПОИСК КОНТАКТОВ" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("💡 Особенности:")
    print("   - Использует только HH.ru API (без лимитов)")
    print("   - Не требует 2GIS API")
    print("   - Можно обработать ВСЕ 5,357 компаний бесплатно")
    print("   - Результаты: сайты компаний, email, телефоны из вакансий")
    print()
    
    if LIMIT:
        response = input(f"Обработать {LIMIT} компаний? (да/нет): ").strip().lower()
    else:
        response = input("Обработать ВСЕ компании? (да/нет): ").strip().lower()
    
    if response not in ['да', 'yes', 'y', 'д']:
        print("Отменено.")
        return
    
    # Создаем поисковик
    finder = FreeContactsFinder(HH_CLIENT_ID, HH_CLIENT_SECRET)
    
    # Обрабатываем
    results = finder.process_vacancies(INPUT_FILE, LIMIT)
    
    if results:
        # Статистика
        print()
        print("=" * 70)
        print("📊 СТАТИСТИКА")
        print("=" * 70)
        found = [r for r in results if r.get('found')]
        print(f"Обработано компаний: {len(results)}")
        print(f"Найдены контакты: {len(found)}")
        print(f"Не найдено: {len(results) - len(found)}")
        
        if found:
            with_phones = len([r for r in found if r.get('phones')])
            with_emails = len([r for r in found if r.get('emails')])
            with_websites = len([r for r in found if r.get('websites')])
            with_hh_url = len([r for r in found if r.get('hh_company_url')])
            
            print()
            print("Контакты:")
            print(f"  📞 С телефонами: {with_phones}")
            print(f"  📧 С email: {with_emails}")
            print(f"  🌐 С сайтами: {with_websites}")
            print(f"  🔗 С HH.ru профилем: {with_hh_url}")
        
        print("=" * 70)
        print()
        
        # Экспортируем
        finder.export_to_csv(results, OUTPUT_CSV)
        finder.export_to_json(results, OUTPUT_JSON)
        
        print()
        print("✅ ГОТОВО!")
        print()
        print("💡 Совет: Эти данные можно дополнить результатами из 2GIS API")
    else:
        print("❌ Нет результатов")


if __name__ == "__main__":
    main()

