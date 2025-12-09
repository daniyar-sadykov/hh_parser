"""
Скрипт для фильтрации и ранжирования вакансий
Отсеивает явных продажников и обрабатывает остальные через GPT
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

# ============================================
# КОНФИГУРАЦИЯ ФИЛЬТРАЦИИ
# ============================================

# Паттерны для ИСКЛЮЧЕНИЯ вакансий (явные продажники с низким потенциалом)
SALES_EXCLUDE_PATTERNS = {
    'название': [
        r'\bменеджер.*продаж',
        r'\bменеджер.*по.*продаж',
        r'\bагент.*недвижимост',
        r'\bриелтор',
        r'\bброкер',
        r'\bторговый.*представител',
        r'\bпродавец.*консультант',
        r'\bспециалист.*продаж',
        r'\bкоммерческий.*директор',
        r'\bтехнический.*менеджер.*продаж',  # иногда это тоже просто продажники
    ],
    'описание': [
        # Явные маркеры продажников
        r'холодн(ые|ых)\s+звонк',
        r'активны(е|х)\s+продаж',
        r'поиск.*клиент.*\s+продаж',
        r'привлечени(е|я)\s+клиент',
        r'встреч(и|ами).*с.*клиент.*личн',
        r'презентац(ии|ия).*продукт.*клиент',
        r'развитие.*клиентск(ой|ого)\s+баз',
        r'расширение.*клиентск(ой|ого)\s+баз',
    ]
}

# Паттерны для СНИЖЕНИЯ оценки (менее явные продажники)
SALES_REDUCE_PATTERNS = {
    'описание': [
        r'ведение.*переговор',
        r'заключение.*сделок',
        r'выполнение.*плана.*продаж',
        r'отдел.*продаж',
        r'воронк(а|и).*продаж',
        r'конверси(я|и).*лид',
    ]
}

# Паттерны ВЫСОКОГО потенциала (приоритет при пограничных случаях)
HIGH_POTENTIAL_PATTERNS = {
    'описание': [
        r'\b1[сС]\b',
        r'\bbitrix24\b',
        r'\bамо\s*crm\b',
        r'\bcrm[\s-]систем',
        r'excel.*больш.*объем',
        r'обработк(а|и).*\d+.*заявок',
        r'формирование.*счет',
        r'формирование.*договор',
        r'формирование.*документ',
        r'выгрузк(а|и).*отчет',
        r'сверк(а|и).*данн',
        r'учет.*склад',
        r'работа.*с.*базами.*данн',
        r'ввод.*данн.*систем',
        r'заполнение.*форм',
        r'рутинн',
        r'повторяющ',
        r'ежедневн.*\d+',
        r'автоматизац',
        r'\bapi\b',
        r'интеграци',
        r'\bweb[\s-]сервис',
    ]
}


def check_patterns(text: str, patterns: List[str]) -> bool:
    """Проверяет, совпадает ли текст с хотя бы одним паттерном"""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def should_exclude_vacancy(vacancy: Dict[str, Any]) -> tuple[bool, str]:
    """
    Определяет, нужно ли полностью исключить вакансию
    
    Returns:
        (should_exclude, reason)
    """
    название = vacancy.get('название', '')
    описание = vacancy.get('описание', '')
    
    # Проверка по названию
    if check_patterns(название, SALES_EXCLUDE_PATTERNS['название']):
        return True, f"Исключено по названию: '{название[:100]}...'"
    
    # Проверка по описанию (более строгая)
    desc_matches = sum(
        1 for pattern in SALES_EXCLUDE_PATTERNS['описание']
        if re.search(pattern, описание.lower(), re.IGNORECASE)
    )
    
    # Если 2+ маркера продажника в описании - исключаем
    if desc_matches >= 2:
        return True, f"Исключено: {desc_matches} маркеров продаж в описании"
    
    return False, ""


def calculate_pre_score(vacancy: Dict[str, Any]) -> int:
    """
    Рассчитывает предварительную оценку потенциала (0-10)
    Помогает определить приоритет обработки
    """
    описание = vacancy.get('описание', '')
    score = 5  # базовая оценка
    
    # Снижаем за признаки продажника
    reduce_matches = check_patterns(описание, SALES_REDUCE_PATTERNS['описание'])
    if reduce_matches:
        score -= 2
    
    # Повышаем за признаки высокого потенциала
    high_potential_matches = sum(
        1 for pattern in HIGH_POTENTIAL_PATTERNS['описание']
        if re.search(pattern, описание.lower(), re.IGNORECASE)
    )
    
    if high_potential_matches >= 5:
        score += 3
    elif high_potential_matches >= 3:
        score += 2
    elif high_potential_matches >= 1:
        score += 1
    
    return max(0, min(10, score))


def filter_batch(batch_file: Path) -> tuple[List[Dict], List[Dict], Dict]:
    """
    Фильтрует батч вакансий
    
    Returns:
        (to_process, excluded, stats)
    """
    with open(batch_file, 'r', encoding='utf-8') as f:
        vacancies = json.load(f)
    
    to_process = []
    excluded = []
    stats = {
        'total': len(vacancies),
        'excluded': 0,
        'to_process': 0,
        'high_priority': 0,
        'medium_priority': 0,
        'low_priority': 0,
    }
    
    for vacancy in vacancies:
        should_exclude, reason = should_exclude_vacancy(vacancy)
        
        if should_exclude:
            excluded.append({
                'vacancy': vacancy,
                'reason': reason,
                'auto_score': 0,
                'auto_category': 'Низкий потенциал (автофильтр)',
            })
            stats['excluded'] += 1
        else:
            pre_score = calculate_pre_score(vacancy)
            vacancy['_pre_score'] = pre_score
            to_process.append(vacancy)
            stats['to_process'] += 1
            
            if pre_score >= 7:
                stats['high_priority'] += 1
            elif pre_score >= 4:
                stats['medium_priority'] += 1
            else:
                stats['low_priority'] += 1
    
    return to_process, excluded, stats


def process_all_batches(batches_dir: Path, output_dir: Path):
    """Обрабатывает все батчи и создает отфильтрованные версии"""
    
    batches_dir = Path(batches_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    all_stats = {
        'total_batches': 0,
        'total_vacancies': 0,
        'total_excluded': 0,
        'total_to_process': 0,
        'total_high_priority': 0,
        'total_medium_priority': 0,
        'total_low_priority': 0,
    }
    
    batch_files = sorted(batches_dir.glob('batch_*.json'))
    
    print(f"Найдено {len(batch_files)} батчей\n")
    
    for batch_file in batch_files:
        print(f"Обработка {batch_file.name}...", end=' ')
        
        to_process, excluded, stats = filter_batch(batch_file)
        
        # Сохраняем отфильтрованный батч
        filtered_file = output_dir / f"filtered_{batch_file.name}"
        with open(filtered_file, 'w', encoding='utf-8') as f:
            json.dump(to_process, f, ensure_ascii=False, indent=2)
        
        # Сохраняем исключенные
        excluded_file = output_dir / f"excluded_{batch_file.name}"
        with open(excluded_file, 'w', encoding='utf-8') as f:
            json.dump(excluded, f, ensure_ascii=False, indent=2)
        
        # Обновляем общую статистику
        all_stats['total_batches'] += 1
        all_stats['total_vacancies'] += stats['total']
        all_stats['total_excluded'] += stats['excluded']
        all_stats['total_to_process'] += stats['to_process']
        all_stats['total_high_priority'] += stats['high_priority']
        all_stats['total_medium_priority'] += stats['medium_priority']
        all_stats['total_low_priority'] += stats['low_priority']
        
        print(f"✓ Обработано: {stats['to_process']}, Исключено: {stats['excluded']}")
    
    # Сохраняем общую статистику
    stats_file = output_dir / "filtering_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"ИТОГОВАЯ СТАТИСТИКА:")
    print(f"{'='*60}")
    print(f"Всего батчей:           {all_stats['total_batches']}")
    print(f"Всего вакансий:         {all_stats['total_vacancies']}")
    print(f"Исключено (продажники): {all_stats['total_excluded']} ({all_stats['total_excluded']/all_stats['total_vacancies']*100:.1f}%)")
    print(f"К обработке GPT:        {all_stats['total_to_process']} ({all_stats['total_to_process']/all_stats['total_vacancies']*100:.1f}%)")
    print(f"  - Высокий приоритет:  {all_stats['total_high_priority']}")
    print(f"  - Средний приоритет:  {all_stats['total_medium_priority']}")
    print(f"  - Низкий приоритет:   {all_stats['total_low_priority']}")
    print(f"{'='*60}")
    print(f"\nОтфильтрованные батчи сохранены в: {output_dir}")
    print(f"Экономия на API: ~{all_stats['total_excluded'] * 0.01:.2f}$ (если $0.01 за вакансию)")


if __name__ == "__main__":
    # Настройка путей
    batches_dir = Path("vacancy_batches")
    output_dir = Path("filtered_batches")
    
    # Запускаем фильтрацию
    process_all_batches(batches_dir, output_dir)

