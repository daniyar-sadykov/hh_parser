import json
import os
from pathlib import Path

def split_vacancies_to_batches(input_file, output_folder, batch_size=50):
    """
    Разбивает файл с вакансиями на батчи по указанному количеству.
    
    Args:
        input_file: путь к исходному JSON файлу
        output_folder: папка для сохранения батчей
        batch_size: количество вакансий в одном батче
    """
    print(f"📂 Чтение файла {input_file}...")
    
    # Читаем JSON файл
    with open(input_file, 'r', encoding='utf-8') as f:
        vacancies = json.load(f)
    
    total_vacancies = len(vacancies)
    print(f"✅ Загружено {total_vacancies} вакансий")
    
    # Создаем папку для батчей
    Path(output_folder).mkdir(exist_ok=True)
    print(f"📁 Создана папка: {output_folder}")
    
    # Разбиваем на батчи
    total_batches = (total_vacancies + batch_size - 1) // batch_size
    print(f"🔄 Создаю {total_batches} батчей по {batch_size} вакансий...")
    
    for i in range(0, total_vacancies, batch_size):
        batch_num = i // batch_size + 1
        batch = vacancies[i:i + batch_size]
        
        # Формируем имя файла с нулями в начале для правильной сортировки
        output_file = os.path.join(output_folder, f"batch_{batch_num:04d}.json")
        
        # Сохраняем батч
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ Батч {batch_num}/{total_batches}: {len(batch)} вакансий → {output_file}")
    
    print(f"\n🎉 Готово! Создано {total_batches} файлов в папке '{output_folder}'")
    print(f"📊 Всего вакансий обработано: {total_vacancies}")

if __name__ == "__main__":
    # Параметры
    INPUT_FILE = "vacancies_all.json"
    OUTPUT_FOLDER = "vacancy_batches"
    BATCH_SIZE = 50
    
    # Запускаем разбивку
    split_vacancies_to_batches(INPUT_FILE, OUTPUT_FOLDER, BATCH_SIZE)

