# 🚀 API для HH.ru Парсера - Полная Инструкция

## 📦 УСТАНОВКА

### 1. Установите зависимости:
```bash
pip install -r requirements.txt
```

### 2. Запустите API сервер:
```bash
python api.py
```

Или:
```bash
uvicorn api:app --reload --port 8000
```

### 3. Откройте в браузере:
- **API:** http://localhost:8000
- **Документация (Swagger):** http://localhost:8000/docs
- **Альтернативная документация:** http://localhost:8000/redoc

---

## 🎯 ЭНДПОИНТЫ

### 1️⃣ **POST /api/search** - Основной поиск

**Полный контроль над всеми параметрами**

#### Запрос:
```json
POST http://localhost:8000/api/search
Content-Type: application/json

{
  "keywords": "входящие заявки CRM оператор",
  "region": 1,
  "min_salary": 50000,
  "only_with_salary": true,
  "period": 7,
  "excluded_words": "недвижимость брокер страхование",
  "sort_by": "publication_time",
  "max_results": 500
}
```

#### Ответ:
```json
{
  "success": true,
  "count": 342,
  "message": "Найдено 342 вакансий",
  "statistics": {
    "total_found": 342,
    "with_salary": 342,
    "with_salary_percent": 100.0,
    "unique_companies": 289,
    "search_params": {
      "keywords": "входящие заявки CRM оператор",
      "region": 1,
      "min_salary": 50000,
      "period_days": 7
    }
  },
  "vacancies": [
    {
      "id": "123456",
      "название": "Оператор входящих обращений",
      "компания": "ООО Компания",
      "оплата": "от 60 000 руб.",
      "описание": "Обработка входящих заявок через CRM систему...",
      "ссылка": "https://hh.ru/vacancy/123456",
      "опыт": "Нет опыта",
      "тип_занятости": "Полная занятость",
      "дата_публикации": "2024-12-09T10:30:00+0300"
    },
    ...
  ]
}
```

---

### 2️⃣ **POST /api/search-quick** - Быстрый поиск

**Минимум параметров, оптимальные настройки**

#### Запрос:
```json
POST http://localhost:8000/api/search-quick?keywords=оператор CRM&region=1&max_results=100
```

Или через JSON:
```json
POST http://localhost:8000/api/search-quick
Content-Type: application/json

{
  "keywords": "оператор CRM",
  "region": 1,
  "max_results": 100
}
```

#### Ответ:
```json
{
  "success": true,
  "count": 87,
  "vacancies": [...]
}
```

---

### 3️⃣ **GET /api/vacancy/{id}** - Детали вакансии

#### Запрос:
```
GET http://localhost:8000/api/vacancy/123456
```

#### Ответ:
```json
{
  "success": true,
  "vacancy": {
    "id": "123456",
    "название": "...",
    "описание": "...",
    ...
  }
}
```

---

### 4️⃣ **GET /api/regions** - Список регионов

#### Запрос:
```
GET http://localhost:8000/api/regions
```

#### Ответ:
```json
{
  "regions": [
    {"id": 1, "name": "Москва"},
    {"id": 2, "name": "Санкт-Петербург"},
    {"id": 113, "name": "Россия (все регионы)"}
  ]
}
```

---

### 5️⃣ **POST /api/analyze** - Анализ вакансий

#### Запрос:
```json
POST http://localhost:8000/api/analyze
Content-Type: application/json

{
  "vacancies": [
    {"название": "...", "оплата": "от 50000 руб.", "компания": "..."},
    ...
  ]
}
```

#### Ответ:
```json
{
  "success": true,
  "statistics": {
    "total": 100,
    "with_salary": 95,
    "with_salary_percent": 95.0,
    "unique_companies": 78,
    "average_salary": 65000,
    "top_companies": [
      {"name": "ООО Компания 1", "count": 5},
      {"name": "ООО Компания 2", "count": 3}
    ]
  }
}
```

---

## 🤖 ИСПОЛЬЗОВАНИЕ С GPT

### **Способ 1: Custom GPT с Actions**

1. Создайте Custom GPT в ChatGPT
2. Добавьте Action с URL вашего API
3. Загрузите OpenAPI схему (доступна на `/openapi.json`)

#### Пример промпта для GPT:
```
Ты - ассистент по поиску вакансий.
У тебя есть доступ к API для поиска вакансий на HH.ru.

Когда пользователь просит найти вакансии:
1. Вызови POST /api/search с параметрами
2. Проанализируй JSON ответ
3. Сформируй красивый ответ для пользователя

Пример:
User: Найди вакансии оператора в Москве с зарплатой от 50к
Assistant: [вызывает API] → [анализирует] → [отвечает пользователю]
```

---

### **Способ 2: ChatGPT API + ваш код**

```python
import openai
import requests

# 1. Получаем вакансии через ваш API
response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "keywords": "оператор CRM",
        "region": 1,
        "min_salary": 50000,
        "only_with_salary": True,
        "period": 7,
        "max_results": 20
    }
)

vacancies_data = response.json()

# 2. Отправляем GPT для анализа
client = openai.OpenAI(api_key="your-api-key")

prompt = f"""
Проанализируй эти вакансии и выдели топ-5 самых интересных:

{vacancies_data['vacancies'][:10]}

Критерии:
- Высокая зарплата
- Интересные обязанности
- Известная компания
- CRM система в описании
"""

completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Ты эксперт по анализу вакансий"},
        {"role": "user", "content": prompt}
    ]
)

print(completion.choices[0].message.content)
```

---

## 🔄 ИСПОЛЬЗОВАНИЕ С N8N

### **Шаг 1: HTTP Request узел**

```
Method: POST
URL: http://your-server:8000/api/search
Authentication: None
Body Content Type: JSON

Body:
{
  "keywords": "{{ $json.keywords }}",
  "region": 1,
  "min_salary": 50000,
  "only_with_salary": true,
  "period": 7,
  "max_results": 100
}
```

### **Шаг 2: Обработка ответа**

n8n автоматически парсит JSON ответ:
- `{{ $json.count }}` - количество вакансий
- `{{ $json.vacancies }}` - массив вакансий
- `{{ $json.statistics }}` - статистика

### **Пример workflow в n8n:**

```
Telegram Trigger
    ↓
[Получаем текст от пользователя]
    ↓
HTTP Request → POST /api/search
    ↓
[Получаем JSON с вакансиями]
    ↓
Code Node (обработка)
    ↓
[Форматируем ответ]
    ↓
Telegram Send Message
```

---

## 🐍 ИСПОЛЬЗОВАНИЕ В PYTHON

### **Простой запрос:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "keywords": "менеджер CRM",
        "region": 1,
        "min_salary": 50000,
        "only_with_salary": True,
        "period": 7,
        "max_results": 200
    }
)

data = response.json()

if data['success']:
    print(f"Найдено: {data['count']} вакансий")
    
    for vacancy in data['vacancies'][:5]:
        print(f"\n{vacancy['название']}")
        print(f"Компания: {vacancy['компания']}")
        print(f"Зарплата: {vacancy['оплата']}")
        print(f"Ссылка: {vacancy['ссылка']}")
```

---

## 📱 ПРИМЕРЫ ЗАПРОСОВ (curl)

### **Базовый поиск:**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "оператор CRM",
    "region": 1,
    "min_salary": 50000,
    "only_with_salary": true,
    "period": 7,
    "max_results": 100
  }'
```

### **Быстрый поиск:**
```bash
curl -X POST "http://localhost:8000/api/search-quick?keywords=оператор&max_results=50"
```

### **Получить вакансию по ID:**
```bash
curl "http://localhost:8000/api/vacancy/123456"
```

---

## 🌐 ДЕПЛОЙ НА СЕРВЕР

### **Railway.app:**

1. Создайте `Procfile`:
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

2. Push в GitHub
3. Подключите Railway к репозиторию
4. Деплой автоматический!

### **VPS (Ubuntu):**

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Запустите через systemd
sudo nano /etc/systemd/system/hh-api.service

[Unit]
Description=HH Parser API
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# 3. Запустите сервис
sudo systemctl start hh-api
sudo systemctl enable hh-api
```

---

## 🔐 БЕЗОПАСНОСТЬ

### **Добавить API ключ (опционально):**

```python
# В api.py добавьте:
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Добавьте в эндпоинты:
@app.post("/api/search")
async def search_vacancies(
    request: VacancySearchRequest,
    api_key: str = Security(verify_api_key)  # ← Защита
):
    ...
```

---

## 📊 МОНИТОРИНГ

### **Проверка статуса:**
```bash
curl http://localhost:8000/health
```

### **Логирование:**
```python
# Добавьте в api.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/search")
async def search_vacancies(request: VacancySearchRequest):
    logger.info(f"Search request: {request.keywords}")
    ...
```

---

## 🎯 ИТОГО

**Что вы получили:**
- ✅ REST API для парсера HH.ru
- ✅ Автоматическая документация (Swagger)
- ✅ Готово для интеграции с GPT
- ✅ Готово для n8n
- ✅ Готово для деплоя

**Использование:**
1. Запустите: `python api.py`
2. Откройте: http://localhost:8000/docs
3. Тестируйте прямо в браузере!
4. Интегрируйте куда угодно! 🚀

