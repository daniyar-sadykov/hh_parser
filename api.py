"""
🚀 FastAPI для HH.ru парсера
Использование: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import json
from datetime import datetime

from hh_parser import HHParser

# ================================================================
# ИНИЦИАЛИЗАЦИЯ FASTAPI
# ================================================================

app = FastAPI(
    title="HH.ru Vacancy Parser API",
    description="API для парсинга вакансий с HH.ru с умными фильтрами",
    version="1.0.0"
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
# PYDANTIC МОДЕЛИ (структура запросов/ответов)
# ================================================================

class VacancySearchRequest(BaseModel):
    """Запрос на поиск вакансий"""
    keywords: str = Field(..., description="Ключевые слова для поиска", example="входящие заявки CRM оператор")
    region: int = Field(1, description="ID региона (1=Москва, 2=СПб, 113=Россия)", example=1)
    min_salary: Optional[int] = Field(None, description="Минимальная зарплата", example=50000)
    only_with_salary: bool = Field(True, description="Только с указанной зарплатой", example=True)
    period: int = Field(7, description="За последние N дней (1, 3, 7, 30)", example=7)
    excluded_words: str = Field(
        "недвижимость брокер страхование агент", 
        description="Слова для исключения (через пробел или запятую)",
        example="недвижимость брокер"
    )
    sort_by: str = Field(
        "publication_time", 
        description="Сортировка (publication_time, relevance, salary_desc)",
        example="publication_time"
    )
    max_results: int = Field(500, description="Максимум результатов", example=500, ge=1, le=2000)


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
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    ❤️ Проверка работоспособности API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/search", response_model=VacancySearchResponse)
async def search_vacancies(request: VacancySearchRequest):
    """
    🔍 ОСНОВНОЙ ЭНДПОИНТ: Поиск вакансий
    
    Возвращает вакансии с HH.ru по заданным критериям
    """
    try:
        # Инициализация парсера
        parser = HHParser(delay=0.3)
        
        # Вычисляем количество страниц
        max_pages = (request.max_results + 99) // 100  # Округление вверх
        
        # Поиск вакансий
        vacancies = parser.search_vacancies(
            keywords=request.keywords,
            area=request.region,
            salary=request.min_salary,
            only_with_salary=request.only_with_salary,
            period=request.period,
            excluded_text=request.excluded_words,
            order_by=request.sort_by,
            max_pages=max_pages
        )
        
        # Ограничиваем результат
        vacancies = vacancies[:request.max_results]
        
        # Статистика
        with_salary_count = sum(1 for v in vacancies if v['оплата'] != 'Не указана')
        unique_companies = len(set(v['компания'] for v in vacancies))
        
        statistics = {
            "total_found": len(vacancies),
            "with_salary": with_salary_count,
            "with_salary_percent": round(with_salary_count / len(vacancies) * 100, 1) if vacancies else 0,
            "unique_companies": unique_companies,
            "search_params": {
                "keywords": request.keywords,
                "region": request.region,
                "min_salary": request.min_salary,
                "period_days": request.period
            }
        }
        
        return {
            "success": True,
            "count": len(vacancies),
            "message": f"Найдено {len(vacancies)} вакансий",
            "statistics": statistics,
            "vacancies": vacancies
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге: {str(e)}")


@app.post("/api/search-quick")
async def search_quick(
    keywords: str,
    region: int = 1,
    max_results: int = 100
):
    """
    ⚡ БЫСТРЫЙ ПОИСК (упрощенный)
    
    Минимум параметров, оптимальные настройки по умолчанию
    """
    try:
        parser = HHParser(delay=0.3)
        max_pages = (max_results + 99) // 100
        
        vacancies = parser.search_vacancies(
            keywords=keywords,
            area=region,
            salary=50000,
            only_with_salary=True,
            period=7,
            excluded_text="недвижимость брокер страхование агент",
            order_by='publication_time',
            max_pages=max_pages
        )
        
        vacancies = vacancies[:max_results]
        
        return {
            "success": True,
            "count": len(vacancies),
            "vacancies": vacancies
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

