"""
КАЧЕСТВЕННОЕ УДАЛЕНИЕ ДУБЛИКАТОВ ПО КОМПАНИЯМ
Оставляет только 1 вакансию от каждой компании (лучшую)
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


class CompanyDeduplicator:
    """Удаление дубликатов вакансий от одной компании"""
    
    def __init__(self):
        self.stats = {
            'total_vacancies': 0,
            'unique_companies': 0,
            'duplicates_removed': 0,
            'kept_vacancies': 0
        }
        
        # Критерии выбора лучшей вакансии
        self.priority_keywords = [
            'входящие заявки',
            'обработка заявок',
            'crm',
            'битрикс',
            'amoCRM',
            'чат',
            'оператор',
            'менеджер по работе с клиентами',
            'support',
            'техподдержка',
            'колл-центр'
        ]
    
    def normalize_company_name(self, company: str) -> str:
        """
        Нормализация названия компании для корректного сравнения
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
    
    def calculate_vacancy_score(self, vacancy: Dict) -> int:
        """
        Рассчитывает оценку вакансии для выбора лучшей
        Чем выше оценка, тем лучше вакансия
        """
        score = 0
        
        title = vacancy.get('название', '').lower()
        description = vacancy.get('описание', '').lower()
        
        # Базовая оценка из pre_score если есть
        if '_pre_score' in vacancy:
            score += vacancy['_pre_score'] * 10
        else:
            score += 50  # базовая оценка
        
        # Бонусы за приоритетные ключевые слова в названии (больше вес)
        for keyword in self.priority_keywords:
            if keyword.lower() in title:
                score += 20
        
        # Бонусы за приоритетные ключевые слова в описании
        for keyword in self.priority_keywords:
            if keyword.lower() in description:
                score += 5
        
        # Бонус за наличие зарплаты
        salary = vacancy.get('оплата', '')
        if salary and salary != 'Не указана' and 'руб' in salary:
            score += 10
        
        # Бонус за длину описания (более подробные описания)
        desc_length = len(description)
        if desc_length > 1000:
            score += 10
        elif desc_length > 500:
            score += 5
        
        # Бонус за недавние вакансии
        date_pub = vacancy.get('дата_публикации', '')
        if '2025-12' in date_pub:  # Декабрь 2025
            score += 15
        elif '2025-11' in date_pub:  # Ноябрь 2025
            score += 10
        
        return score
    
    def select_best_vacancy(self, vacancies: List[Dict]) -> Dict:
        """
        Выбирает лучшую вакансию из списка дубликатов
        """
        if len(vacancies) == 1:
            return vacancies[0]
        
        # Оцениваем все вакансии
        scored_vacancies = [
            (vacancy, self.calculate_vacancy_score(vacancy))
            for vacancy in vacancies
        ]
        
        # Сортируем по оценке (по убыванию)
        scored_vacancies.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем лучшую
        best_vacancy = scored_vacancies[0][0]
        
        # Добавляем информацию о дубликатах
        best_vacancy['_duplicates_count'] = len(vacancies) - 1
        best_vacancy['_dedup_score'] = scored_vacancies[0][1]
        
        return best_vacancy
    
    def deduplicate_batch(self, vacancies: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Удаляет дубликаты в батче
        
        Returns:
            (kept_vacancies, removed_duplicates)
        """
        # Группируем по компаниям
        companies = defaultdict(list)
        
        for vacancy in vacancies:
            company = vacancy.get('компания', '')
            if not company:
                # Вакансии без компании оставляем как есть
                companies['_no_company_' + str(id(vacancy))].append(vacancy)
            else:
                normalized = self.normalize_company_name(company)
                companies[normalized].append(vacancy)
        
        kept = []
        removed = []
        
        for company_key, company_vacancies in companies.items():
            if len(company_vacancies) == 1:
                # Нет дубликатов
                kept.append(company_vacancies[0])
            else:
                # Есть дубликаты - выбираем лучшую
                best = self.select_best_vacancy(company_vacancies)
                kept.append(best)
                
                # Остальные помечаем как дубликаты
                for vac in company_vacancies:
                    if vac != best:
                        removed.append({
                            'vacancy': vac,
                            'reason': f"Дубликат компании '{vac.get('компания', '')}' (оставлена лучшая)",
                            'kept_vacancy_id': best.get('id', ''),
                            'kept_vacancy_title': best.get('название', '')
                        })
        
        return kept, removed
    
    def process_directory(self, input_dir: str, output_dir: str = None):
        """
        Обработка всех filtered_batch файлов в директории
        
        Args:
            input_dir: Директория с filtered_batch файлами
            output_dir: Директория для сохранения результатов (если None, перезаписываем)
        """
        input_path = Path(input_dir)
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
        else:
            output_path = input_path
        
        # Находим все filtered_batch файлы
        filtered_files = sorted(input_path.glob('filtered_batch_*.json'))
        
        if not filtered_files:
            print(f"❌ Не найдено файлов filtered_batch_*.json в {input_dir}")
            return
        
        print("=" * 70)
        print("🔄 УДАЛЕНИЕ ДУБЛИКАТОВ ПО КОМПАНИЯМ")
        print("=" * 70)
        print()
        print(f"📁 Найдено файлов: {len(filtered_files)}")
        print()
        print("📋 Правила дедупликации:")
        print("   1. Одна компания = одна вакансия")
        print("   2. Выбирается лучшая вакансия по критериям:")
        print("      - Приоритетные ключевые слова (входящие заявки, CRM)")
        print("      - Наличие зарплаты")
        print("      - Свежесть публикации")
        print("      - Подробность описания")
        print()
        
        # Тестовая проверка на первом файле
        print("🧪 Тестовая проверка на первом батче...")
        test_file = filtered_files[0]
        
        with open(test_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        test_kept, test_removed = self.deduplicate_batch(test_data)
        
        print(f"   Файл: {test_file.name}")
        print(f"   Было: {len(test_data)} вакансий")
        print(f"   Стало: {len(test_kept)} вакансий")
        print(f"   Удалено дубликатов: {len(test_removed)}")
        
        if test_removed:
            print()
            print("   Примеры удаленных дубликатов:")
            for i, dup in enumerate(test_removed[:3], 1):
                vac = dup['vacancy']
                print(f"   {i}. {vac.get('компания', 'N/A')} - {vac.get('название', 'N/A')[:60]}...")
        
        print()
        response = input("Продолжить обработку всех файлов? (да/нет): ").strip().lower()
        if response not in ['да', 'yes', 'y', 'д']:
            print("Отменено.")
            return
        
        print()
        print("🚀 Обработка всех файлов...")
        print()
        
        all_removed = []
        
        for i, file_path in enumerate(filtered_files, 1):
            # Читаем файл
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
            except Exception as e:
                print(f"⚠️ [{i}/{len(filtered_files)}] Ошибка чтения {file_path.name}: {e}")
                continue
            
            # Дедуплицируем
            kept, removed = self.deduplicate_batch(batch_data)
            
            self.stats['total_vacancies'] += len(batch_data)
            self.stats['kept_vacancies'] += len(kept)
            self.stats['duplicates_removed'] += len(removed)
            
            # Сохраняем дедуплицированный батч
            output_file = output_path / file_path.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(kept, f, ensure_ascii=False, indent=2)
            
            # Добавляем в общий список удаленных
            all_removed.extend(removed)
            
            # Показываем прогресс
            if len(removed) > 0:
                print(f"[{i}/{len(filtered_files)}] {file_path.name}: было {len(batch_data)}, убрали {len(removed)} дубликатов, осталось {len(kept)}")
            else:
                print(f"[{i}/{len(filtered_files)}] {file_path.name}: {len(batch_data)} (без дубликатов)", end='\r')
        
        print()
        print()
        
        # Подсчитываем уникальные компании
        all_companies = set()
        for file_path in filtered_files:
            with open(output_path / file_path.name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for vac in data:
                    company = vac.get('компания', '')
                    if company:
                        all_companies.add(self.normalize_company_name(company))
        
        self.stats['unique_companies'] = len(all_companies)
        
        # Сохраняем все удаленные дубликаты
        if all_removed:
            removed_file = output_path / 'removed_duplicates.json'
            with open(removed_file, 'w', encoding='utf-8') as f:
                json.dump(all_removed, f, ensure_ascii=False, indent=2)
            print(f"💾 Удаленные дубликаты сохранены: {removed_file}")
        
        # Обновляем статистику
        stats_file = output_path / 'filtering_stats.json'
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                old_stats = json.load(f)
            
            new_stats = {
                'total_batches': old_stats.get('total_batches', 0),
                'total_vacancies': self.stats['kept_vacancies'],
                'total_excluded': old_stats.get('total_excluded', 0) + self.stats['duplicates_removed'],
                'total_to_process': self.stats['kept_vacancies'],
                'unique_companies': self.stats['unique_companies'],
                'duplicates_removed': self.stats['duplicates_removed'],
                'total_high_priority': old_stats.get('total_high_priority', 0),
                'total_medium_priority': old_stats.get('total_medium_priority', 0),
                'total_low_priority': old_stats.get('total_low_priority', 0)
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(new_stats, f, ensure_ascii=False, indent=2)
        
        # Показываем статистику
        print()
        print("=" * 70)
        print("📊 СТАТИСТИКА ДЕДУПЛИКАЦИИ")
        print("=" * 70)
        print(f"Обработано вакансий: {self.stats['total_vacancies']}")
        print(f"Удалено дубликатов: {self.stats['duplicates_removed']} ({self.stats['duplicates_removed']/self.stats['total_vacancies']*100:.1f}%)")
        print(f"Осталось вакансий: {self.stats['kept_vacancies']}")
        print(f"Уникальных компаний: {self.stats['unique_companies']}")
        print()
        print(f"Среднее дубликатов на компанию: {self.stats['total_vacancies']/self.stats['unique_companies']:.2f}")
        print("=" * 70)
        print()
        print("✅ ГОТОВО!")


def main():
    """Основная функция"""
    
    # Директория с батчами
    INPUT_DIR = "filtered_batches"
    
    # Можно указать отдельную директорию для вывода или оставить None для перезаписи
    OUTPUT_DIR = None  # None = перезаписываем те же файлы
    
    # Создаем дедупликатор
    deduplicator = CompanyDeduplicator()
    
    # Обрабатываем
    deduplicator.process_directory(INPUT_DIR, OUTPUT_DIR)
    
    print()
    print("💡 Совет: Проверьте файл 'removed_duplicates.json' - там все удаленные дубликаты")


if __name__ == "__main__":
    main()

