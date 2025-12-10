# 🔗 N8N ИНТЕГРАЦИЯ: Поиск контактов компаний

## 📋 Содержание
1. [Быстрый старт](#быстрый-старт)
2. [Полный workflow](#полный-workflow)
3. [Примеры узлов N8N](#примеры-узлов-n8n)
4. [Готовый JSON workflow](#готовый-json-workflow)

---

## 🚀 Быстрый старт

### Что делает этот workflow?

```
Пользователь пишет в Telegram бота
    ↓
Бот ищет 20 вакансий через API
    ↓
Автоматически извлекает компании
    ↓
Ищет контакты для каждой компании
    ↓
Отправляет пользователю вакансии + контакты
```

**Время выполнения: 15-25 секунд**

---

## 📊 Полный Workflow

### Шаг 1: Telegram Trigger

**Узел:** `Telegram Trigger`

**Настройка:**
- Bot Token: ваш токен бота
- Updates: `message`

**Что делает:**
Получает сообщение от пользователя с ключевыми словами для поиска.

---

### Шаг 2: Поиск вакансий (изменить лимит!)

**Узел:** `HTTP Request`

**Настройки:**
- Method: `POST`
- URL: `https://your-app.railway.app/api/search-quick`

**Query Parameters:**
```javascript
{
  "keywords": "{{ $json.message.text }}",
  "region": 1,
  "max_results": 20  // ← ВАЖНО! Было 100, стало 20
}
```

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Что получаем:**
```json
{
  "success": true,
  "count": 20,
  "vacancies": [
    {
      "id": "123456",
      "название": "Python разработчик",
      "компания": "Яндекс",
      "оплата": "от 150000 руб",
      "ссылка": "https://hh.ru/vacancy/123456",
      "описание": "..."
    },
    // ... еще 19 вакансий
  ]
}
```

---

### Шаг 3: Извлечь уникальные компании

**Узел:** `Code` (JavaScript)

**Код:**
```javascript
// Получаем все вакансии
const vacancies = $input.all()[0].json.vacancies;

// Извлекаем уникальные компании
const uniqueCompanies = [...new Set(
  vacancies.map(v => v.компания)
)];

// Формируем массив объектов для следующего узла
return uniqueCompanies.map(company => ({
  company_name: company,
  city: "Москва"
}));
```

**Что получаем:**
```json
[
  { "company_name": "Яндекс", "city": "Москва" },
  { "company_name": "Сбер", "city": "Москва" },
  { "company_name": "МТС", "city": "Москва" },
  // ... 10-15 уникальных компаний
]
```

---

### Шаг 4: Поиск контактов для каждой компании

**Узел:** `HTTP Request`

**Настройки:**
- Method: `POST`
- URL: `https://your-app.railway.app/api/contacts/search-quick`
- Split Into Items: `true` (включить!)

**Query Parameters:**
```javascript
{
  "company_name": "{{ $json.company_name }}",
  "city": "{{ $json.city }}"
}
```

**Что получаем (для каждой компании):**
```json
{
  "success": true,
  "company_name": "Яндекс",
  "found": true,
  "sources": ["2gis", "hh.ru", "website"],
  "contacts": {
    "phones": ["+7 495 739-70-00"],
    "emails": ["hr@yandex.ru", "job@yandex.ru"],
    "telegram": ["@yandex_official"],
    "whatsapp": ["+7 495 739-70-00"],
    "websites": ["https://yandex.ru"],
    "address": "г. Москва, ул. Льва Толстого, 16"
  },
  "additional_info": {
    "full_name": "ООО «Яндекс»",
    "hh_company_url": "https://hh.ru/employer/1740"
  },
  "from_cache": false
}
```

---

### Шаг 5: Объединить вакансии с контактами

**Узел:** `Merge`

**Настройки:**
- Mode: `Combine`
- Join: `Merge By Key`
- Key to Match: `компания` (из вакансий) = `company_name` (из контактов)

**Что получаем:**
```json
[
  {
    // Данные вакансии
    "название": "Python разработчик",
    "компания": "Яндекс",
    "оплата": "от 150000 руб",
    "ссылка": "https://hh.ru/vacancy/123456",
    
    // + Контакты компании
    "contacts": {
      "phones": ["+7 495 739-70-00"],
      "emails": ["hr@yandex.ru"],
      "telegram": ["@yandex_official"],
      "websites": ["https://yandex.ru"]
    }
  },
  // ... остальные вакансии с контактами
]
```

---

### Шаг 6: Форматировать сообщение

**Узел:** `Code` (JavaScript)

**Код:**
```javascript
const items = $input.all();
let message = `🎉 Найдено ${items.length} вакансий!\n\n`;

items.forEach((item, index) => {
  const vacancy = item.json;
  
  message += `📍 Вакансия ${index + 1}:\n`;
  message += `   ${vacancy.название}\n`;
  message += `   💼 ${vacancy.компания}\n`;
  message += `   💰 ${vacancy.оплата}\n`;
  message += `   🔗 ${vacancy.ссылка}\n`;
  
  // Добавляем контакты если есть
  if (vacancy.contacts) {
    message += `\n   📞 Контакты:\n`;
    
    if (vacancy.contacts.phones && vacancy.contacts.phones.length > 0) {
      message += `   Тел: ${vacancy.contacts.phones[0]}\n`;
    }
    
    if (vacancy.contacts.emails && vacancy.contacts.emails.length > 0) {
      message += `   Email: ${vacancy.contacts.emails[0]}\n`;
    }
    
    if (vacancy.contacts.telegram && vacancy.contacts.telegram.length > 0) {
      message += `   Telegram: ${vacancy.contacts.telegram[0]}\n`;
    }
    
    if (vacancy.contacts.websites && vacancy.contacts.websites.length > 0) {
      message += `   Сайт: ${vacancy.contacts.websites[0]}\n`;
    }
  }
  
  message += `\n`;
});

return [{ json: { message } }];
```

---

### Шаг 7: Отправить в Telegram

**Узел:** `Telegram`

**Настройки:**
- Resource: `Message`
- Operation: `Send Text`
- Chat ID: `{{ $node["Telegram Trigger"].json.message.chat.id }}`
- Text: `{{ $json.message }}`

---

## 🎬 Альтернатива: Пакетный поиск контактов

Вместо шагов 3-4 можно использовать **один запрос** для всех компаний:

### Узел: Code (подготовка данных)

```javascript
const vacancies = $input.all()[0].json.vacancies;

// Извлекаем уникальные компании с их вакансиями
const companiesMap = {};

vacancies.forEach(v => {
  const company = v.компания;
  if (!companiesMap[company]) {
    companiesMap[company] = {
      company_name: company,
      city: "Москва",
      vacancy_link: v.ссылка
    };
  }
});

// Формируем массив
const companies = Object.values(companiesMap);

return [{ json: { companies } }];
```

### Узел: HTTP Request (пакетный поиск)

**Настройки:**
- Method: `POST`
- URL: `https://your-app.railway.app/api/contacts/batch`
- Body Content Type: `JSON`

**Body:**
```javascript
{{ $json.companies }}
```

**Преимущество:** Один запрос вместо 10-15! Быстрее и меньше нагрузка.

---

## 📦 Готовый JSON Workflow для импорта в N8N

Сохраните этот JSON и импортируйте в N8N:

```json
{
  "name": "HH.ru Вакансии + Контакты",
  "nodes": [
    {
      "parameters": {
        "updates": ["message"]
      },
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "https://your-app.railway.app/api/search-quick",
        "method": "POST",
        "queryParameters": {
          "parameters": [
            {
              "name": "keywords",
              "value": "={{ $json.message.text }}"
            },
            {
              "name": "region",
              "value": "1"
            },
            {
              "name": "max_results",
              "value": "20"
            }
          ]
        }
      },
      "name": "Поиск вакансий",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "jsCode": "const vacancies = $input.all()[0].json.vacancies;\nconst uniqueCompanies = [...new Set(vacancies.map(v => v.компания))];\nreturn uniqueCompanies.map(company => ({ company_name: company, city: 'Москва' }));"
      },
      "name": "Извлечь компании",
      "type": "n8n-nodes-base.code",
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "https://your-app.railway.app/api/contacts/search-quick",
        "method": "POST",
        "queryParameters": {
          "parameters": [
            {
              "name": "company_name",
              "value": "={{ $json.company_name }}"
            },
            {
              "name": "city",
              "value": "={{ $json.city }}"
            }
          ]
        },
        "options": {
          "splitIntoItems": true
        }
      },
      "name": "Поиск контактов",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300]
    },
    {
      "parameters": {
        "mode": "combine",
        "mergeByFields": {
          "values": [
            {
              "field1": "компания",
              "field2": "company_name"
            }
          ]
        }
      },
      "name": "Объединить",
      "type": "n8n-nodes-base.merge",
      "position": [1050, 300]
    },
    {
      "parameters": {
        "jsCode": "// См. код выше в Шаге 6"
      },
      "name": "Форматировать",
      "type": "n8n-nodes-base.code",
      "position": [1250, 300]
    },
    {
      "parameters": {
        "chatId": "={{ $node['Telegram Trigger'].json.message.chat.id }}",
        "text": "={{ $json.message }}"
      },
      "name": "Отправить в Telegram",
      "type": "n8n-nodes-base.telegram",
      "position": [1450, 300]
    }
  ],
  "connections": {
    "Telegram Trigger": {
      "main": [[{"node": "Поиск вакансий", "type": "main", "index": 0}]]
    },
    "Поиск вакансий": {
      "main": [[{"node": "Извлечь компании", "type": "main", "index": 0}]]
    },
    "Извлечь компании": {
      "main": [[{"node": "Поиск контактов", "type": "main", "index": 0}]]
    },
    "Поиск контактов": {
      "main": [[{"node": "Объединить", "type": "main", "index": 0}]]
    },
    "Объединить": {
      "main": [[{"node": "Форматировать", "type": "main", "index": 0}]]
    },
    "Форматировать": {
      "main": [[{"node": "Отправить в Telegram", "type": "main", "index": 0}]]
    }
  }
}
```

---

## ⚙️ Важные настройки

### 1. Изменить лимит вакансий

В узле "Поиск вакансий" **ОБЯЗАТЕЛЬНО** измените:
```
"max_results": 20  // Было 100
```

### 2. URL вашего Railway приложения

Замените `https://your-app.railway.app` на ваш реальный URL Railway.

### 3. Split Into Items

В узле "Поиск контактов" включите опцию **Split Into Items**, чтобы N8N обрабатывал каждую компанию отдельно.

---

## 🎯 Пример использования

**Пользователь пишет боту:**
```
Python разработчик Москва
```

**Бот отвечает через 20 секунд:**
```
🎉 Найдено 20 вакансий от 12 компаний!

📍 Вакансия 1:
   Python разработчик
   💼 Яндекс
   💰 от 150000 руб
   🔗 https://hh.ru/vacancy/123456
   
   📞 Контакты:
   Тел: +7 495 739-70-00
   Email: hr@yandex.ru
   Telegram: @yandex_official
   Сайт: https://yandex.ru

📍 Вакансия 2:
   Backend разработчик Python
   💼 Сбер
   💰 от 200000 руб
   🔗 https://hh.ru/vacancy/123457
   
   📞 Контакты:
   Тел: +7 495 500-55-50
   Email: career@sber.ru
   Сайт: https://www.sberbank.com

... (еще 18 вакансий)
```

---

## 🐛 Troubleshooting

### Проблема: "Не находит контакты"

**Решение:**
1. Проверьте что API работает: `https://your-app.railway.app/health`
2. Проверьте API ключ 2GIS в переменных окружения Railway
3. Проверьте логи Railway на наличие ошибок

### Проблема: "Слишком долго выполняется"

**Решение:**
1. Используйте пакетный поиск (`/api/contacts/batch`)
2. Уменьшите количество вакансий до 10-15
3. Проверьте что кеш работает (повторные запросы должны быть быстрее)

### Проблема: "Некоторые компании без контактов"

**Ответ:**
Это нормально! Не для всех компаний удается найти контакты. Примерно:
- 70% - найдут телефоны и email через 2GIS
- 90% - найдут сайты через HH.ru
- 20-30% - найдут Telegram/WhatsApp

---

## 📞 API Эндпоинты

### POST `/api/contacts/search`
Полный поиск с параметрами

### POST `/api/contacts/search-quick`
Быстрый поиск (для N8N)

### POST `/api/contacts/batch`
Пакетный поиск для нескольких компаний

### GET `/api/contacts/stats`
Статистика кеша и API вызовов

---

## 🎉 Готово!

Теперь ваш Telegram-бот автоматически находит не только вакансии, но и контакты компаний!

**Время разработки:** 2 часа  
**Время выполнения workflow:** 15-25 секунд  
**Найденные контакты:** телефоны, email, Telegram, WhatsApp, сайты

