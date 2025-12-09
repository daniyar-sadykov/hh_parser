"""
Скрипт для обработки отфильтрованных вакансий через GPT API
С защитой от шаблонных ответов и валидацией качества
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
import openai
from openai import OpenAI

# ============================================
# КОНФИГУРАЦИЯ
# ============================================

# API настройки
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Установите через переменную окружения
MODEL = "gpt-4o"  # или "gpt-4o-mini" для экономии
BATCH_SIZE = 15  # Обрабатываем по 15 вакансий за раз (оптимально для качества)

# Параметры генерации (КРИТИЧНО для качества!)
TEMPERATURE = 0.7  # Не 0! Нужна вариативность
MAX_TOKENS = 6000  # Достаточно для 15 вакансий с детальным анализом
PRESENCE_PENALTY = 0.3  # Против повторений
FREQUENCY_PENALTY = 0.3  # Против шаблонных фраз

# Параметры повторных попыток
MAX_RETRIES = 3
RETRY_DELAY = 2  # секунд

# Пути
FILTERED_BATCHES_DIR = Path("filtered_batches")
RESULTS_DIR = Path("ranked_results")
PROMPT_FILE = Path("vacancy_ranking_prompt.txt")
PROGRESS_FILE = RESULTS_DIR / "progress.json"

# ============================================
# ВАЛИДАЦИЯ КАЧЕСТВА ОТВЕТОВ
# ============================================

def is_template_response(result: Dict[str, Any]) -> tuple[bool, str]:
    """
    Проверяет, является ли ответ шаблонным
    
    Returns:
        (is_template, reason)
    """
    reasoning = result.get("reasoning", "").lower()
    
    # Запрещенные шаблонные фразы
    TEMPLATE_PHRASES = [
        "автоматическая оценка на основе",
        "ключевых индикаторов в описании",
        "общая оценка",
        "стандартный анализ",
        "базовая оценка",
    ]
    
    for phrase in TEMPLATE_PHRASES:
        if phrase in reasoning:
            return True, f"Найдена шаблонная фраза: '{phrase}'"
    
    # Слишком короткое обоснование
    if len(reasoning) < 100:
        return True, f"Слишком короткое обоснование: {len(reasoning)} символов"
    
    # Проверка automation_opportunities
    auto_ops = result.get("automation_opportunities", [])
    if len(auto_ops) < 2:
        return True, "Слишком мало возможностей автоматизации"
    
    # Проверка на одинаковые automation_opportunities
    generic_ops = [
        "автоответ на заявки",
        "базовая автоматизация crm",
        "мониторинг обращений",
    ]
    
    if all(op.lower() in generic_ops for op in auto_ops):
        return True, "Все возможности автоматизации - шаблонные"
    
    return False, ""


def validate_batch_results(results: List[Dict], vacancies: List[Dict]) -> tuple[bool, List[str]]:
    """
    Валидирует качество результатов для батча
    
    Returns:
        (is_valid, issues)
    """
    issues = []
    
    # Проверка количества
    if len(results) != len(vacancies):
        issues.append(f"Количество результатов ({len(results)}) != количеству вакансий ({len(vacancies)})")
        return False, issues
    
    # Проверка каждого результата
    template_count = 0
    for i, result in enumerate(results):
        vacancy_id = result.get("vacancy_id")
        
        # Проверка наличия vacancy_id
        if not vacancy_id:
            issues.append(f"Результат #{i}: отсутствует vacancy_id")
            continue
        
        # Проверка на шаблонность
        is_template, reason = is_template_response(result)
        if is_template:
            template_count += 1
            if template_count <= 3:  # Показываем первые 3
                issues.append(f"Вакансия {vacancy_id}: шаблонный ответ - {reason}")
    
    # Если больше 30% шаблонных - отклоняем весь батч
    template_percentage = (template_count / len(results)) * 100
    if template_percentage > 30:
        issues.append(f"Слишком много шаблонных ответов: {template_percentage:.1f}% ({template_count}/{len(results)})")
        return False, issues
    
    return True, issues


# ============================================
# РАБОТА С GPT API
# ============================================

def load_prompt() -> str:
    """Загружает промпт из файла"""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def prepare_batch_for_api(vacancies: List[Dict]) -> List[Dict]:
    """Подготавливает батч вакансий для API (убирает служебные поля)"""
    clean_vacancies = []
    for v in vacancies:
        clean_v = {k: v for k, v in v.items() if not k.startswith('_')}
        clean_vacancies.append(clean_v)
    return clean_vacancies


def call_gpt_api(client: OpenAI, prompt: str, vacancies: List[Dict], attempt: int = 1) -> tuple[List[Dict] | None, str]:
    """
    Вызывает GPT API для ранжирования вакансий
    
    Returns:
        (results, error_message)
    """
    try:
        # Формируем сообщения
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": json.dumps(vacancies, ensure_ascii=False, indent=2)
            }
        ]
        
        # Добавляем дополнительное напоминание при повторной попытке
        if attempt > 1:
            messages.append({
                "role": "system",
                "content": "⚠️ ВНИМАНИЕ: Предыдущий ответ был отклонен из-за шаблонных фраз. "
                          "Ты ОБЯЗАН написать УНИКАЛЬНЫЙ анализ для КАЖДОЙ вакансии, "
                          "основываясь на РЕАЛЬНЫХ деталях из описания. "
                          "НИКАКИХ общих фраз типа 'автоматическая оценка на основе ключевых индикаторов'!"
            })
        
        # Вызов API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            presence_penalty=PRESENCE_PENALTY,
            frequency_penalty=FREQUENCY_PENALTY,
            response_format={"type": "json_object"} if MODEL.startswith("gpt-4") else None
        )
        
        # Парсинг ответа
        content = response.choices[0].message.content
        
        # Пробуем извлечь JSON
        try:
            # Если ответ - это объект с массивом
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "results" in parsed:
                results = parsed["results"]
            elif isinstance(parsed, dict) and "rankings" in parsed:
                results = parsed["rankings"]
            elif isinstance(parsed, list):
                results = parsed
            else:
                # Ищем первый ключ, который содержит массив
                for key, value in parsed.items():
                    if isinstance(value, list):
                        results = value
                        break
                else:
                    return None, f"Не найден массив результатов в ответе: {list(parsed.keys())}"
            
            return results, ""
            
        except json.JSONDecodeError as e:
            return None, f"Ошибка парсинга JSON: {e}\n\nОтвет:\n{content[:500]}"
    
    except Exception as e:
        return None, f"Ошибка API: {str(e)}"


def process_batch(client: OpenAI, prompt: str, vacancies: List[Dict], batch_name: str) -> tuple[List[Dict] | None, str]:
    """
    Обрабатывает один батч с повторными попытками и валидацией
    
    Returns:
        (results, error_message)
    """
    clean_vacancies = prepare_batch_for_api(vacancies)
    
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"    Попытка {attempt}/{MAX_RETRIES}...", end=" ")
        
        # Вызов API
        results, error = call_gpt_api(client, prompt, clean_vacancies, attempt)
        
        if error:
            print(f"❌ Ошибка: {error}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return None, error
        
        # Валидация результатов
        is_valid, issues = validate_batch_results(results, vacancies)
        
        if is_valid:
            if issues:
                print(f"⚠️  OK (с замечаниями: {len(issues)})")
                for issue in issues[:3]:
                    print(f"        - {issue}")
            else:
                print("✓ OK")
            return results, ""
        else:
            print(f"❌ Невалидный результат:")
            for issue in issues[:5]:
                print(f"        - {issue}")
            
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            
            return None, f"Не удалось получить валидный результат после {MAX_RETRIES} попыток"
    
    return None, "Неожиданная ошибка"


# ============================================
# УПРАВЛЕНИЕ ПРОГРЕССОМ
# ============================================

def load_progress() -> Dict:
    """Загружает прогресс обработки"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "processed_batches": [],
        "failed_batches": [],
        "total_processed": 0,
        "total_failed": 0,
        "started_at": None,
        "last_update": None,
    }


def save_progress(progress: Dict):
    """Сохраняет прогресс обработки"""
    progress["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ============================================
# ОСНОВНОЙ ПРОЦЕСС
# ============================================

def process_all_batches():
    """Обрабатывает все отфильтрованные батчи"""
    
    # Проверка API ключа
    if not OPENAI_API_KEY:
        print("❌ Ошибка: не установлен OPENAI_API_KEY")
        print("Установите через: $env:OPENAI_API_KEY='your-key-here'")
        return
    
    # Инициализация
    client = OpenAI(api_key=OPENAI_API_KEY)
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Загрузка промпта
    print("Загрузка промпта...")
    prompt = load_prompt()
    print(f"✓ Промпт загружен ({len(prompt)} символов)")
    
    # Загрузка прогресса
    progress = load_progress()
    if not progress["started_at"]:
        progress["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Поиск батчей
    batch_files = sorted(FILTERED_BATCHES_DIR.glob("filtered_batch_*.json"))
    print(f"\nНайдено {len(batch_files)} отфильтрованных батчей")
    print(f"Уже обработано: {len(progress['processed_batches'])}")
    print(f"Провалено: {len(progress['failed_batches'])}\n")
    
    # Обработка батчей
    for batch_file in batch_files:
        batch_name = batch_file.stem.replace("filtered_", "")
        
        # Пропускаем уже обработанные
        if batch_name in progress["processed_batches"]:
            continue
        
        print(f"Обработка {batch_name}...")
        
        # Загрузка вакансий
        with open(batch_file, 'r', encoding='utf-8') as f:
            vacancies = json.load(f)
        
        if not vacancies:
            print(f"  ⚠️ Пустой батч, пропускаем")
            progress["processed_batches"].append(batch_name)
            continue
        
        print(f"  Вакансий: {len(vacancies)}")
        
        # Разбиваем на под-батчи если нужно
        sub_batches = [vacancies[i:i + BATCH_SIZE] for i in range(0, len(vacancies), BATCH_SIZE)]
        all_results = []
        
        for sub_idx, sub_batch in enumerate(sub_batches, 1):
            if len(sub_batches) > 1:
                print(f"  Под-батч {sub_idx}/{len(sub_batches)} ({len(sub_batch)} вакансий):")
            
            results, error = process_batch(client, prompt, sub_batch, batch_name)
            
            if error:
                print(f"  ❌ Провален: {error}")
                progress["failed_batches"].append({
                    "batch": batch_name,
                    "error": error,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                progress["total_failed"] += len(sub_batch)
                break
            
            all_results.extend(results)
        else:
            # Все под-батчи успешны
            # Сохраняем результаты
            result_file = RESULTS_DIR / f"ranked_{batch_name}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            
            progress["processed_batches"].append(batch_name)
            progress["total_processed"] += len(vacancies)
            print(f"  ✓ Сохранено в {result_file.name}")
        
        # Сохраняем прогресс
        save_progress(progress)
        
        # Небольшая пауза между батчами
        time.sleep(1)
    
    # Финальная статистика
    print(f"\n{'='*60}")
    print(f"ОБРАБОТКА ЗАВЕРШЕНА")
    print(f"{'='*60}")
    print(f"Успешно обработано: {progress['total_processed']} вакансий")
    print(f"Провалено:          {progress['total_failed']} вакансий")
    print(f"Батчей обработано:  {len(progress['processed_batches'])}/{len(batch_files)}")
    print(f"Результаты в:       {RESULTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        process_all_batches()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем. Прогресс сохранен.")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        raise

