"""
Фильтрация нежелательных вакансий:
- Агенты по недвижимости
- Менеджеры продаж
- Брокеры
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple


class UnwantedVacanciesFilter:
    """Фильтр для удаления нежелательных вакансий"""
    
    def __init__(self):
        # Ключевые слова для фильтрации (в нижнем регистре)
        self.unwanted_keywords = {
            'недвижимость': [
                'агент по недвижимости',
                'риэлтор',
                'риелтор',
                'специалист по недвижимости',
                'консультант по недвижимости',
                'менеджер по недвижимости',
                'брокер недвижимости',
                'риелторские услуги',
                'сделки с недвижимостью'
            ],
            'продажи': [
                'менеджер по продажам',
                'специалист по продажам',
                'продавец-консультант',
                'торговый представитель',
                'менеджер активных продаж',
                'менеджер по привлечению клиентов',
                'sales manager',
                'специалист отдела продаж'
            ],
            'брокеры': [
                'брокер',
                'страховой брокер',
                'финансовый брокер',
                'кредитный брокер',
                'таможенный брокер',
                'биржевой брокер'
            ]
        }
        
        # Исключения - вакансии, которые НЕ надо фильтровать, даже если есть ключевые слова
        self.exceptions = [
            'входящие заявки',
            'обработка заявок',
            'без холодных звонков',
            'теплые заявки',
            'crm',
            'битрикс',
            'amoCRM',
            'чат',
            'оператор',
            'колл-центр',
            'call-центр',
            'техподдержка',
            'поддержка',
            'саппорт',
            'support'
        ]
        
        self.stats = {
            'processed_files': 0,
            'total_vacancies': 0,
            'filtered_out': 0,
            'reasons': {}
        }
    
    def is_unwanted(self, vacancy: Dict) -> Tuple[bool, str]:
        """
        Проверка, является ли вакансия нежелательной
        
        Returns:
            (is_unwanted, reason)
        """
        title = vacancy.get('название', '').lower()
        description = vacancy.get('описание', '').lower()
        
        # Проверяем исключения - если есть, то НЕ фильтруем
        for exception in self.exceptions:
            if exception.lower() in title or exception.lower() in description:
                return False, ""
        
        # Проверяем нежелательные ключевые слова
        for category, keywords in self.unwanted_keywords.items():
            for keyword in keywords:
                # Проверяем название
                if keyword in title:
                    reason = f"Категория: {category}, найдено в названии: '{keyword}'"
                    return True, reason
                
                # Проверяем описание (только для коротких фраз)
                if len(keyword.split()) <= 3:  # Короткие фразы
                    # Используем регулярные выражения для точного поиска
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, description):
                        reason = f"Категория: {category}, найдено в описании: '{keyword}'"
                        return True, reason
        
        return False, ""
    
    def filter_batch(self, batch_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Фильтрация батча вакансий
        
        Returns:
            (kept_vacancies, filtered_vacancies)
        """
        kept = []
        filtered = []
        
        for vacancy in batch_data:
            is_unwanted, reason = self.is_unwanted(vacancy)
            
            if is_unwanted:
                filtered.append({
                    'vacancy': vacancy,
                    'reason': reason
                })
                
                # Обновляем статистику
                category = reason.split(',')[0].replace('Категория: ', '')
                self.stats['reasons'][category] = self.stats['reasons'].get(category, 0) + 1
            else:
                kept.append(vacancy)
        
        return kept, filtered
    
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
        print("🔍 ФИЛЬТРАЦИЯ НЕЖЕЛАТЕЛЬНЫХ ВАКАНСИЙ")
        print("=" * 70)
        print()
        print(f"📁 Найдено файлов: {len(filtered_files)}")
        print()
        print("🚫 Фильтруем:")
        print("   - Агенты по недвижимости")
        print("   - Менеджеры продаж")
        print("   - Брокеры")
        print()
        print("✅ НЕ фильтруем, если есть:")
        print("   - 'входящие заявки'")
        print("   - 'обработка заявок'")
        print("   - 'CRM', 'Битрикс', 'чат', 'оператор'")
        print()
        
        # Автоматический запуск (закомментируйте для запроса подтверждения)
        # response = input("Начать фильтрацию? (да/нет): ").strip().lower()
        # if response not in ['да', 'yes', 'y', 'д']:
        #     print("Отменено.")
        #     return
        
        print()
        print("🚀 Обработка файлов...")
        print()
        
        all_filtered = []
        
        for i, file_path in enumerate(filtered_files, 1):
            # Читаем файл
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
            except Exception as e:
                print(f"⚠️ [{i}/{len(filtered_files)}] Ошибка чтения {file_path.name}: {e}")
                continue
            
            # Фильтруем
            kept, filtered = self.filter_batch(batch_data)
            
            self.stats['processed_files'] += 1
            self.stats['total_vacancies'] += len(batch_data)
            self.stats['filtered_out'] += len(filtered)
            
            # Сохраняем отфильтрованный батч
            if kept:
                output_file = output_path / file_path.name
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(kept, f, ensure_ascii=False, indent=2)
            
            # Добавляем в общий список отфильтрованных
            all_filtered.extend(filtered)
            
            # Показываем прогресс
            if len(filtered) > 0:
                print(f"[{i}/{len(filtered_files)}] {file_path.name}: было {len(batch_data)}, убрали {len(filtered)}, осталось {len(kept)}")
            else:
                print(f"[{i}/{len(filtered_files)}] {file_path.name}: {len(batch_data)} (без изменений)", end='\r')
        
        print()
        print()
        
        # Сохраняем все отфильтрованные вакансии
        if all_filtered:
            filtered_file = output_path / 'removed_unwanted.json'
            with open(filtered_file, 'w', encoding='utf-8') as f:
                json.dump(all_filtered, f, ensure_ascii=False, indent=2)
            print(f"💾 Отфильтрованные вакансии сохранены: {filtered_file}")
        
        # Обновляем статистику
        stats_file = output_path / 'filtering_stats.json'
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                old_stats = json.load(f)
            
            new_stats = {
                'total_batches': old_stats.get('total_batches', 0),
                'total_vacancies': self.stats['total_vacancies'] - self.stats['filtered_out'],
                'total_excluded': old_stats.get('total_excluded', 0) + self.stats['filtered_out'],
                'total_to_process': self.stats['total_vacancies'] - self.stats['filtered_out'],
                'total_high_priority': old_stats.get('total_high_priority', 0),
                'total_medium_priority': old_stats.get('total_medium_priority', 0),
                'total_low_priority': old_stats.get('total_low_priority', 0)
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(new_stats, f, ensure_ascii=False, indent=2)
        
        # Показываем статистику
        print()
        print("=" * 70)
        print("📊 СТАТИСТИКА ФИЛЬТРАЦИИ")
        print("=" * 70)
        print(f"Обработано файлов: {self.stats['processed_files']}")
        print(f"Всего вакансий: {self.stats['total_vacancies']}")
        print(f"Отфильтровано: {self.stats['filtered_out']} ({self.stats['filtered_out']/self.stats['total_vacancies']*100:.1f}%)")
        print(f"Осталось: {self.stats['total_vacancies'] - self.stats['filtered_out']}")
        print()
        print("По категориям:")
        for category, count in sorted(self.stats['reasons'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {category}: {count}")
        print("=" * 70)
        print()
        print("✅ ГОТОВО!")


def main():
    """Основная функция"""
    
    # Директория с батчами
    INPUT_DIR = "filtered_batches"
    
    # Можно указать отдельную директорию для вывода или оставить None для перезаписи
    OUTPUT_DIR = None  # None = перезаписываем те же файлы
    
    # Создаем фильтр
    filter_tool = UnwantedVacanciesFilter()
    
    # Обрабатываем
    filter_tool.process_directory(INPUT_DIR, OUTPUT_DIR)
    
    print()
    print("💡 Совет: Проверьте файл 'removed_unwanted.json' - там все удаленные вакансии")


if __name__ == "__main__":
    main()

