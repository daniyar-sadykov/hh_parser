"""
ОБЪЕДИНЕНИЕ КОНТАКТОВ ИЗ РАЗНЫХ ИСТОЧНИКОВ
Комбинирует результаты из 2GIS, HH.ru и других источников
"""

import json
import csv
from typing import Dict, List
from pathlib import Path
from datetime import datetime


class ContactsMerger:
    """Объединение контактов из разных источников"""
    
    def __init__(self):
        self.merged_contacts = {}
    
    def load_json(self, file_path: str) -> List[Dict]:
        """Загрузить контакты из JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки {file_path}: {e}")
            return []
    
    def merge_company_contacts(self, existing: Dict, new: Dict) -> Dict:
        """
        Объединить контакты одной компании из разных источников
        
        Args:
            existing: Существующие контакты
            new: Новые контакты
            
        Returns:
            Объединенные контакты
        """
        merged = existing.copy()
        
        # Объединяем списки контактов (без дубликатов)
        for field in ['phones', 'emails', 'websites']:
            existing_items = set(existing.get(field, []))
            new_items = set(new.get(field, []))
            merged[field] = list(existing_items | new_items)
        
        # Обновляем адрес если не был заполнен
        if not merged.get('address') and new.get('address'):
            merged['address'] = new['address']
        
        # Обновляем полное название если не было
        if not merged.get('full_name') and new.get('full_name'):
            merged['full_name'] = new['full_name']
        
        # Добавляем HH.ru ссылку
        if new.get('hh_company_url'):
            merged['hh_company_url'] = new['hh_company_url']
        
        # Объединяем источники
        sources = set()
        if existing.get('source'):
            sources.add(existing['source'])
        if new.get('source'):
            sources.add(new['source'])
        merged['sources'] = list(sources)
        
        # Если хоть из одного источника found=True
        merged['found'] = existing.get('found', False) or new.get('found', False)
        
        # Обновляем дату
        merged['last_updated'] = datetime.now().isoformat()
        
        return merged
    
    def merge_files(self, file_paths: List[str]) -> Dict[str, Dict]:
        """
        Объединить несколько файлов с контактами
        
        Args:
            file_paths: Список путей к JSON файлам
            
        Returns:
            Словарь компания -> контакты
        """
        print("🔄 Объединение контактов из разных источников...")
        print()
        
        all_contacts = {}
        
        for file_path in file_paths:
            if not Path(file_path).exists():
                print(f"⚠️ Файл не найден: {file_path}")
                continue
            
            print(f"📖 Загружаем: {file_path}")
            contacts_list = self.load_json(file_path)
            
            for contact in contacts_list:
                company_name = contact.get('company_name', '').strip()
                if not company_name:
                    continue
                
                if company_name not in all_contacts:
                    all_contacts[company_name] = contact
                else:
                    # Объединяем с существующими
                    all_contacts[company_name] = self.merge_company_contacts(
                        all_contacts[company_name],
                        contact
                    )
            
            print(f"   ✓ Загружено: {len(contacts_list)} компаний")
        
        print()
        print(f"✅ Всего уникальных компаний: {len(all_contacts)}")
        
        return all_contacts
    
    def analyze_merged(self, merged: Dict[str, Dict]) -> Dict:
        """Анализ объединенных данных"""
        stats = {
            'total_companies': len(merged),
            'found': 0,
            'with_phones': 0,
            'with_emails': 0,
            'with_websites': 0,
            'with_address': 0,
            'from_2gis': 0,
            'from_hh': 0,
            'from_multiple_sources': 0,
            'quality_excellent': 0,  # Телефон + Email + Сайт
            'quality_good': 0,       # 2 из 3
            'quality_basic': 0,      # 1 из 3
            'quality_none': 0        # Ничего не найдено
        }
        
        for company, data in merged.items():
            if data.get('found'):
                stats['found'] += 1
            
            has_phone = len(data.get('phones', [])) > 0
            has_email = len(data.get('emails', [])) > 0
            has_website = len(data.get('websites', [])) > 0
            
            if has_phone:
                stats['with_phones'] += 1
            if has_email:
                stats['with_emails'] += 1
            if has_website:
                stats['with_websites'] += 1
            if data.get('address'):
                stats['with_address'] += 1
            
            # Источники
            sources = data.get('sources', [data.get('source', '')])
            if '2gis' in sources:
                stats['from_2gis'] += 1
            if any(s in ['hh.ru', 'free', 'alternative'] for s in sources):
                stats['from_hh'] += 1
            if len(sources) > 1:
                stats['from_multiple_sources'] += 1
            
            # Качество данных
            contact_count = sum([has_phone, has_email, has_website])
            if contact_count >= 3:
                stats['quality_excellent'] += 1
            elif contact_count == 2:
                stats['quality_good'] += 1
            elif contact_count == 1:
                stats['quality_basic'] += 1
            else:
                stats['quality_none'] += 1
        
        return stats
    
    def export_to_csv(self, merged: Dict[str, Dict], output_file: str):
        """Экспорт объединенных контактов в CSV"""
        try:
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = [
                    'company_name', 'full_name', 'found', 'sources',
                    'phones', 'emails', 'websites', 'hh_company_url',
                    'address', 'last_updated', 'quality'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for company_name, data in merged.items():
                    # Определяем качество
                    has_phone = len(data.get('phones', [])) > 0
                    has_email = len(data.get('emails', [])) > 0
                    has_website = len(data.get('websites', [])) > 0
                    contact_count = sum([has_phone, has_email, has_website])
                    
                    if contact_count >= 3:
                        quality = "Отлично"
                    elif contact_count == 2:
                        quality = "Хорошо"
                    elif contact_count == 1:
                        quality = "Базовая"
                    else:
                        quality = "Нет данных"
                    
                    row = {
                        'company_name': company_name,
                        'full_name': data.get('full_name', company_name),
                        'found': data.get('found', False),
                        'sources': ', '.join(data.get('sources', [data.get('source', '')])),
                        'phones': '; '.join(data.get('phones', [])),
                        'emails': '; '.join(data.get('emails', [])),
                        'websites': '; '.join(data.get('websites', [])),
                        'hh_company_url': data.get('hh_company_url', ''),
                        'address': data.get('address', ''),
                        'last_updated': data.get('last_updated', data.get('search_date', '')),
                        'quality': quality
                    }
                    writer.writerow(row)
            
            print(f"💾 CSV сохранен: {output_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения CSV: {e}")
    
    def export_to_json(self, merged: Dict[str, Dict], output_file: str):
        """Экспорт объединенных контактов в JSON"""
        try:
            # Конвертируем в список
            contacts_list = list(merged.values())
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(contacts_list, f, ensure_ascii=False, indent=2)
            
            print(f"💾 JSON сохранен: {output_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")


def main():
    """Основная функция"""
    
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🔄 ОБЪЕДИНЕНИЕ КОНТАКТОВ" + " " * 28 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Ищем все файлы с контактами
    print("🔍 Поиск файлов с контактами...")
    print()
    
    contact_files = []
    
    # Ищем файлы с контактами
    for pattern in ['smart_contacts_*.json', 'free_contacts_*.json', 'company_contacts_*.json']:
        files = list(Path('.').glob(pattern))
        contact_files.extend([str(f) for f in files])
    
    if not contact_files:
        print("❌ Файлы с контактами не найдены!")
        print()
        print("Запустите сначала:")
        print("  - python smart_contacts_finder.py")
        print("  - python free_contacts_finder.py")
        return
    
    print("Найдены файлы:")
    for i, file in enumerate(contact_files, 1):
        file_path = Path(file)
        size = file_path.stat().st_size / 1024  # KB
        print(f"  {i}. {file} ({size:.1f} KB)")
    
    print()
    response = input(f"Объединить все {len(contact_files)} файлов? (да/нет): ").strip().lower()
    
    if response not in ['да', 'yes', 'y', 'д']:
        print("Отменено.")
        return
    
    print()
    
    # Создаем объединитель
    merger = ContactsMerger()
    
    # Объединяем файлы
    merged = merger.merge_files(contact_files)
    
    if merged:
        # Анализ
        print()
        print("=" * 70)
        print("📊 АНАЛИЗ ОБЪЕДИНЕННЫХ ДАННЫХ")
        print("=" * 70)
        
        stats = merger.analyze_merged(merged)
        
        print(f"Всего компаний: {stats['total_companies']}")
        print(f"Найдены контакты: {stats['found']}")
        print()
        print("Тип контактов:")
        print(f"  📞 С телефонами: {stats['with_phones']} ({stats['with_phones']/stats['total_companies']*100:.1f}%)")
        print(f"  📧 С email: {stats['with_emails']} ({stats['with_emails']/stats['total_companies']*100:.1f}%)")
        print(f"  🌐 С сайтами: {stats['with_websites']} ({stats['with_websites']/stats['total_companies']*100:.1f}%)")
        print(f"  📍 С адресами: {stats['with_address']} ({stats['with_address']/stats['total_companies']*100:.1f}%)")
        print()
        print("Источники:")
        print(f"  🗺️  Из 2GIS: {stats['from_2gis']}")
        print(f"  💼 Из HH.ru: {stats['from_hh']}")
        print(f"  🔗 Из нескольких источников: {stats['from_multiple_sources']}")
        print()
        print("Качество данных:")
        print(f"  ⭐⭐⭐ Отлично (тел+email+сайт): {stats['quality_excellent']}")
        print(f"  ⭐⭐ Хорошо (2 из 3): {stats['quality_good']}")
        print(f"  ⭐ Базовая (1 из 3): {stats['quality_basic']}")
        print(f"  ❌ Нет данных: {stats['quality_none']}")
        print("=" * 70)
        print()
        
        # Экспорт
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_csv = f"merged_contacts_{timestamp}.csv"
        output_json = f"merged_contacts_{timestamp}.json"
        
        merger.export_to_csv(merged, output_csv)
        merger.export_to_json(merged, output_json)
        
        print()
        print("✅ ГОТОВО!")
        print()
        print(f"📊 Результат: {stats['found']}/{stats['total_companies']} компаний с контактами")
        print(f"📈 Покрытие: {stats['found']/stats['total_companies']*100:.1f}%")
    else:
        print("❌ Нет данных для объединения")


if __name__ == "__main__":
    main()

