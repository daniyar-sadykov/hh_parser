# 🔄 N8N WORKFLOW - Telegram бот для поиска вакансий

## СХЕМА WORKFLOW:

```
┌─────────────────────┐
│ Telegram Trigger    │ ← Пользователь отправляет сообщение
└──────────┬──────────┘
           │
           ↓
┌──────────┴──────────┐
│ OpenAI Chat         │ ← AI-агент (System Message)
│ (с Function Call)   │
└──────────┬──────────┘
           │
           ↓
┌──────────┴──────────┐
│ HTTP Request        │ ← Вызывается агентом
│ (Railway API)       │
└──────────┬──────────┘
           │
           ↓
┌──────────┴──────────┐
│ OpenAI Chat         │ ← Форматирует ответ
│ (Анализ)            │
└──────────┬──────────┘
           │
           ↓
┌──────────┴──────────┐
│ Telegram Send       │ ← Отправляет пользователю
└─────────────────────┘
```

---

## НАСТРОЙКА УЗЛОВ:

### 1️⃣ TELEGRAM TRIGGER

**Settings:**
- Event: Message received
- Download Images/Files: No

**Output:**
```json
{
  "message": {
    "text": "Обрабатываю заявки в CRM, от 60к",
    "chat": {
      "id": 123456789
    }
  }
}
```

---

### 2️⃣ OPENAI CHAT (Agent)

**Model:** gpt-4-turbo-preview или gpt-4

**System Message:** (Скопируйте из SYSTEM_PROMPT_КРАТКИЙ.md)

```
Ты — ассистент по поиску вакансий на HH.ru через API.

API: https://hhparser-production.up.railway.app/api/search (POST, JSON)

ТВОЯ ЗАДАЧА:
1. Прочитай запрос пользователя
2. Извлеки: навыки, зарплату, регион, требования
3. Сформируй JSON запрос к API
4. Проанализируй результаты
5. Выдай ТОП-5 лучших вакансий с обоснованием

ПАРАМЕТРЫ API:
{
  "keywords": "ключевые слова",
  "region": 1,
  "min_salary": 50000,
  "only_with_salary": true,
  "period": 7,
  "excluded_words": "недвижимость брокер",
  "sort_by": "publication_time",
  "max_results": 100
}

ПРАВИЛА:
- keywords: главные навыки + синонимы
- min_salary: если не указана → 40-80к по профессии
- only_with_salary: всегда true
- excluded_words: базовые + то что НЕ хочет пользователь

ФОРМАТ ОТВЕТА:
📊 Статистика
🎯 ТОП-5 с обоснованием
```

**User Message:**
```
{{ $json.message.text }}
```

**Options:**
- Enable Function Calling: ✅
- Temperature: 0.7
- Max Tokens: 4000

**Functions/Tools:**
```json
{
  "name": "search_vacancies",
  "description": "Поиск вакансий через HH.ru API",
  "parameters": {
    "type": "object",
    "properties": {
      "keywords": {
        "type": "string",
        "description": "Ключевые слова для поиска"
      },
      "region": {
        "type": "integer",
        "description": "ID региона (1=Москва, 2=СПб, 113=Россия)"
      },
      "min_salary": {
        "type": "integer",
        "description": "Минимальная зарплата"
      },
      "only_with_salary": {
        "type": "boolean",
        "description": "Только с указанной зарплатой"
      },
      "period": {
        "type": "integer",
        "description": "За последние N дней (1,3,7,30)"
      },
      "excluded_words": {
        "type": "string",
        "description": "Слова для исключения"
      },
      "sort_by": {
        "type": "string",
        "description": "Сортировка"
      },
      "max_results": {
        "type": "integer",
        "description": "Максимум результатов"
      }
    },
    "required": ["keywords"]
  }
}
```

---

### 3️⃣ HTTP REQUEST

**Method:** POST

**URL:**
```
https://hhparser-production.up.railway.app/api/search
```

**Authentication:** None

**Send Headers:** ✅

**Headers:**
```
Content-Type: application/json
```

**Send Body:** ✅

**Body Content Type:** JSON

**Body (JSON):**
```json
{
  "keywords": "{{ $json.keywords }}",
  "region": {{ $json.region }},
  "min_salary": {{ $json.min_salary }},
  "only_with_salary": {{ $json.only_with_salary }},
  "period": {{ $json.period }},
  "excluded_words": "{{ $json.excluded_words }}",
  "sort_by": "{{ $json.sort_by }}",
  "max_results": {{ $json.max_results }}
}
```

**Options:**
- Timeout: 120000 (2 минуты)
- Follow Redirects: ✅

---

### 4️⃣ OPENAI CHAT (Formatter)

**Model:** gpt-4-turbo-preview

**System Message:**
```
Ты получил результаты поиска вакансий через API.

Твоя задача:
1. Проанализировать data.vacancies
2. Выбрать ТОП-5 лучших вакансий
3. Для каждой написать почему она подходит
4. Отформатировать красиво для Telegram

Формат:
📊 **СТАТИСТИКА**
Найдено: {count} вакансий

🎯 **ТОП-5 ВАКАНСИЙ:**

**1. [Название]**
🏢 [Компания]
💰 [Зарплата]
📋 [Опыт]

**Почему подходит:**
[2-3 предложения обоснования]

🔗 [Ссылка]

---

[Повторить для 2-5]

💡 **Рекомендации:** [советы]
```

**User Message:**
```
Исходный запрос пользователя: {{ $('Telegram Trigger').item.json.message.text }}

Результаты API:
{{ JSON.stringify($json) }}

Проанализируй и выдай топ-5 вакансий с обоснованием для каждой.
```

**Options:**
- Temperature: 0.8
- Max Tokens: 3000

---

### 5️⃣ TELEGRAM SEND MESSAGE

**Chat ID:**
```
{{ $('Telegram Trigger').item.json.message.chat.id }}
```

**Text:**
```
{{ $json.choices[0].message.content }}
```

**Additional Fields:**
- Parse Mode: Markdown
- Disable Web Page Preview: ✅

---

## АЛЬТЕРНАТИВНЫЙ УПРОЩЕННЫЙ WORKFLOW:

Если OpenAI Function Calling не работает, используйте этот вариант:

```
[Telegram] → [Set] → [OpenAI] → [Code] → [HTTP] → [OpenAI] → [Telegram]
```

### CODE УЗЕЛ (вместо Function Calling):

```javascript
// Извлекаем параметры из ответа GPT
const gptResponse = items[0].json.choices[0].message.content;

// Парсим JSON из ответа GPT (если GPT вернул JSON)
const params = JSON.parse(gptResponse);

return [{
  json: {
    keywords: params.keywords || "оператор CRM",
    region: params.region || 1,
    min_salary: params.min_salary || 50000,
    only_with_salary: true,
    period: 7,
    excluded_words: params.excluded_words || "недвижимость брокер",
    sort_by: "publication_time",
    max_results: 100
  }
}];
```

---

## ТЕСТИРОВАНИЕ:

### Тестовые сообщения:

1. **Простой:**
   ```
   Обрабатываю заявки в CRM, хочу от 60к
   ```

2. **Детальный:**
   ```
   Я SMM-менеджер, работаю с таргетом и контентом.
   Нужна работа в Москве, зарплата от 80 тысяч.
   Без агентств и недвижимости.
   ```

3. **Минимальный:**
   ```
   Ищу работу оператором
   ```

---

## ВАЖНЫЕ НАСТРОЙКИ:

1. **Timeout в HTTP Request:**
   - Поставьте 120000 (2 минуты)
   - Парсинг может занимать время

2. **Error Handling:**
   - Добавьте узел "On Error" после HTTP Request
   - Отправьте пользователю: "Извините, произошла ошибка. Попробуйте другие параметры"

3. **Rate Limiting:**
   - Если много пользователей → добавьте очередь
   - Или лимит запросов (1 запрос в минуту на пользователя)

---

## ГОТОВЫЙ JSON WORKFLOW (ИМПОРТ В N8N):

Сохраните этот JSON и импортируйте в n8n:

```json
{
  "name": "Telegram Vacancy Search Bot",
  "nodes": [
    {
      "parameters": {},
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "model": "gpt-4-turbo-preview",
        "messages": {
          "messageValues": [
            {
              "role": "system",
              "content": "Ты — ассистент по поиску вакансий..."
            },
            {
              "role": "user",
              "content": "={{ $json.message.text }}"
            }
          ]
        }
      },
      "name": "OpenAI Agent",
      "type": "n8n-nodes-base.openAi",
      "typeVersion": 1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "url": "https://hhparser-production.up.railway.app/api/search",
        "method": "POST",
        "jsonParameters": true,
        "bodyParametersJson": "={{ JSON.stringify($json.function_call.arguments) }}"
      },
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "model": "gpt-4-turbo-preview",
        "messages": {
          "messageValues": [
            {
              "role": "user",
              "content": "Проанализируй результаты и выдай топ-5: {{ JSON.stringify($json) }}"
            }
          ]
        }
      },
      "name": "OpenAI Formatter",
      "type": "n8n-nodes-base.openAi",
      "typeVersion": 1,
      "position": [850, 300]
    },
    {
      "parameters": {
        "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
        "text": "={{ $json.choices[0].message.content }}"
      },
      "name": "Telegram Send",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1,
      "position": [1050, 300]
    }
  ]
}
```

---

Готово! Теперь у вас есть всё для создания Telegram бота! 🚀

