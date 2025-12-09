"""
🎯 ШПАРГАЛКА: Примеры использования HH Parser с новыми фильтрами
"""

from hh_parser import HHParser

# ================================================================
# 🔥 ПРИМЕР 1: Оптимальные настройки для автоотклика
# ================================================================

def example_autorespond():
    """Максимально релевантные вакансии для автоотклика"""
    parser = HHParser(delay=0.3)
    
    vacancies = parser.search_vacancies(
        keywords="входящие заявки CRM оператор менеджер",
        area=1,                           # Москва
        salary=50000,                     # От 50к
        only_with_salary=True,            # Только с зарплатой ✅
        period=7,                         # За неделю ✅
        excluded_text="недвижимость брокер страхование агент",  # Убираем мусор ✅
        order_by='publication_time',      # Новые первые ✅
        max_pages=15                      # 1500 вакансий
    )
    
    print(f"✅ Найдено: {len(vacancies)} релевантных вакансий")
    
    # Сохраняем
    parser.save_to_json(vacancies, 'vacancies_filtered.json')
    
    return vacancies


# ================================================================
# 🎯 ПРИМЕР 2: Удаленная работа по всей России
# ================================================================

def example_remote_work():
    """Поиск удаленных вакансий"""
    parser = HHParser()
    
    vacancies = parser.search_vacancies(
        keywords="оператор CRM входящие",
        area=113,                         # Вся Россия
        salary=40000,                     # От 40к
        only_with_salary=True,
        period=7,
        # Можно добавить schedule='remote' в будущем
        excluded_text="недвижимость брокер продажи",
        order_by='publication_time',
        max_pages=10
    )
    
    return vacancies


# ================================================================
# 💎 ПРИМЕР 3: Высокооплачиваемые вакансии
# ================================================================

def example_high_salary():
    """Топовые вакансии с высокой зарплатой"""
    parser = HHParser()
    
    vacancies = parser.search_vacancies(
        keywords="менеджер по работе с клиентами",
        area=1,                           # Москва
        salary=100000,                    # От 100к
        only_with_salary=True,
        period=30,                        # Месяц (так как высокая зарплата = меньше вакансий)
        order_by='salary_desc',           # Сначала самые высокооплачиваемые
        max_pages=5
    )
    
    return vacancies


# ================================================================
# 🔍 ПРИМЕР 4: Широкий поиск (максимум вакансий)
# ================================================================

def example_wide_search():
    """Максимальное количество вакансий без строгих фильтров"""
    parser = HHParser()
    
    vacancies = parser.search_vacancies(
        keywords="менеджер клиент",
        area=1,
        salary=None,                      # Без фильтра зарплаты
        only_with_salary=False,           # Все вакансии
        period=30,                        # За месяц
        excluded_text="недвижимость",     # Минимальные исключения
        order_by='relevance',             # По релевантности
        max_pages=50                      # Много страниц
    )
    
    return vacancies


# ================================================================
# ⚡ ПРИМЕР 5: Супер-быстрый парсинг (свежие вакансии)
# ================================================================

def example_fresh_only():
    """Только вчерашние вакансии - максимальная скорость отклика"""
    parser = HHParser(delay=0.2)  # Меньше задержка
    
    vacancies = parser.search_vacancies(
        keywords="оператор входящие CRM",
        area=1,
        salary=45000,
        only_with_salary=True,
        period=1,                         # ⚡ ТОЛЬКО ЗА ВЧЕРА!
        excluded_text="недвижимость брокер страхование",
        order_by='publication_time',
        max_pages=5                       # Меньше страниц = быстрее
    )
    
    print(f"⚡ Свежак! Найдено {len(vacancies)} вакансий за последний день")
    
    return vacancies


# ================================================================
# 🎨 ПРИМЕР 6: Для API endpoint (FastAPI)
# ================================================================

def example_api_usage():
    """Использование в API"""
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional
    
    app = FastAPI()
    
    class VacancySearchRequest(BaseModel):
        keywords: str
        region: int = 1
        min_salary: Optional[int] = 50000
        only_with_salary: bool = True
        days: int = 7
        excluded_words: str = "недвижимость брокер страхование"
        max_results: int = 1000  # пользователь указывает количество результатов
    
    @app.post("/api/search-vacancies")
    async def search_vacancies(request: VacancySearchRequest):
        parser = HHParser()
        
        # Конвертируем max_results в max_pages (100 вакансий на страницу)
        max_pages = (request.max_results + 99) // 100
        
        try:
            vacancies = parser.search_vacancies(
                keywords=request.keywords,
                area=request.region,
                salary=request.min_salary,
                only_with_salary=request.only_with_salary,
                period=request.days,
                excluded_text=request.excluded_words,
                order_by='publication_time',
                max_pages=max_pages
            )
            
            return {
                "success": True,
                "count": len(vacancies),
                "vacancies": vacancies[:request.max_results]  # Ограничиваем по запросу
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# ================================================================
# 📊 ПРИМЕР 7: С детальной статистикой
# ================================================================

def example_with_statistics():
    """Парсинг + анализ результатов"""
    parser = HHParser()
    
    vacancies = parser.search_vacancies(
        keywords="менеджер CRM",
        area=1,
        salary=50000,
        only_with_salary=True,
        period=7,
        excluded_text="недвижимость брокер",
        order_by='publication_time',
        max_pages=10
    )
    
    # Анализ результатов
    if vacancies:
        # Статистика по зарплатам
        salaries = []
        for v in vacancies:
            salary_text = v['оплата']
            if 'от' in salary_text:
                try:
                    salary = int(salary_text.split('от')[1].split()[0].replace(' ', ''))
                    salaries.append(salary)
                except:
                    pass
        
        if salaries:
            avg_salary = sum(salaries) / len(salaries)
            print(f"\n💰 Средняя зарплата: {avg_salary:,.0f} руб.".replace(',', ' '))
            print(f"💰 Минимум: {min(salaries):,} руб.".replace(',', ' '))
            print(f"💰 Максимум: {max(salaries):,} руб.".replace(',', ' '))
        
        # Топ компаний
        from collections import Counter
        companies = [v['компания'] for v in vacancies]
        top_companies = Counter(companies).most_common(5)
        
        print("\n🏢 Топ-5 компаний по количеству вакансий:")
        for company, count in top_companies:
            print(f"  • {company}: {count} вакансий")
    
    return vacancies


# ================================================================
# 🔄 ПРИМЕР 8: Батч-обработка (несколько запросов)
# ================================================================

def example_batch_processing():
    """Несколько запросов по разным критериям"""
    parser = HHParser()
    
    all_vacancies = []
    
    # Запрос 1: Операторы
    print("\n1️⃣ Ищу операторов...")
    vacancies_1 = parser.search_vacancies(
        keywords="оператор входящие CRM",
        area=1,
        salary=40000,
        only_with_salary=True,
        period=7,
        excluded_text="недвижимость",
        order_by='publication_time',
        max_pages=5
    )
    all_vacancies.extend(vacancies_1)
    
    # Запрос 2: Менеджеры
    print("\n2️⃣ Ищу менеджеров...")
    vacancies_2 = parser.search_vacancies(
        keywords="менеджер по работе с клиентами CRM",
        area=1,
        salary=50000,
        only_with_salary=True,
        period=7,
        excluded_text="недвижимость брокер",
        order_by='publication_time',
        max_pages=5
    )
    all_vacancies.extend(vacancies_2)
    
    # Дедупликация по ID
    unique_vacancies = {v['id']: v for v in all_vacancies}.values()
    
    print(f"\n✅ Всего найдено: {len(all_vacancies)}")
    print(f"✅ Уникальных: {len(unique_vacancies)}")
    
    return list(unique_vacancies)


# ================================================================
# 🚀 ЗАПУСК ПРИМЕРОВ
# ================================================================

if __name__ == "__main__":
    print("="*60)
    print("🎯 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ HH PARSER")
    print("="*60)
    
    # Раскомментируйте нужный пример:
    
    # vacancies = example_autorespond()           # Пример 1
    # vacancies = example_remote_work()           # Пример 2
    # vacancies = example_high_salary()           # Пример 3
    # vacancies = example_wide_search()           # Пример 4
    vacancies = example_fresh_only()              # Пример 5 ⚡
    # vacancies = example_with_statistics()       # Пример 7
    # vacancies = example_batch_processing()      # Пример 8
    
    print(f"\n✅ Готово! Найдено {len(vacancies)} вакансий")

