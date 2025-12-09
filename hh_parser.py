"""
Парсер вакансий с hh.ru через официальный API
Быстрая реализация для получения данных о вакансиях
"""

import requests
import json
import time
import re
from typing import List, Dict, Optional
from datetime import datetime


class HHParser:
    """Класс для парсинга вакансий с hh.ru"""
    
    BASE_URL = "https://api.hh.ru"
    
    def __init__(self, delay: float = 0.3):
        """
        Инициализация парсера
        
        Args:
            delay: Задержка между запросами в секундах (для избежания блокировок)
                   По умолчанию 0.3 сек, так как запрашиваем полные описания
        """
        self.session = requests.Session()
        self.delay = delay
        # Правильные заголовки для API hh.ru
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://hh.ru/',
            'Origin': 'https://hh.ru'
        })
    
    def search_vacancies(
        self, 
        keywords: str, 
        area: int = 1,  # 1 - Москва, 2 - СПб, 113 - Россия
        per_page: int = 100,
        max_pages: Optional[int] = None,
        salary: Optional[int] = None,
        only_with_salary: bool = False,
        period: Optional[int] = None,
        excluded_text: Optional[str] = None,
        order_by: str = 'relevance'
    ) -> List[Dict]:
        """
        Поиск вакансий по ключевым словам
        
        Args:
            keywords: Ключевые слова для поиска
            area: ID региона (1 - Москва, 2 - СПб, 113 - Россия)
            per_page: Количество результатов на странице (до 100)
            max_pages: Максимальное количество страниц (None = все)
            salary: Минимальная зарплата (например: 50000)
            only_with_salary: Только вакансии с указанной зарплатой
            period: Вакансии за последние N дней (1, 3, 7, 30)
            excluded_text: Слова для исключения из результатов
            order_by: Сортировка ('relevance', 'publication_time', 'salary_desc')
        
        Returns:
            Список словарей с данными вакансий
        """
        all_vacancies = []
        page = 0
        total_pages = None
        
        print(f"Начинаю поиск вакансий по запросу: '{keywords}'...")
        if salary:
            print(f"  💰 Минимальная зарплата: {salary:,} руб.".replace(',', ' '))
        if only_with_salary:
            print(f"  ✅ Только с указанной зарплатой")
        if period:
            print(f"  📅 За последние {period} дней")
        if excluded_text:
            print(f"  ❌ Исключаем: {excluded_text}")
        if order_by != 'relevance':
            print(f"  🔢 Сортировка: {order_by}")
        
        while True:
            if max_pages and page >= max_pages:
                break
                
            params = {
                'text': keywords,
                'area': area,
                'per_page': min(per_page, 100),
                'page': page,
                'order_by': order_by
            }
            
            # Добавляем опциональные параметры
            if salary:
                params['salary'] = salary
            if only_with_salary:
                params['only_with_salary'] = 'true'
            if period:
                params['period'] = period
            if excluded_text:
                params['excluded_text'] = excluded_text
            
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/vacancies",
                    params=params,
                    timeout=15
                )
                
                # Проверка статуса ответа
                if response.status_code == 403:
                    print(f"Ошибка 403: Доступ запрещен. Попробуйте позже или проверьте заголовки.")
                    print(f"Ответ сервера: {response.text[:200]}")
                    break
                elif response.status_code == 429:
                    print("Слишком много запросов. Ожидание 60 секунд...")
                    time.sleep(60)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Получаем информацию о количестве страниц (только на первой странице)
                if page == 0:
                    total_pages = data.get('pages', 0)
                    total_found = data.get('found', 0)
                    if total_pages > 0:
                        if max_pages:
                            print(f"Найдено вакансий: {total_found} (будет обработано до {max_pages} страниц)")
                        else:
                            print(f"Найдено вакансий: {total_found} (всего страниц: {total_pages})")
                
                if not data.get('items'):
                    break
                
                # Показываем прогресс
                current_page = page + 1
                if max_pages:
                    print(f"Обрабатываю страницу {current_page}/{max_pages}...", end='\r')
                elif total_pages:
                    print(f"Обрабатываю страницу {current_page}/{total_pages}...", end='\r')
                else:
                    print(f"Обрабатываю страницу {current_page}...", end='\r')
                
                # Получаем полную информацию о каждой вакансии (включая полное описание)
                for item in data['items']:
                    vacancy_id = item['id']
                    full_vacancy = self.get_vacancy_details(vacancy_id)
                    if full_vacancy:
                        all_vacancies.append(full_vacancy)
                
                # Задержка между запросами
                time.sleep(self.delay)
                
                # Проверяем, есть ли еще страницы
                pages = data.get('pages', 0)
                if page >= pages - 1:
                    break
                    
                page += 1
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"Ошибка 403: Доступ запрещен.")
                    print("Возможные причины:")
                    print("- Слишком много запросов")
                    print("- Неправильные заголовки")
                    print("- Блокировка по IP")
                else:
                    print(f"HTTP ошибка {e.response.status_code}: {e}")
                break
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при запросе: {e}")
                break
        
        return all_vacancies
    
    
    def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """
        Получение полной информации о вакансии (дополнительный запрос)
        
        Args:
            vacancy_id: ID вакансии
        
        Returns:
            Словарь с данными вакансии или None при ошибке
        """
        try:
            time.sleep(self.delay)  # Задержка перед запросом
            
            response = self.session.get(
                f"{self.BASE_URL}/vacancies/{vacancy_id}",
                timeout=15
            )
            
            if response.status_code == 403:
                print(f"Ошибка 403 при получении вакансии {vacancy_id}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Форматируем зарплату
            salary = self._format_salary(data.get('salary'))
            
            # Получаем и очищаем описание от HTML
            description = self._clean_html(data.get('description', ''))
            
            # Извлекаем нужные данные
            vacancy = {
                'название': data.get('name', ''),
                'описание': description,
                'оплата': salary,
                'компания': data.get('employer', {}).get('name', ''),
                'ссылка': data.get('alternate_url', ''),
                'id': vacancy_id,
                'опыт': data.get('experience', {}).get('name', ''),
                'тип_занятости': data.get('employment', {}).get('name', ''),
                'дата_публикации': data.get('published_at', '')
            }
            
            return vacancy
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении вакансии {vacancy_id}: {e}")
            return None
    
    def _clean_html(self, html_text: str) -> str:
        """
        Очистка HTML тегов из текста описания
        
        Args:
            html_text: Текст с HTML тегами
        
        Returns:
            Очищенный текст
        """
        if not html_text:
            return ''
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', html_text)
        
        # Заменяем HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _format_salary(self, salary: Optional[Dict]) -> str:
        """
        Форматирование информации о зарплате
        
        Args:
            salary: Словарь с данными о зарплате
        
        Returns:
            Отформатированная строка с зарплатой
        """
        if not salary:
            return 'Не указана'
        
        currency = salary.get('currency', '')
        if currency == 'RUR':
            currency = 'руб.'
        
        from_salary = salary.get('from')
        to_salary = salary.get('to')
        
        if from_salary and to_salary:
            return f"{from_salary:,} - {to_salary:,} {currency}".replace(',', ' ')
        elif from_salary:
            return f"от {from_salary:,} {currency}".replace(',', ' ')
        elif to_salary:
            return f"до {to_salary:,} {currency}".replace(',', ' ')
        else:
            return 'Не указана'
    
    def save_to_json(self, vacancies: List[Dict], filename: str = 'vacancies.json'):
        """Сохранение вакансий в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vacancies, f, ensure_ascii=False, indent=2)
        print(f"Сохранено {len(vacancies)} вакансий в {filename}")
    
    def save_to_txt(self, vacancies: List[Dict], filename: str = 'vacancies.txt'):
        """Сохранение вакансий в текстовый файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            for i, vac in enumerate(vacancies, 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"ВАКАНСИЯ #{i}\n")
                f.write(f"{'='*80}\n")
                f.write(f"Название: {vac['название']}\n")
                f.write(f"Компания: {vac['компания']}\n")
                f.write(f"Оплата: {vac['оплата']}\n")
                f.write(f"Ссылка: {vac['ссылка']}\n")
                f.write(f"\nОписание:\n{vac['описание']}\n")
                f.write(f"\n{'-'*80}\n")
        print(f"Сохранено {len(vacancies)} вакансий в {filename}")


def main():
    """Пример использования парсера"""
    parser = HHParser()
    
    print("="*60)
    print("🔍 ПАРСЕР ВАКАНСИЙ HH.RU")
    print("="*60)
    
    # Введите ключевые слова для поиска
    keywords = input("\nВведите ключевые слова для поиска: ").strip()
    if not keywords:
        keywords = "входящие заявки CRM оператор менеджер"
        print(f"Используются ключевые слова по умолчанию: {keywords}")
    
    # Выбор региона
    print("\n" + "-"*60)
    print("РЕГИОН:")
    print("1 - Москва")
    print("2 - Санкт-Петербург")
    print("113 - Россия")
    area_choice = input("Введите номер (по умолчанию 1): ").strip()
    
    area_map = {'1': 1, '2': 2, '113': 113}
    area = area_map.get(area_choice, 1)
    
    # Минимальная зарплата
    print("\n" + "-"*60)
    print("МИНИМАЛЬНАЯ ЗАРПЛАТА:")
    print("Enter = не указывать")
    print("Или введите сумму (например: 50000)")
    salary_input = input("Минимальная зарплата (руб.): ").strip()
    salary = int(salary_input) if salary_input else None
    
    # Только с зарплатой
    print("\n" + "-"*60)
    only_with_salary_input = input("Только вакансии с указанной зарплатой? (да/нет, по умолчанию: да): ").strip().lower()
    only_with_salary = only_with_salary_input != 'нет'
    
    # Период публикации
    print("\n" + "-"*60)
    print("ПЕРИОД ПУБЛИКАЦИИ:")
    print("1 - За последний день")
    print("3 - За 3 дня")
    print("7 - За неделю (рекомендуется)")
    print("30 - За месяц")
    print("Enter - Без ограничений")
    period_input = input("Выберите период (по умолчанию 7): ").strip()
    period = int(period_input) if period_input else 7
    
    # Исключить слова
    print("\n" + "-"*60)
    print("ИСКЛЮЧИТЬ ИЗ РЕЗУЛЬТАТОВ:")
    print("Enter = стандартный фильтр (недвижимость, брокер, страхование)")
    print("Или введите свои слова через запятую")
    excluded_input = input("Исключить: ").strip()
    excluded_text = excluded_input if excluded_input else "недвижимость, брокер, страхование, агент по недвижимости"
    
    # Сортировка
    print("\n" + "-"*60)
    print("СОРТИРОВКА:")
    print("1 - По дате публикации (новые первые) - РЕКОМЕНДУЕТСЯ")
    print("2 - По релевантности")
    print("3 - По убыванию зарплаты")
    order_input = input("Выберите сортировку (по умолчанию 1): ").strip()
    order_map = {
        '1': 'publication_time',
        '2': 'relevance',
        '3': 'salary_desc'
    }
    order_by = order_map.get(order_input, 'publication_time')
    
    # Количество страниц
    print("\n" + "-"*60)
    print("КОЛИЧЕСТВО СТРАНИЦ:")
    print("Enter или 0 = все страницы")
    print("Или укажите число страниц (например: 10)")
    max_pages_input = input("Введите количество страниц: ").strip()
    if max_pages_input and max_pages_input != '0':
        max_pages = int(max_pages_input)
        print(f"Будут обработаны первые {max_pages} страниц")
    else:
        max_pages = None  # Все страницы
        print("Будут обработаны ВСЕ страницы")
    
    print("\n" + "="*60)
    print("🚀 НАЧИНАЮ ПОИСК...")
    print("="*60)
    print()
    
    # Поиск вакансий
    vacancies = parser.search_vacancies(
        keywords=keywords,
        area=area,
        max_pages=max_pages,
        salary=salary,
        only_with_salary=only_with_salary,
        period=period,
        excluded_text=excluded_text,
        order_by=order_by
    )
    
    print()  # Пустая строка после прогресса
    print("\n" + "="*60)
    print("✅ ПОИСК ЗАВЕРШЕН!")
    print("="*60)
    print(f"Найдено вакансий: {len(vacancies)}")
    
    if vacancies:
        # Сохранение результатов
        parser.save_to_json(vacancies, 'vacancies_all.json')
        parser.save_to_txt(vacancies, 'vacancies_all.txt')
        
        # Статистика
        print("\n📊 СТАТИСТИКА:")
        with_salary = sum(1 for v in vacancies if v['оплата'] != 'Не указана')
        print(f"  • С указанной зарплатой: {with_salary} ({with_salary/len(vacancies)*100:.1f}%)")
        
        companies = set(v['компания'] for v in vacancies)
        print(f"  • Уникальных компаний: {len(companies)}")
        
        # Вывод первых 5 вакансий в консоль
        print("\n" + "="*60)
        print("📋 ПРИМЕРЫ НАЙДЕННЫХ ВАКАНСИЙ (первые 5):")
        print("="*60)
        for i, vac in enumerate(vacancies[:5], 1):
            print(f"\n{i}. {vac['название']}")
            print(f"   Компания: {vac['компания']}")
            print(f"   Оплата: {vac['оплата']}")
            print(f"   Опыт: {vac['опыт']}")
            print(f"   Ссылка: {vac['ссылка']}")
        
        print("\n" + "="*60)
        print("💾 Результаты сохранены:")
        print("  • vacancies_all.json")
        print("  • vacancies_all.txt")
        print("="*60)
    else:
        print("\n⚠️ Вакансии не найдены.")
        print("Попробуйте изменить параметры поиска.")


if __name__ == "__main__":
    main()

