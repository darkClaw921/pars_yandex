from yd_image_similarity import YandexImageSimilarityFinder
import sys
import os

def scan_yandex_folder(finder, public_link):
    """Сканирование папки на Яндекс.Диске"""
    print(f"Сканирование папки по ссылке: {public_link}")
    finder.scan_directory(public_link)
    print("База данных создана.")

def check_local_image(finder, image_path):
    """Проверка локального изображения"""
    if not os.path.exists(image_path):
        print(f"Файл не найден: {image_path}")
        return

    results = finder.check_local_image(image_path)
    if results:
        print("\nНайдены похожие изображения на Яндекс.Диске!")
        
        # Группируем результаты по папкам
        folders = {}
        for match in results:
            if match['folder'] not in folders:
                folders[match['folder']] = []
            folders[match['folder']].append(match)

        # Показываем все найденные папки
        print("\nНайдены похожие изображения в следующих папках:")
        for idx, (folder, matches) in enumerate(folders.items(), 1):
            print(f"\n{idx}. Папка: {folder}")
            print("Найденные совпадения:")
            for match in matches:
                print(f"  - {match['file']} (схожесть: {match['similarity']:.2f}%)")

        # Если найдено несколько папок, спрашиваем пользователя
        if len(folders) > 1:
            while True:
                try:
                    folder_idx = int(input("\nВыберите номер папки для загрузки (0 для отмены): "))
                    if folder_idx == 0:
                        print("Загрузка отменена")
                        return
                    if 1 <= folder_idx <= len(folders):
                        selected_folder = list(folders.keys())[folder_idx - 1]
                        break
                    else:
                        print("Неверный номер папки")
                except ValueError:
                    print("Пожалуйста, введите число")
        else:
            selected_folder = list(folders.keys())[0]

        # Спрашиваем подтверждение загрузки
        answer = input(f"\nЗагрузить файл в папку {selected_folder}? (y/n): ")
        if answer.lower() == 'y':
            if finder.upload_to_folder(image_path, selected_folder):
                print("Файл успешно загружен и добавлен в базу данных!")
            else:
                print("Ошибка при загрузке файла.")
        else:
            print("Загрузка отменена")
    else:
        print("Похожих изображений не найдено")

def main():
    finder = YandexImageSimilarityFinder(bins=16)

    if len(sys.argv) < 2:
        print("Использование:")
        print("Для сканирования: python yd_example_usage.py scan ссылка_на_папку")
        print("Для проверки локального файла: python yd_example_usage.py check путь_к_локальному_файлу")
        return

    command = sys.argv[1]
    
    if command == "scan":
        if len(sys.argv) < 3:
            print("Укажите ссылку на папку Яндекс.Диска")
            return
        public_link = sys.argv[2]
        scan_yandex_folder(finder, public_link)
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Укажите путь к локальному файлу")
            return
        image_path = os.path.normpath(sys.argv[2])
        check_local_image(finder, image_path)
    
    else:
        print("Неизвестная команда. Используйте 'scan' или 'check'")

if __name__ == "__main__":
    main() 