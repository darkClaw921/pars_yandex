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
import asyncio

load_dotenv()

class YandexImageSimilarityFinder:
    def __init__(self, db_path='yd_image_database.db', bins=8, isTest=False):
        self.yadisk = YaDisk(
            os.getenv('APLICATION_ID'),
            os.getenv('APLICATION_SECRET'),
            os.getenv('TOKEN_YD')
        )
        self.db_path = db_path
        self.bins = bins
        
        if isTest:
            # self.pathMain = '/Производственный отдел/ТЕСТИРОВАНИЕ/'
            self.pathMain = '/Производственный отдел/ТЕСТИРОВАНИЕ/'
        else:
            # self.pathMain = '/Производственный отдел/ПРОЕКТЫ - собираем подборки под проекты, извлекаем отсюда новые/'
            self.pathMain = '/Производственный отдел/BBase 🗄/'
            
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folder_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_path TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folder_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_folder TEXT NOT NULL,
                    target_folder TEXT NOT NULL,
                    new_path TEXT,
                    status TEXT NOT NULL,
                    processed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        for folder in tqdm(folders, desc="Сканировние папок"):
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

    def find_similar_images(self, file_path, threshold=91):
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

    def check_local_image(self, local_image_path, threshold=91):
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

    def is_folder_in_database(self, folder_path):
        """Проверяет, есть ли папка в базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Проверяем наличие файлов в папке и её подпапках с учетом префикса "disk:"
                patterns = [
                    f"{folder_path}%",  # без префикса
                    f"disk:{folder_path}%"  # с префиксом
                ]
                cursor.execute('''
                    SELECT COUNT(*) FROM images 
                    WHERE image_path LIKE ? OR image_path LIKE ?
                    OR folder_path LIKE ? OR folder_path LIKE ?
                ''', (*patterns, *patterns))
                count = cursor.fetchone()[0]
                
                logger.info(f"Проверка папки {folder_path} в базе данных")
                logger.info(f"Найдено {count} файлов")
                
                # Выводим все пути в базе для отладки
                cursor.execute('SELECT DISTINCT folder_path FROM images')
                all_paths = cursor.fetchall()
                logger.info("Существующие пути в базе данных:")
                for path in all_paths:
                    logger.info(path[0])
                
                return count > 0
        except Exception as e:
            logger.error(f"Ошибка при проверк папки в базе данных: {str(e)}")
            return False

    def compare_folders(self, folder1_path, folder2_path, threshold=91):
        """Сравнивает две папки и находит похожие фотографии"""
        similar_photos = []
        logger.info(f"Сравниваю папки:\n{folder1_path}\n{folder2_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем содержимое базы данных
            cursor.execute('SELECT COUNT(*) FROM images')
            total_images = cursor.fetchone()[0]
            logger.info(f"Всего изображений в базе данных: {total_images}")
            
            # Получаем все фотографии из первой папки и её подпапок
            patterns1 = [f"{folder1_path}%", f"disk:{folder1_path}%"]
            query1 = '''
                SELECT image_path, histogram FROM images 
                WHERE image_path LIKE ? OR image_path LIKE ?
                OR folder_path LIKE ? OR folder_path LIKE ?
            '''
            cursor.execute(query1, (*patterns1, *patterns1))
            folder1_photos = cursor.fetchall()
            logger.info(f"SQL запрос для первой папки: {query1}")
            logger.info(f"Найдено {len(folder1_photos)} фото в первой папке")
            
            # Получаем все фотографии из второй папки и её подпапок
            patterns2 = [f"{folder2_path}%", f"disk:{folder2_path}%"]
            query2 = '''
                SELECT image_path, histogram FROM images 
                WHERE image_path LIKE ? OR image_path LIKE ?
                OR folder_path LIKE ? OR folder_path LIKE ?
            '''
            cursor.execute(query2, (*patterns2, *patterns2))
            folder2_photos = cursor.fetchall()
            logger.info(f"SQL запрос для второй папки: {query2}")
            logger.info(f"Найдено {len(folder2_photos)} фото во второй папке")
            
            if not folder1_photos or not folder2_photos:
                logger.warning("Одна или обе папки пусты в базе данных")
                return similar_photos
            
            # Сравниваем каждую фотографию из первой папки с каждой из второй
            total_comparisons = len(folder1_photos) * len(folder2_photos)
            current_comparison = 0
            
            for path1, hist1_blob in folder1_photos:
                hist1 = pickle.loads(hist1_blob)
                
                for path2, hist2_blob in folder2_photos:
                    current_comparison += 1
                    if current_comparison % 100 == 0:
                        1+0
                        # logger.info(f"Прогресс сравнения: {current_comparison}/{total_comparisons}")
                    
                    hist2 = pickle.loads(hist2_blob)
                    similarity = self.calculate_similarity(hist1, hist2)
                    
                    if similarity >= threshold:
                        similar_photos.append({
                            'file1': os.path.basename(path1),
                            'file2': os.path.basename(path2),
                            'similarity': similarity,
                            'full_path1': path1,
                            'full_path2': path2
                        })
                        logger.info(f"Найдено совпадение: {path1} и {path2} ({similarity:.2f}%)")
        
        logger.info(f"Найдено {len(similar_photos)} похожих фотографий")
        return similar_photos

    def get_all_files_from_folder(self, folder_path, exclude_files):
        """Получает список всех файлов из папки, исключая указанные"""
        files = []
        for item in self.yadisk.get_meta(folder_path).embedded.items:
            if item.file is not None and item.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                if os.path.basename(item.path) not in exclude_files:
                    files.append(item.path)
        return files

    def move_file(self, source_path, target_folder):
        """Перемещает файл в указанную папку"""
        try:
            file_name = os.path.basename(source_path)
            target_path = f"{target_folder}/{file_name}"
            
            # Если файл с таким именем уе существует, добавляем timestamp
            try:
                self.yadisk.get_meta(target_path)
                name, ext = os.path.splitext(file_name)
                target_path = f"{target_folder}/{name}_{int(time.time())}{ext}"
            except:
                pass
            
            self.yadisk.move(source_path, target_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка при перемещении файла {source_path}: {str(e)}")
            return False

    def count_files_recursive(self, path):
        """Рекурсивно подсчитывает количество файлов в папке и подпапках"""
        total = 0
        try:
            
            # path='disk:'+path
            print(path)
            items = self.yadisk.get_meta(path).embedded.items
            for item in items:
                if item.file is not None and item.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    total += 1
                elif item.file is None:  # Это папка
                    total += self.count_files_recursive(item.path)
        except Exception as e:
            logger.error(f"Ошибка при подсчете файлов в {path}: {str(e)}")
        return total

    async def scan_directory_async(self, public_link, progress_callback):
        """Асинхронно сканирует директорию на Яндекс.Диске"""
        try:
            logger.info(f"Начинаем сканирование директории по ссылке: {public_link}")
            
            folder_project = self.yadisk.get_public_meta(public_link).name
            


            all_path = self.pathMain + folder_project + '/'
            start_time = time.time()

            if folder_project == self.pathMain.split('/')[-2]:
                all_path = self.pathMain

            if folder_project == '/Производственный отдел/BBase 🗄/BBase/':
                all_path = self.pathMain
            
            # Подсчитываем общее количество файлов
            total_files = self.count_files_recursive(all_path)  # Используем метод класса
            logger.info(f"Всего найдено файлов: {total_files}")
            
            if total_files == 0:
                logger.warning("Не найдено файлов для обработки")
                return False
            
            processed_files = [0]  # Используем список для передачи по ссылке
            files_added = [0]  # Счетчик добавленных файлов
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                await self.scan_folder_recursive(all_path, conn, cursor, processed_files, total_files, files_added, start_time, progress_callback)
            
            logger.info(f"Сканирование завершено. Обработано {processed_files[0]} файлов, добавлено в базу {files_added[0]}")
            return files_added[0] > 0  # Возвращаем True, если были добавлены файлы
            
        except Exception as e:
            logger.error(f"Ошибка при сканировании директории: {str(e)}")
            return False

    async def scan_folder_recursive(self, path, conn, cursor, processed_files, total_files, files_added, start_time, progress_callback):
        """Рекурсивно сканирует папку и её подпапки"""
        try:
            items = self.yadisk.get_meta(path).embedded.items
            for item in items:
                if item.file is not None and item.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    try:
                        # Проверяем оба варианта пути
                        cursor.execute(
                            'SELECT COUNT(*) FROM images WHERE image_path = ? OR image_path = ?', 
                            (item.path, f"disk:{item.path}")
                        )
                        if cursor.fetchone()[0] == 0:
                            download_link = self.yadisk.get_download_link(item.path)
                            
                            response = requests.get(download_link)
                            if response.status_code == 200:
                                image_data = response.content
                                histogram = self.calculate_histogram(image_data)
                                if histogram:
                                    # Сохраняем путь без префикса "disk:"
                                    clean_path = item.path.replace('disk:', '')
                                    cursor.execute(
                                        'INSERT INTO images (image_path, folder_path, histogram, md5_hash) VALUES (?, ?, ?, ?)',
                                        (clean_path, path, histogram, item.md5)
                                    )
                                    conn.commit()
                                    files_added[0] += 1
                                    logger.info(f"Добавлен файл: {clean_path} в папке: {path}")
                    
                        processed_files[0] += 1
                        # Вычисляем оствшееся время
                        elapsed_time = time.time() - start_time
                        files_per_second = processed_files[0] / elapsed_time if elapsed_time > 0 else 0
                        remaining_files = total_files - processed_files[0]
                        estimated_time = remaining_files / files_per_second if files_per_second > 0 else 0
                        
                        # Форматируем время
                        estimated_minutes = int(estimated_time / 60)
                        estimated_seconds = int(estimated_time % 60)
                        time_str = f"{estimated_minutes}м {estimated_seconds}с"
                        
                        await progress_callback(processed_files[0], total_files, time_str)
                        await asyncio.sleep(0.1)
                    
                    except Exception as e:
                        logger.error(f"Ошибка при обработке файла {item.name}: {str(e)}")
                        continue
                    
                elif item.file is None:  # Это папка
                    await self.scan_folder_recursive(item.path, conn, cursor, processed_files, total_files, files_added, start_time, progress_callback)
                
        except Exception as e:
            logger.error(f"Ошибка при сканировании папки {path}: {str(e)}")

    def get_public_link(self, path):
        """Получает публичную ссылку на файл или папку"""
        try:
            # Проверяем, есть ли уже публичная ссылка
            resource = self.yadisk.get_meta(path)
            if not resource.public_url:
                resource = self.yadisk.publish(path)
            return resource.public_url
        except Exception as e:
            logger.error(f"Ошибка при получении публичной ссылки для {path}: {str(e)}")
            return path  # Возвращаем путь, если не удалось получить ссылку

    async def add_folder_tag(self, folder_path, tag):
        """Добавляет тег к папке в базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO folder_tags (folder_path, tag) VALUES (?, ?)',
                    (folder_path, tag)
                )
                logger.info(f"Добавлен тег '{tag}' к папке {folder_path} в базе данных")
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении тега к папке {folder_path}: {str(e)}")
            raise

    def get_folder_tags(self, folder_path):
        """Получает все теги папки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT tag FROM folder_tags WHERE folder_path = ? ORDER BY created_at DESC',
                    (folder_path,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка при получении тегов папки {folder_path}: {str(e)}")
            return []

    def folder_exists(self, folder_path):
        """Проверяет существование папки"""
        try:
            self.yadisk.get_meta(folder_path)
            return True
        except:
            return False

    def create_folder(self, folder_path):
        """Создает новую папку"""
        try:
            self.yadisk.mkdir(folder_path)
            logger.info(f"Создана папка: {folder_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании папки {folder_path}: {str(e)}")
            return False

    def update_paths_in_database(self, old_path, new_path):
        """Обновляет пути в базе данных после перемещения папки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Обновляем пути в таблице images
                cursor.execute('''
                    UPDATE images 
                    SET image_path = REPLACE(image_path, ?, ?),
                        folder_path = REPLACE(folder_path, ?, ?)
                    WHERE image_path LIKE ? || '%' 
                    OR folder_path LIKE ? || '%'
                ''', (old_path, new_path, old_path, new_path, old_path, old_path))
                
                # Обновляем пути в таблице folder_tags
                cursor.execute('''
                    UPDATE folder_tags 
                    SET folder_path = REPLACE(folder_path, ?, ?)
                    WHERE folder_path LIKE ? || '%'
                ''', (old_path, new_path, old_path))
                
                logger.info(f"Обновлены пути в базе данных: {old_path} -> {new_path}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении путей в базе данных: {str(e)}")
            return False

    async def move_folder(self, source_path, target_path):
        """Перемещает папку и обновляет пути в базе данных"""
        try:
            folder_name = os.path.basename(source_path)
            new_path = os.path.join(target_path, folder_name)
            
            # Сначала перемещаем папку
            self.yadisk.move(source_path, new_path)
            logger.info(f"Папка {source_path} перемещена в {target_path}")
            
            # Затем обновляем пути в базе данных
            if not self.update_paths_in_database(source_path, new_path):
                logger.warning("Не удалось обновить пути в базе данных")
            
            return new_path
        except Exception as e:
            logger.error(f"Ошибка при перемещении папки {source_path}: {str(e)}")
            raise

    def cleanup_database(self):
        """Очищает базу данных от несуществующих файлов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT image_path FROM images')
                paths = cursor.fetchall()
                
                for (path,) in paths:
                    try:
                        self.yadisk.get_meta(path)
                    except:
                        # Если файл не найден, удаляем его из базы
                        cursor.execute('DELETE FROM images WHERE image_path = ?', (path,))
                        logger.info(f"Удален несуществующий файл из базы: {path}")
                
                conn.commit()
                logger.info("База данных очищена от несуществующих файлов")
        except Exception as e:
            logger.error(f"Ошибка при очистке базы данных: {str(e)}")

    async def update_folder_status(self, source_folder, target_folder, new_path, status, processed_at):
        """Обновляет статус папки в базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO folder_status 
                    (source_folder, target_folder, new_path, status, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (source_folder, target_folder, new_path, status, processed_at))
                
                # Обновляем пути в таблице images
                if new_path:
                    self.update_paths_in_database(source_folder, new_path)
                
                logger.info(
                    f"Обновлен статус папки {source_folder}:\n"
                    f"- Целевая папка: {target_folder}\n"
                    f"- Новый путь: {new_path}\n"
                    f"- Статус: {status}\n"
                    f"- Время обработки: {processed_at}"
                )
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса папки {source_folder}: {str(e)}")
            raise

    def get_folder_status(self, folder_path):
        """Получает историю статусов папки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT status, processed_at, target_folder, new_path
                    FROM folder_status
                    WHERE source_folder = ?
                    ORDER BY processed_at DESC
                ''', (folder_path,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении статуса папки {folder_path}: {str(e)}")
            return []

    def get_current_folder_files(self, folder_path):
        """Получает актуальный список файлов в папке"""
        try:
            files = []
            items = self.yadisk.get_meta(folder_path).embedded.items
            for item in items:
                if item.file is not None and item.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    files.append(item.path)
            logger.info(f"Получено {len(files)} файлов из папки {folder_path}")
            return files
        except Exception as e:
            logger.error(f"Ошибка при получении списка файлов из {folder_path}: {str(e)}")
            raise

    def get_similar_files(self, source_folder, target_folder, threshold=91):
        """Получает список файлов с высокой схожестью"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT image_path 
                    FROM images 
                    WHERE folder_path = ? 
                    AND EXISTS (
                        SELECT 1 
                        FROM images i2 
                        WHERE i2.folder_path = ? 
                        AND similarity >= ?
                    )
                ''', (source_folder, target_folder, threshold))
                similar_files = [os.path.basename(row[0]) for row in cursor.fetchall()]
                logger.info(f"Найдено {len(similar_files)} похожих файлов между папками {source_folder} и {target_folder}")
                return similar_files
        except Exception as e:
            logger.error(f"Ошибка при получении похожих файлов: {str(e)}")
            return []

    async def move_file(self, source_path, target_folder):
        """Перемещает файл в указанную папку"""
        try:
            file_name = os.path.basename(source_path)
            new_path = os.path.join(target_folder, file_name)
            
            # Если файл с таким именем уже существует, добавляем timestamp
            try:
                self.yadisk.get_meta(new_path)
                name, ext = os.path.splitext(file_name)
                new_path = f"{target_folder}/{name}_{int(time.time())}{ext}"
            except:
                pass
            
            self.yadisk.move(source_path, new_path)
            logger.info(f"Файл {source_path} перемещен в {new_path}")
            return new_path
        except Exception as e:
            logger.error(f"Ошибка при перемещении файла {source_path}: {str(e)}")
            return None

    async def update_file_location(self, old_path, new_path, new_folder):
        """Обновляет информацию о местоположении файла в базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE images 
                    SET image_path = ?, folder_path = ?
                    WHERE image_path = ?
                ''', (new_path, new_folder, old_path))
                logger.info(f"Обновлено местоположение файла в базе данных: {old_path} -> {new_path}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении местоположения файла в базе данных: {str(e)}")
            return False