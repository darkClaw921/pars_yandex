import os
from PIL import Image
import numpy as np
from pathlib import Path
import sqlite3
import logging
import pickle

class ImageSimilarityFinder:
    def __init__(self, db_path='image_database.db', bins=8):
        self.db_path = db_path
        self.bins = bins  # количество интервалов для каждого цветового канала
        self.setup_database()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    histogram BLOB NOT NULL
                )
            ''')

    def calculate_histogram(self, image_path):
        """Выисляет RGB гистограмму изображения"""
        try:
            with Image.open(image_path) as img:
                # Преобразуем изображение в RGB если оно в другом формате
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Преобразуем в numpy массив
                img_array = np.array(img)
                
                # Вычисляем гистограмму для каждого канала
                hist_r = np.histogram(img_array[:,:,0], bins=self.bins, range=(0,256))[0]
                hist_g = np.histogram(img_array[:,:,1], bins=self.bins, range=(0,256))[0]
                hist_b = np.histogram(img_array[:,:,2], bins=self.bins, range=(0,256))[0]
                
                # Нормализуем гистограммы
                total_pixels = img.size[0] * img.size[1]
                hist_r = hist_r / total_pixels
                hist_g = hist_g / total_pixels
                hist_b = hist_b / total_pixels
                
                # Объединяем гистограммы
                histogram = np.concatenate([hist_r, hist_g, hist_b])
                
                return pickle.dumps(histogram)
        except Exception as e:
            self.logger.error(f"Ошибка при обработке {image_path}: {str(e)}")
            return None

    def add_image_to_database(self, image_path):
        """Добавляет изображение в базу данных без проверки на схожесть"""
        histogram = self.calculate_histogram(image_path)
        if not histogram:
            return None

        # Получаем абсолютный путь к папке
        folder_path = str(Path(image_path).absolute().parent)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO images (image_path, folder_path, histogram) VALUES (?, ?, ?)',
                (str(image_path), folder_path, histogram)
            )
        return None

    def scan_directory(self, root_dir):
        """Сканирует директорию и добавляет все изображения в базу данных"""
        if not os.path.exists(root_dir):
            self.logger.error(f"Директория не существует: {root_dir}")
            return
            
        self.logger.info(f"Начинаем сканирование директории: {root_dir}")
        
        total_files = 0
        processed_files = 0
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        
        # Сначала подсчитаем общее количество файлов
        for folder_path, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    total_files += 1
                    self.logger.debug(f"Найден файл: {os.path.join(folder_path, file)}")
        
        if total_files == 0:
            self.logger.warning(f"В директории не найдено изображений с расширениями: {supported_extensions}")
            return
            
        self.logger.info(f"Найдено {total_files} изображений для обработки")
        
        # Теперь обрабатываем файлы
        with sqlite3.connect(self.db_path) as conn:
            for folder_path, _, files in os.walk(root_dir):
                current_folder_files = [f for f in files if f.lower().endswith(supported_extensions)]
                if current_folder_files:
                    self.logger.info(f"\nСканирование папки: {folder_path}")
                    self.logger.info(f"Найдено файлов в текущей папке: {len(current_folder_files)}")
                    
                    for file in current_folder_files:
                        image_path = os.path.join(folder_path, file)
                        processed_files += 1
                        self.logger.info(f"Обработка [{processed_files}/{total_files}]: {file}")
                        self.add_image_to_database(image_path)
        
        self.logger.info(f"\nСканирование завершено. Обработано {processed_files} файлов")

    def find_similar_images(self, image_path, threshold=75):
        """Ищет похожие изображения в базе данных"""
        histogram = self.calculate_histogram(image_path)
        if not histogram:
            return None

        hist1 = pickle.loads(histogram)
        similar_images = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT image_path, folder_path, histogram FROM images')
            
            for db_image_path, folder_path, db_histogram in cursor.fetchall():
                hist2 = pickle.loads(db_histogram)
                similarity = self.calculate_similarity(hist1, hist2)
                if similarity >= threshold:
                    similar_images.append({
                        'file': os.path.basename(db_image_path),
                        'folder': folder_path,
                        'similarity': similarity,
                        'full_path': db_image_path
                    })
            
            if similar_images:
                self.logger.info("\nНайдены похожие изображения!")
                # Сортируем по проценту схожести (от большего к меньшему)
                similar_images.sort(key=lambda x: x['similarity'], reverse=True)
                
                for idx, match in enumerate(similar_images, 1):
                    self.logger.info(f"\nСовпадение #{idx}:")
                    self.logger.info(f"Файл: {match['file']}")
                    self.logger.info(f"Полный путь: {match['full_path']}")
                    self.logger.info(f"Папка: {match['folder']}")
                    self.logger.info(f"Процент схожести: {match['similarity']:.2f}%")
                
                # Возвращаем список всех папок с похожими изображениями
                return [match['folder'] for match in similar_images]
        return None

    def calculate_similarity(self, hist1, hist2):
        """Вычисляет процент схожести между двумя гистограммами используя chi-square distance"""
        # Добавляем малое число, чтобы избежать деления на ноль
        epsilon = 1e-10
        # Вычисляем chi-square distance
        chi_square = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + epsilon))
        # Преобразуем расстояние в процент схожести
        similarity = 100 * np.exp(-chi_square)
        return similarity

    def add_image(self, image_path):
        """Добавляет одно изображение в базу данных с проверкой на схожесть"""
        histogram = self.calculate_histogram(image_path)
        if not histogram:
            return None

        # Получаем абсолютный путь к папке
        folder_path = str(Path(image_path).absolute().parent)
        
        similar_folders = self.find_similar_images(image_path, threshold=75)
        if similar_folders:
            self.logger.info(f"\nНовый файл: {os.path.basename(image_path)}")
            self.logger.info(f"Путь к новому файлу: {image_path}")
            return similar_folders

        self.logger.info(f"Добавлен новый файл: {image_path}")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO images (image_path, folder_path, histogram) VALUES (?, ?, ?)',
                (str(image_path), folder_path, histogram)
            )
        return None