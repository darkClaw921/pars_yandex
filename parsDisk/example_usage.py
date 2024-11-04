from image_similarity import ImageSimilarityFinder
import os
import sys

def scan_directory(finder, path):
    """Первичное сканирование директории"""
    print(f"Сканируемая директория: {path}")
    finder.scan_directory(path)
    print("База данных создана. Теперь вы можете добавлять новые изображения для поиска.")

def add_folder(finder, path):
    """Добавление новой папки в существующую базу"""
    print(f"Добавление папки в базу: {path}")
    finder.scan_directory(path)
    print("Папка добавлена в базу данных.")

def check_image(finder, image_path):
    """Проверка одного изображения"""
    if os.path.exists(image_path):
        results = finder.add_image(image_path)
        if results:
            print("\nПохожие изображения найдены в следующих папках:")
            for idx, folder in enumerate(results, 1):
                print(f"{idx}. {folder}")
        else:
            print("Похожих изображений не найдено")
    else:
        print(f"Изображение не найдено: {image_path}")

def main():
    # Создаем экземпляр класса
    finder = ImageSimilarityFinder(bins=16)

    # Получаем аргументы командной строки
    if len(sys.argv) < 2:
        print("Использование:")
        print("Для первичного сканирования: python example_usage.py scan путь/к/папке")
        print("Для добавления новой папки: python example_usage.py add путь/к/новой/папке")
        print("Для проверки: python example_usage.py check путь/к/изображению")
        return

    command = sys.argv[1]
    
    if command == "scan":
        if len(sys.argv) < 3:
            print("Укажите путь к папке для сканирования")
            return
        scan_path = os.path.normpath(sys.argv[2])
        scan_directory(finder, scan_path)
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("Укажите путь к папке для добавления")
            return
        folder_path = os.path.normpath(sys.argv[2])
        add_folder(finder, folder_path)
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Укажите путь к изображению для проверки")
            return
        image_path = os.path.normpath(sys.argv[2])
        check_image(finder, image_path)
    
    else:
        print("Неизвестная команда. Используйте 'scan', 'add' или 'check'")

if __name__ == "__main__":
    main() 