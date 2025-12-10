# 🔌 N8N ИНТЕГРАЦИЯ: Как использовать новый параметр limit

## 🎯 БЫСТРЫЙ СТАРТ

### **Что изменилось:**
- Backend ищет **ВСЕ** вакансии
- Возвращает только **N самых свежих** (параметр `limit`)
- N8N просто указывает нужное количество

---

## 📋 ПРИМЕР 1: HTTP Request Node

### **Настройка узла:**

```
Тип: HTTP Request
Метод: POST
URL: https://your-api.com/api/search
Authentication: None
```

### **Body (JSON):**

```json
{
  "keywords": "{{$json.query}}",
  "region": 1,
  "min_salary": 50000,
  "only_with_salary": true,
  "period": 7,
  "limit": 20,
  "max_results": 10000
}
```

### **Что получите:**

```json
{
  "success": true,
  "count": 20,
  "message": "Найдено 1247 вакансий, возвращено 20 самых свежих",
  "statistics": {
    "total_found": 1247,
    "returned_count": 20,
    ...
  },
  "vacancies": [20 самых свежих вакансий]
}
```

---

## 📋 ПРИМЕР 2: Динамический limit

### **Webhook принимает:**

```json
{
  "query": "оператор CRM",
  "how_many": 50
}
```

### **HTTP Request Body:**

```json
{
  "keywords": "{{$json.query}}",
  "region": 1,
  "limit": {{$json.how_many}},
  "min_salary": 50000,
  "only_with_salary": true,
  "period": 7
}
```

### **Результат:**
Backend найдёт ВСЕ, вернёт только 50 самых свежих.

---

## 📋 ПРИМЕР 3: Быстрый endpoint

### **URL (GET/POST):**

```
POST https://your-api.com/api/search-quick
```

### **Query Parameters или Body:**

```json
{
  "keywords": "оператор CRM",
  "region": 1,
  "limit": 20
}
```

### **Ответ:**

```json
{
  "success": true,
  "total_found": 1247,
  "returned_count": 20,
  "vacancies": [...]
}
```

---

## 🔄 ПОЛНЫЙ WORKFLOW N8N

```
┌─────────────────────┐
│ 1. Webhook          │
│    Получает запрос  │
│    от Telegram      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Set Node         │
│    Формирует        │
│    параметры:       │
│    - keywords       │
│    - limit          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. HTTP Request     │
│    POST /api/search │
│    Body: {...}      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Function Node    │
│    (опционально)    │
│    Обработка        │
│    вакансий         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Respond Webhook  │
│    Отправка боту    │
└─────────────────────┘
```

---

## 💡 ПОЛЕЗНЫЕ НАСТРОЙКИ

### **Для ежедневных рассылок:**
```json
{
  "period": 1,    // За последний день
  "limit": 20     // Топ-20 самых свежих
}
```

### **Для еженедельных отчётов:**
```json
{
  "period": 7,
  "limit": 50
}
```

### **Для срочного поиска:**
```json
{
  "period": 1,
  "limit": 5      // Только самые-самые свежие
}
```

---

## 🎯 ГЛАВНОЕ

### **Раньше:**
- Backend ограничивал результат
- Могли пропустить свежие вакансии

### **Сейчас:**
- Backend ищет **ВСЕ**
- Возвращает только **N самых свежих**
- Вы указываете `limit` - получаете ровно столько

---

## ✅ ГОТОВО!

Просто добавьте параметр `limit` в ваш HTTP Request, и всё заработает! 🚀

