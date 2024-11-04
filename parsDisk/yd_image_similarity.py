import os
from PIL import Image
import numpy as np
import sqlite3
import pickle
import io
from yadisk import YaDisk
from loguru import logger
from tqdm import tqdm
from dotenv import load_dotenv
import time
import requests

load_dotenv()

class YandexImageSimilarityFinder:
    def __init__(self, db_path='yd_image_database.db', bins=8, isTest=True):
        self.yadisk = YaDisk(
            os.getenv('APLICATION_ID'),
            os.getenv('APLICATION_SECRET'),
            os.getenv('TOKEN_YD')
        )
        self.db_path = db_path
        self.bins = bins
        
        if isTest:
            self.pathMain = '/Производственный отдел/ТЕСТИРОВАНИЕ/'
        else:
            self.pathMain = '/Производственный отдел/ПРОЕКТЫ - собираем подборки под проекты, извлекаем отсюда новые/'
            
        self.setup_database()
        logger.add(
            "logs/yd_similarity_{time}.log",
            format="{time} - {level} - {message}",
            rotation="100 MB",
            retention="10 days",
            level="DEBUG"
        )

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    histogram BLOB NOT NULL,
                    md5_hash TEXT NOT NULL
                )
            ''')

    def calculate_histogram(self, image_data):
        """Вычисляет RGB гистограмму изображения из бинарных данных"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img_array = np.array(img)
                
                hist_r = np.histogram(img_array[:,:,0], bins=self.bins, range=(0,256))[0]
                hist_g = np.histogram(img_array[:,:,1], bins=self.bins, range=(0,256))[0]
                hist_b = np.histogram(img_array[:,:,2], bins=self.bins, range=(0,256))[0]
                
                total_pixels = img.size[0] * img.size[1]
                hist_r = hist_r / total_pixels
                hist_g = hist_g / total_pixels
                hist_b = hist_b / total_pixels
                
                histogram = np.concatenate([hist_r, hist_g, hist_b])
                
                return pickle.dumps(histogram)
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {str(e)}")
            return None

    def scan_directory(self, public_link):
        """Сканирует директорию на Яндекс.Диске и добавляет все изображения в базу данных"""
        logger.info(f"Начинаем сканирование директории по ссылке: {public_link}")
        
        folder_project = self.yadisk.get_public_meta(public_link).name
        all_path = self.pathMain + folder_project + '/'
        
        folders = []
        for item in self.yadisk.get_meta(all_path).embedded.items:
            if item.file is None:
                folders.append(item.path.replace('disk:' + all_path, ''))
        
        total_files = 0
        processed_files = 0
        
        # Подсчитываем общее количество файлов
        for folder in tqdm(folders, desc="Сканирование папок"):
            current_path = all_path + folder
            try:
                files = self.yadisk.get_meta(current_path).embedded.items
                for file in files:
                    if file.file is not None and file.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        total_files += 1
            except Exception as e:
                logger.error(f"Ошибка при сканировании {current_path}: {str(e)}")
                continue
        
        logger.info(f"Найдено {total_files} файлов для обработки")
        
        with sqlite3.connect(self.db_path) as conn:
            for folder in tqdm(folders, desc="Обработка папок"):
                cursor = conn.cursor()
                current_path = all_path + folder
                try:
                    files = self.yadisk.get_meta(current_path).embedded.items
                    for file in files:
                        if file.file is not None and file.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                            processed_files += 1
                            logger.info(f"Обработка [{processed_files}/{total_files}]: {file.name}")
                            
                            try:
                                # Получаем временную ссылку на файл
                                download_link = self.yadisk.get_download_link(file.path)
                                
                                # Скачиваем содержимое файла
                                response = requests.get(download_link)
                                if response.status_code == 200:
                                    image_data = response.content
                                    histogram = self.calculate_histogram(image_data)
                                    if histogram:
                                        cursor.execute(
                                            'INSERT INTO images (image_path, folder_path, histogram, md5_hash) VALUES (?, ?, ?, ?)',
                                            (file.path, current_path, histogram, file.md5)
                                        )
                                        conn.commit()
                                    else:
                                        logger.error(f"Не удалось создать гистограмму для {file.name}")
                                else:
                                    logger.error(f"Не удалось скачать файл {file.name}: {response.status_code}")
                            except Exception as e:
                                logger.error(f"Ошибка при обработке файла {file.name}: {str(e)}")
                                continue
                                
                except Exception as e:
                    logger.error(f"Ошибка при обработке папки {current_path}: {str(e)}")
                    continue
        
        logger.info(f"\nСканирование завершено. Обработано {processed_files} файлов")

    def calculate_similarity(self, hist1, hist2):
        """Вычисляет процент схожести между двумя гистограммами"""
        epsilon = 1e-10
        chi_square = np.sum((hist1 - hist2) ** 2 / (hist1 + hist2 + epsilon))
        similarity = 100 * np.exp(-chi_square)
        return similarity

    def find_similar_images(self, file_path, threshold=75):
        """Ищет похожие изображения в базе данных"""
        try:
            response = self.yadisk.download(file_path, None)
            histogram = self.calculate_histogram(response.content)
            if not histogram:
                return None

            hist1 = pickle.loads(histogram)
            similar_images = []

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT image_path, folder_path, histogram, md5_hash FROM images')
                
                for db_image_path, folder_path, db_histogram, md5_hash in cursor.fetchall():
                    hist2 = pickle.loads(db_histogram)
                    similarity = self.calculate_similarity(hist1, hist2)
                    if similarity >= threshold:
                        similar_images.append({
                            'file': os.path.basename(db_image_path),
                            'folder': folder_path,
                            'similarity': similarity,
                            'full_path': db_image_path,
                            'md5_hash': md5_hash
                        })
                
                if similar_images:
                    similar_images.sort(key=lambda x: x['similarity'], reverse=True)
                    
                    for idx, match in enumerate(similar_images, 1):
                        logger.info(f"\nСовпадение #{idx}:")
                        logger.info(f"Файл: {match['file']}")
                        logger.info(f"Полный путь: {match['full_path']}")
                        logger.info(f"Папка: {match['folder']}")
                        logger.info(f"MD5 хэш: {match['md5_hash']}")
                        logger.info(f"Процент схожести: {match['similarity']:.2f}%")
                    
                    return [match['folder'] for match in similar_images]
            return None
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих изображений: {str(e)}")
            return None

    def check_local_image(self, local_image_path, threshold=75):
        """Проверяет локальный файл на наличие похожих в Яндекс.Диске"""
        try:
            with open(local_image_path, 'rb') as f:
                image_data = f.read()
            
            histogram = self.calculate_histogram(image_data)
            if not histogram:
                return None

            hist1 = pickle.loads(histogram)
            similar_images = []

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT image_path, folder_path, histogram, md5_hash FROM images')
                
                for db_image_path, folder_path, db_histogram, md5_hash in cursor.fetchall():
                    hist2 = pickle.loads(db_histogram)
                    similarity = self.calculate_similarity(hist1, hist2)
                    if similarity >= threshold:
                        similar_images.append({
                            'file': os.path.basename(db_image_path),
                            'folder': folder_path,
                            'similarity': similarity,
                            'full_path': db_image_path,
                            'md5_hash': md5_hash
                        })
                
                if similar_images:
                    similar_images.sort(key=lambda x: x['similarity'], reverse=True)
                    
                    logger.info(f"\nДля локального файла: {os.path.basename(local_image_path)}")
                    for idx, match in enumerate(similar_images, 1):
                        logger.info(f"\nСовпадение #{idx}:")
                        logger.info(f"Файл на Яндекс.Диске: {match['file']}")
                        logger.info(f"Путь на диске: {match['full_path']}")
                        logger.info(f"Папка: {match['folder']}")
                        logger.info(f"MD5 хэш: {match['md5_hash']}")
                        logger.info(f"Процент схожести: {match['similarity']:.2f}%")
                    
                    return similar_images
            return None
        except Exception as e:
            logger.error(f"Ошибка при проверке локального файла {local_image_path}: {str(e)}")
            return None

    def upload_to_folder(self, local_image_path, target_folder):
        """Загружает локальный файл в указанную папку на Яндекс.Диске и добавляет в базу данных"""
        try:
            file_name = os.path.basename(local_image_path)
            target_path = f"{target_folder}/{file_name}"
            
            # Проверяем, существует ли файл с таким именем
            try:
                self.yadisk.get_meta(target_path)
                # Если файл существует, добавляем к имени timestamp
                name, ext = os.path.splitext(file_name)
                file_name = f"{name}_{int(time.time())}{ext}"
                target_path = f"{target_folder}/{file_name}"
            except:
                pass

            # Загружаем файл на Яндекс.Диск
            self.yadisk.upload(local_image_path, target_path)
            logger.info(f"Файл {file_name} успешно загружен в папку {target_folder}")

            # Добавляем файл в базу данных
            with open(local_image_path, 'rb') as f:
                image_data = f.read()
            
            histogram = self.calculate_histogram(image_data)
            if histogram:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    # Получаем MD5 хэш загруженного файла
                    file_meta = self.yadisk.get_meta(target_path)
                    cursor.execute(
                        'INSERT INTO images (image_path, folder_path, histogram, md5_hash) VALUES (?, ?, ?, ?)',
                        (target_path, target_folder, histogram, file_meta.md5)
                    )
                    logger.info(f"Файл {file_name} добавлен в базу данных")
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {local_image_path}: {str(e)}")
            return False