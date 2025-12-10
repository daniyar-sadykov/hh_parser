"""
🚀 FastAPI для HH.ru парсера
Использование: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import json
from datetime import datetime
from collections import defaultdict
import tempfile
import os

from hh_parser import HHParser
from contacts_search_engine import ContactsSearchEngine

# ================================================================
# ИНИЦИАЛИЗАЦИЯ FASTAPI
# ================================================================

app = FastAPI(
    title="HH.ru Vacancy Parser API",
    description="API для парсинга вакансий с HH.ru с умными фильтрами + поиск контактов компаний",
    version="2.0.0"
)

# Инициализация движка поиска контактов
# API ключ 2GIS - можно задать через переменную окружения
import os
API_KEY_2GIS = os.getenv("API_KEY_2GIS", "75730e35-2767-46d6-b42b-548b4acae13e")

contacts_engine = ContactsSearchEngine(
    api_key_2gis=API_KEY_2GIS,
    enable_2gis=True,
    enable_hh=True,
    enable_website_parsing=True
)

# CORS (для доступа из браузера/n8n)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ================================================================

def normalize_company_name(company: str) -> str:
    """
    Нормализация названия компании для дедупликации
    """
    if not company:
        return ""
    
    company_lower = company.lower().strip()
    
    # Убираем общие префиксы/суффиксы
    replacements = [
        ('ооо ', ''),
        ('оао ', ''),
        ('зао ', ''),
        ('пао ', ''),
        ('ип ', ''),
        ('индивидуальный предприниматель ', ''),
        (' ооо', ''),
        (' оао', ''),
        ('"', ''),
        ("'", ''),
        ('«', ''),
        ('»', ''),
    ]
    
    for old, new in replacements:
        company_lower = company_lower.replace(old, new)
    
    return company_lower.strip()


def calculate_vacancy_score(vacancy: Dict) -> int:
    """
    Рассчитывает оценку вакансии для выбора лучшей при дедупликации
    """
    score = 0
    
    title = vacancy.get('название', '').lower()
    description = vacancy.get('описание', '').lower()
    
    # Базовая оценка
    if '_pre_score' in vacancy:
        score += vacancy['_pre_score'] * 10
    else:
        score += 50
    
    # Приоритетные ключевые слова
    priority_keywords = [
        'входящие заявки', 'обработка заявок', 'crm', 'битрикс',
        'amocrm', 'чат', 'оператор', 'менеджер по работе с клиентами',
        'support', 'техподдержка', 'колл-центр'
    ]
    
    # Бонусы за ключевые слова в названии
    for keyword in priority_keywords:
        if keyword in title:
            score += 20
    
    # Бонусы за ключевые слова в описании
    for keyword in priority_keywords:
        if keyword in description:
            score += 5
    
    # Бонус за наличие зарплаты
    salary = vacancy.get('оплата', '')
    if salary and salary != 'Не указана' and 'руб' in salary:
        score += 10
    
    # Бонус за длину описания
    desc_length = len(description)
    if desc_length > 1000:
        score += 10
    elif desc_length > 500:
        score += 5
    
    # Бонус за свежесть
    date_pub = vacancy.get('дата_публикации', '')
    if '2025-12' in date_pub:
        score += 15
    elif '2025-11' in date_pub:
        score += 10
    
    return score


def deduplicate_vacancies(vacancies: List[Dict]) -> List[Dict]:
    """
    Удаляет дубликаты вакансий от одной компании
    Оставляет только лучшую вакансию от каждой компании
    """
    if not vacancies:
        return []
    
    # Группируем по компаниям
    companies = defaultdict(list)
    
    for vacancy in vacancies:
        company = vacancy.get('компания', '')
        if not company:
            # Вакансии без компании оставляем как есть
            companies[f'_no_company_{id(vacancy)}'].append(vacancy)
        else:
            normalized = normalize_company_name(company)
            companies[normalized].append(vacancy)
    
    # Выбираем лучшую вакансию от каждой компании
    result = []
    duplicates_removed = 0
    
    for company_key, company_vacancies in companies.items():
        if len(company_vacancies) == 1:
            result.append(company_vacancies[0])
        else:
            # Оцениваем все вакансии компании
            scored_vacancies = [
                (vacancy, calculate_vacancy_score(vacancy))
                for vacancy in company_vacancies
            ]
            
            # Сортируем по оценке
            scored_vacancies.sort(key=lambda x: x[1], reverse=True)
            
            # Берём лучшую
            best_vacancy = scored_vacancies[0][0]
            best_vacancy['_duplicates_removed'] = len(company_vacancies) - 1
            
            result.append(best_vacancy)
            duplicates_removed += len(company_vacancies) - 1
    
    return result


def create_txt_file(vacancies: List[Dict], filename: str = None) -> str:
    """
    Создаёт TXT файл с вакансиями и возвращает путь к файлу
    """
    if filename is None:
        # Создаём временный файл
        fd, filename = tempfile.mkstemp(suffix='.txt', prefix='vacancies_')
        os.close(fd)
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i, vac in enumerate(vacancies, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"ВАКАНСИЯ #{i}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Название: {vac.get('название', 'N/A')}\n")
            f.write(f"Компания: {vac.get('компания', 'N/A')}\n")
            f.write(f"Оплата: {vac.get('оплата', 'Не указана')}\n")
            f.write(f"Ссылка: {vac.get('ссылка', 'N/A')}\n")
            f.write(f"\nОписание:\n{vac.get('описание', 'Нет описания')}\n")
            f.write(f"\n{'-'*80}\n")
    
    return filename

# ================================================================
# PYDANTIC МОДЕЛИ (структура запросов/ответов)
# ================================================================

class VacancySearchRequest(BaseModel):
    """Запрос на поиск вакансий"""
    keywords: str = Field(..., description="Ключевые слова для поиска", json_schema_extra={"example": "входящие заявки CRM оператор"})
    region: int = Field(1, description="ID региона (1=Москва, 2=СПб, 113=Россия)", json_schema_extra={"example": 1})
    min_salary: Optional[int] = Field(None, description="Минимальная зарплата", json_schema_extra={"example": 50000})
    only_with_salary: bool = Field(True, description="Только с указанной зарплатой", json_schema_extra={"example": True})
    period: int = Field(7, description="За последние N дней (1, 3, 7, 30)", json_schema_extra={"example": 7})
    excluded_words: str = Field(
        "недвижимость брокер страхование агент", 
        description="Слова для исключения (через пробел или запятую)",
        json_schema_extra={"example": "недвижимость брокер"}
    )
    sort_by: str = Field(
        "publication_time", 
        description="Сортировка (publication_time, relevance, salary_desc)",
        json_schema_extra={"example": "publication_time"}
    )
    limit: int = Field(20, description="Сколько ВЕРНУТЬ самых свежих вакансий (по умолчанию 20)", json_schema_extra={"example": 20}, ge=1, le=1000)
    max_results: int = Field(10000, description="Максимум вакансий для ПОИСКА (внутренний параметр, по умолчанию 10000)", json_schema_extra={"example": 10000}, ge=1, le=10000)


class VacancyItem(BaseModel):
    """Одна вакансия"""
    id: str
    название: str
    компания: str
    оплата: str
    описание: str
    ссылка: str
    опыт: str
    тип_занятости: str
    дата_публикации: str


class VacancySearchResponse(BaseModel):
    """Ответ с вакансиями"""
    success: bool
    count: int
    message: str
    statistics: Dict
    vacancies: List[Dict]


class HealthResponse(BaseModel):
    """Ответ health check"""
    status: str
    timestamp: str
    version: str


class ContactsSearchRequest(BaseModel):
    """Запрос на поиск контактов компании"""
    company_name: str = Field(..., description="Название компании", example="Яндекс")
    city: str = Field("Москва", description="Город поиска", example="Москва")
    vacancy_link: Optional[str] = Field(None, description="Ссылка на вакансию HH.ru (опционально)", example="https://hh.ru/vacancy/123456")


class ContactsSearchResponse(BaseModel):
    """Ответ с контактами компании"""
    success: bool
    company_name: str
    found: bool
    sources: List[str]
    contacts: Dict
    additional_info: Dict
    search_date: str
    from_cache: bool


# ================================================================
# ЭНДПОИНТЫ API
# ================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """
    🏠 Главная страница API
    """
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    ❤️ Проверка работоспособности API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.post("/api/search", response_model=VacancySearchResponse)
async def search_vacancies(request: VacancySearchRequest):
    """
    🔍 ОСНОВНОЙ ЭНДПОИНТ: Поиск вакансий
    
    Ищет ВСЕ подходящие вакансии, но возвращает только N самых свежих.
    
    Логика:
    1. Backend ищет максимум вакансий (до 10000)
    2. ДЕДУПЛИЦИРУЕТ по компаниям (1 компания = 1 вакансия)
    3. Сортирует по дате публикации (свежие первыми)
    4. Возвращает только первые `limit` штук (по умолчанию 20)
    
    Это позволяет N8N получать только самые актуальные вакансии без дубликатов!
    """
    try:
        # Инициализация парсера
        parser = HHParser(delay=0.3)
        
        # Вычисляем количество страниц для поиска ВСЕХ вакансий
        max_pages = (request.max_results + 99) // 100  # Округление вверх
        
        # ВАЖНО: Ищем ВСЕ вакансии с сортировкой по дате!
        all_vacancies = parser.search_vacancies(
            keywords=request.keywords,
            area=request.region,
            salary=request.min_salary,
            only_with_salary=request.only_with_salary,
            period=request.period,
            excluded_text=request.excluded_words,
            order_by='publication_time',  # ВСЕГДА по дате!
            max_pages=max_pages
        )
        
        # ДЕДУПЛИЦИРУЕМ (удаляем дубликаты компаний)
        before_dedup = len(all_vacancies)
        all_vacancies = deduplicate_vacancies(all_vacancies)
        after_dedup = len(all_vacancies)
        duplicates_removed = before_dedup - after_dedup
        
        # Сортируем по дате (на всякий случай, если API вернул не в порядке)
        all_vacancies.sort(
            key=lambda x: x.get('дата_публикации', ''), 
            reverse=True  # Новые первыми
        )
        
        # ОГРАНИЧИВАЕМ до limit самых свежих
        freshest_vacancies = all_vacancies[:request.limit]
        
        # Статистика
        with_salary_count = sum(1 for v in freshest_vacancies if v['оплата'] != 'Не указана')
        unique_companies = len(set(v['компания'] for v in freshest_vacancies if v.get('компания')))
        
        statistics = {
            "total_found": before_dedup,  # Сколько ВСЕГО нашли
            "after_deduplication": after_dedup,  # После удаления дубликатов
            "duplicates_removed": duplicates_removed,  # Удалено дубликатов
            "returned_count": len(freshest_vacancies),  # Сколько ВЕРНУЛИ
            "with_salary": with_salary_count,
            "with_salary_percent": round(with_salary_count / len(freshest_vacancies) * 100, 1) if freshest_vacancies else 0,
            "unique_companies": unique_companies,
            "search_params": {
                "keywords": request.keywords,
                "region": request.region,
                "min_salary": request.min_salary,
                "period_days": request.period,
                "limit": request.limit
            }
        }
        
        return {
            "success": True,
            "count": len(freshest_vacancies),
            "message": f"Найдено {before_dedup} вакансий, после дедупликации {after_dedup}, возвращено {len(freshest_vacancies)} самых свежих",
            "statistics": statistics,
            "vacancies": freshest_vacancies  # Только самые свежие без дубликатов!
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге: {str(e)}")


@app.post("/api/search-quick")
async def search_quick(
    keywords: str,
    region: int = 1,
    limit: int = 20  # Сколько вернуть самых свежих
):
    """
    ⚡ БЫСТРЫЙ ПОИСК (упрощенный)
    
    Минимум параметров, оптимальные настройки по умолчанию.
    Ищет ВСЕ вакансии, дедуплицирует, возвращает только N самых свежих.
    """
    try:
        parser = HHParser(delay=0.3)
        
        # Ищем максимум (до 100 страниц = 10000 вакансий)
        all_vacancies = parser.search_vacancies(
            keywords=keywords,
            area=region,
            salary=50000,
            only_with_salary=True,
            period=7,
            excluded_text="недвижимость брокер страхование агент",
            order_by='publication_time',  # Свежие первыми!
            max_pages=100  # Искать максимум
        )
        
        # ДЕДУПЛИЦИРУЕМ
        before_dedup = len(all_vacancies)
        all_vacancies = deduplicate_vacancies(all_vacancies)
        after_dedup = len(all_vacancies)
        
        # Сортируем по дате
        all_vacancies.sort(
            key=lambda x: x.get('дата_публикации', ''), 
            reverse=True
        )
        
        # Берём только N самых свежих
        freshest_vacancies = all_vacancies[:limit]
        
        return {
            "success": True,
            "total_found": before_dedup,
            "after_deduplication": after_dedup,
            "duplicates_removed": before_dedup - after_dedup,
            "returned_count": len(freshest_vacancies),
            "vacancies": freshest_vacancies
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vacancy/{vacancy_id}")
async def get_vacancy_details(vacancy_id: str):
    """
    📄 Получить детали одной вакансии по ID
    """
    try:
        parser = HHParser()
        vacancy = parser.get_vacancy_details(vacancy_id)
        
        if vacancy:
            return {
                "success": True,
                "vacancy": vacancy
            }
        else:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/regions")
async def get_regions():
    """
    🌍 Список популярных регионов
    """
    return {
        "regions": [
            {"id": 1, "name": "Москва"},
            {"id": 2, "name": "Санкт-Петербург"},
            {"id": 3, "name": "Екатеринбург"},
            {"id": 4, "name": "Новосибирск"},
            {"id": 66, "name": "Нижний Новгород"},
            {"id": 88, "name": "Казань"},
            {"id": 113, "name": "Россия (все регионы)"}
        ]
    }


@app.post("/api/search-txt")
async def search_vacancies_txt(request: VacancySearchRequest):
    """
    📄 ПОИСК ВАКАНСИЙ С ВОЗВРАТОМ TXT ФАЙЛА
    
    Работает так же как /api/search, но возвращает TXT файл вместо JSON.
    Идеально для N8N - сразу получаете файл для отправки в Telegram!
    
    Логика:
    1. Ищет ВСЕ вакансии
    2. Дедуплицирует (1 компания = 1 вакансия)
    3. Сортирует по дате (свежие первыми)
    4. Берёт только limit самых свежих
    5. Создаёт TXT файл
    6. Возвращает файл
    """
    try:
        # Инициализация парсера
        parser = HHParser(delay=0.3)
        
        # Вычисляем количество страниц
        max_pages = (request.max_results + 99) // 100
        
        # Ищем ВСЕ вакансии
        all_vacancies = parser.search_vacancies(
            keywords=request.keywords,
            area=request.region,
            salary=request.min_salary,
            only_with_salary=request.only_with_salary,
            period=request.period,
            excluded_text=request.excluded_words,
            order_by='publication_time',
            max_pages=max_pages
        )
        
        # ДЕДУПЛИЦИРУЕМ
        before_dedup = len(all_vacancies)
        all_vacancies = deduplicate_vacancies(all_vacancies)
        
        # Сортируем по дате
        all_vacancies.sort(
            key=lambda x: x.get('дата_публикации', ''), 
            reverse=True
        )
        
        # Берём только limit самых свежих
        freshest_vacancies = all_vacancies[:request.limit]
        
        # Создаём TXT файл
        txt_file = create_txt_file(freshest_vacancies)
        
        # Возвращаем файл
        return FileResponse(
            path=txt_file,
            filename=f"vacancies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            media_type="text/plain",
            background=None  # Файл удалится автоматически после отправки
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.post("/api/analyze")
async def analyze_vacancies(vacancies: List[Dict]):
    """
    📊 Анализ списка вакансий
    
    Принимает массив вакансий, возвращает статистику
    """
    try:
        if not vacancies:
            return {
                "success": False,
                "message": "Пустой список вакансий"
            }
        
        # Подсчет статистики
        with_salary = sum(1 for v in vacancies if v.get('оплата') != 'Не указана')
        companies = [v.get('компания') for v in vacancies if v.get('компания')]
        unique_companies = len(set(companies))
        
        # Топ компаний
        from collections import Counter
        top_companies = Counter(companies).most_common(5)
        
        # Средняя зарплата (примерная)
        salaries = []
        for v in vacancies:
            salary_text = v.get('оплата', '')
            if 'от' in salary_text:
                try:
                    salary = int(salary_text.split('от')[1].split()[0].replace(' ', ''))
                    salaries.append(salary)
                except:
                    pass
        
        avg_salary = sum(salaries) / len(salaries) if salaries else 0
        
        return {
            "success": True,
            "statistics": {
                "total": len(vacancies),
                "with_salary": with_salary,
                "with_salary_percent": round(with_salary / len(vacancies) * 100, 1),
                "unique_companies": unique_companies,
                "average_salary": round(avg_salary, 0) if avg_salary else None,
                "top_companies": [{"name": name, "count": count} for name, count in top_companies]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# ЭНДПОИНТЫ ПОИСКА КОНТАКТОВ КОМПАНИЙ
# ================================================================

@app.post("/api/contacts/search", response_model=ContactsSearchResponse)
async def search_company_contacts(request: ContactsSearchRequest):
    """
    🔍 НОВЫЙ ЭНДПОИНТ: Поиск контактов компании
    
    Ищет контакты компании через все доступные источники:
    - 2GIS API (телефоны, email, адреса, сайты)
    - HH.ru (сайты компании, контакты из вакансий)
    - Парсинг сайтов (Telegram, WhatsApp, дополнительные контакты)
    
    Использует кеширование для экономии API лимитов.
    """
    try:
        result = contacts_engine.search_company(
            company_name=request.company_name,
            city=request.city,
            vacancy_link=request.vacancy_link
        )
        
        return {
            "success": True,
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске контактов: {str(e)}")


@app.post("/api/contacts/search-quick")
async def search_company_contacts_quick(
    company_name: str,
    city: str = "Москва"
):
    """
    ⚡ БЫСТРЫЙ ПОИСК КОНТАКТОВ (упрощенный)
    
    Минимум параметров, используется для N8N интеграции
    """
    try:
        result = contacts_engine.search_company(
            company_name=company_name,
            city=city
        )
        
        return {
            "success": True,
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contacts/batch")
async def search_batch_contacts(companies: List[Dict]):
    """
    📦 ПАКЕТНЫЙ ПОИСК КОНТАКТОВ
    
    Принимает массив компаний, возвращает контакты для каждой
    
    Пример запроса:
    [
        {"company_name": "Яндекс", "city": "Москва"},
        {"company_name": "Сбер", "city": "Москва"}
    ]
    """
    try:
        if not companies:
            return {
                "success": False,
                "message": "Пустой список компаний"
            }
        
        results = []
        
        for company in companies:
            company_name = company.get('company_name')
            city = company.get('city', 'Москва')
            vacancy_link = company.get('vacancy_link')
            
            if not company_name:
                continue
            
            result = contacts_engine.search_company(
                company_name=company_name,
                city=city,
                vacancy_link=vacancy_link
            )
            
            results.append(result)
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contacts/stats")
async def get_contacts_stats():
    """
    📊 Статистика работы движка поиска контактов
    """
    try:
        stats = contacts_engine.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contacts/clear-cache")
async def clear_contacts_cache():
    """
    🗑️ Очистить кеш контактов
    """
    try:
        contacts_engine.clear_cache()
        
        return {
            "success": True,
            "message": "Кеш очищен"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# ЗАПУСК
# ================================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Запуск API сервера...")
    print("=" * 60)
    print("📍 URL: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)

