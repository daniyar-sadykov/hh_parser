# ⚡ БЫСТРЫЙ СТАРТ: API + GPT

## 🚀 ЗА 5 МИНУТ

### 1️⃣ Установка (30 сек)
```bash
pip install -r requirements.txt
```

### 2️⃣ Запуск API (10 сек)
```bash
python api.py
```

API запущен на: http://localhost:8000

### 3️⃣ Проверка (10 сек)
Откройте в браузере: http://localhost:8000/docs

---

## 🎯 САМЫЙ ПРОСТОЙ ПРИМЕР

### Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/search-quick",
    params={
        "keywords": "оператор CRM",
        "max_results": 50
    }
)

data = response.json()
print(f"Найдено: {data['count']} вакансий")

for v in data['vacancies'][:5]:
    print(f"\n{v['название']}")
    print(f"💰 {v['оплата']}")
    print(f"🔗 {v['ссылка']}")
```

### curl:
```bash
curl -X POST "http://localhost:8000/api/search-quick?keywords=оператор&max_results=50"
```

---

## 🤖 С GPT (ChatGPT API)

```python
import requests
import openai

# 1. Получаем вакансии
response = requests.post(
    "http://localhost:8000/api/search-quick",
    params={"keywords": "менеджер CRM", "max_results": 10}
)
vacancies = response.json()['vacancies']

# 2. GPT анализирует
client = openai.OpenAI(api_key="your-key")
completion = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": f"Выбери топ-3 из этих вакансий: {vacancies}"
    }]
)

print(completion.choices[0].message.content)
```

---

## 🔄 С N8N

1. **HTTP Request узел:**
   - Method: `POST`
   - URL: `http://your-server:8000/api/search-quick`
   - Query Parameters:
     - `keywords`: `{{ $json.keywords }}`
     - `max_results`: `100`

2. **Результат:**
   - `{{ $json.count }}` - количество
   - `{{ $json.vacancies }}` - массив вакансий

---

## 📊 ЭНДПОИНТЫ

### Быстрый поиск (рекомендуется):
```
POST /api/search-quick?keywords=оператор&max_results=100
```

### Полный поиск:
```
POST /api/search
Body: {
  "keywords": "оператор CRM",
  "region": 1,
  "min_salary": 50000,
  "only_with_salary": true,
  "period": 7,
  "max_results": 500
}
```

### Одна вакансия:
```
GET /api/vacancy/123456
```

### Список регионов:
```
GET /api/regions
```

---

## 🌐 ДЕПЛОЙ

### Railway.app (самый простой):
1. Push код в GitHub
2. Подключите Railway к репозиторию
3. Готово! URL: `https://your-app.railway.app`

### VPS:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

---

## 📚 ПОЛНАЯ ДОКУМЕНТАЦИЯ

- **API документация:** `API_ИНСТРУКЦИЯ.md`
- **Примеры с GPT:** `GPT_ПРИМЕРЫ.py`
- **Парсер:** `ИНСТРУКЦИЯ_ПАРСЕР.md`

---

## ✅ ГОТОВО!

Теперь у вас есть:
- ✅ REST API для парсера
- ✅ Готовые примеры с GPT
- ✅ Документация Swagger
- ✅ Готово к деплою

**Следующий шаг:** Запустите `python GPT_ПРИМЕРЫ.py` чтобы увидеть все возможности! 🚀

