import asyncio
import datetime
import time
import traceback
from aiogram import types, F, Router, html, Bot
from aiogram.types import (Message, CallbackQuery,
                           InputFile, FSInputFile,
                            MessageEntity, InputMediaDocument,
                            InputMediaPhoto, InputMediaVideo, Document,
                            ReactionTypeEmoji)
from aiogram.filters import Command, StateFilter,ChatMemberUpdatedFilter

from pprint import pprint
from aiogram.fsm.context import FSMContext

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import re
from dotenv import load_dotenv
import os

from loguru import logger
from workGS import Sheet
# from workSelenium import get_info
# from pars_avito import get_info_avito
load_dotenv()
# TOKEN = os.getenv('SENDER_BOT_TOKEN')

router = Router()

# bot = Bot(token=TOKEN,)

# s=Sheet('profzaboru-5f6f677a3cd8.json','Объекты тест','Объекты')

from loguru import logger
logger.add("logs/parsBot_{time}.log",format="{time} - {level} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")





        
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
from ydWork import YandexDiskManager   # Импортируем менеджер Яндекс Диска
from workBitrix import get_prepare_active_deals, Deal
import postgreWork
load_dotenv()

BOT_TOKEN = os.getenv('PARS_DISK_TOKEN_BOT')
# YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')
APLICATION_ID = os.getenv('APLICATION_ID')
APLICATION_SECRET = os.getenv('APLICATION_SECRET')
TOKEN_YD = os.getenv('TOKEN_YD')

bot = Bot(token=BOT_TOKEN)
# dp = Dispatcher()
# yadisk_manager = YandexDiskManager(token=YANDEX_TOKEN)  # Создаем экземпляр менеджера
# yandexManager=YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD)

Yd=YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD, isTest=False)

from yd_image_similarity import YandexImageSimilarityFinder

class UploadStates(StatesGroup):
    waiting_for_folder = State()
    waiting_for_photos = State()
    get_deal_id=State()
    folder=State()
    waiting_for_new_folder = State()
    confirm_upload = State()
    waiting_for_first_folder = State()
    waiting_for_second_folder = State()
    confirm_move = State()

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from math import ceil



class DealPaginator:
    def __init__(self, deals, page_size=5):
        self.deals = deals
        self.page_size = page_size
        self.total_pages = ceil(len(deals) / page_size)

    def get_page(self, page):
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.deals[start:end], page, self.total_pages

    def get_keyboard(self, current_page):
        builder = InlineKeyboardBuilder()
        
        # Кнопки для сделок
        for deal in self.get_page(current_page)[0]:
            builder.button(text=f"{deal['TITLE']} (ID: {deal['ID']})", callback_data=f"deal:{deal['ID']}")
        builder.adjust(1)
        
        # Кнопки навигации
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"page:{current_page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{current_page}/{self.total_pages}", callback_data="ignore"))
        if current_page < self.total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"page:{current_page+1}"))
        
        # Добавляем навигационные кнопки в конец
        builder.row(*nav_buttons)
        
        return builder.as_markup()

class FolderPaginator:
    def __init__(self, folders, page_size=5):
        self.folders = folders
        self.page_size = page_size
        self.total_pages = ceil(len(folders) / page_size)

    def get_page(self, page):
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.folders[start:end], page, self.total_pages

    def get_keyboard(self, current_page):
        builder = InlineKeyboardBuilder()
        
        # Кнопки для папок
        for folder in self.get_page(current_page)[0]:
            builder.button(text=folder, callback_data=f"folder:{folder}")
        builder.adjust(1)
        
        # Кнопка для создания новой папки
        builder.button(text="Создать новую папку", callback_data="new_folder")
        builder.adjust(1) 
        # Кнопки навигации
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton(text="◀️ Наза", callback_data=f"folderpage:{current_page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{current_page}/{self.total_pages}", callback_data="ignore"))
        if current_page < self.total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"folderpage:{current_page+1}"))
        
        # Добавляем навигационные кнопки в конец
        builder.row(*nav_buttons)
        
        return builder.as_markup()

@router.message(Command("reinstart"))
async def cmd_start(message: types.Message):
    try:
        # postgreWork.add_new_user(
        #     userID=message.from_user.id,
        #     nickname=message.from_user.username
        # )
        
        # Создаем finder и очищаем базу при старте
        message.answer("Калибровка базы")
        finder = YandexImageSimilarityFinder(bins=16)
        finder.cleanup_database()
        message.answer("Калибровка завершина")
    except Exception as e:
        logger.error(f"Ошибка при инициализации: {str(e)}")

@router.message(Command('delete_folder'))
async def delete_folder_in_db(message: types.Message):
    # удаляем папку с отправленым путем из базы /Производственный отдел/разобрать
    folder_path = message.text.replace('/delete_folder', '').strip()
    finder = YandexImageSimilarityFinder(bins=16)
    finder.delete_folder_from_database(folder_path)
    await message.answer("Папка удалена из базы")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Загрузить фото")],
            [KeyboardButton(text="Сравнить папки")]
        ], 
        resize_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)
    return 0

def is_yandex_link(text):
    """Проверяет, является ли текст ссылкой на Яндекс.Диск"""
    return text.startswith(('https://disk.yandex.ru/', 'https://yadi.sk/'))

def process_folder_path(path):
    """Обрабатывает путь к папке, добавляя 'Производственный отдел/' если нужно"""
    special_folders = {
        'Разобрать': 'Производственный отдел/Разобрать',
        'BBase': 'Производственный отдел/BBase 🗄',
        # Добавьте другие специальные папки при необходимости
    }
    
    # Если введено название специальной папки
    if path in special_folders:
        return special_folders[path]
    
    # Если путь уже начинается с 'Производственный отдел'
    if path.startswith('Производственный отдел'):
        return path
    
    # Если это полный путь, начинающийся с '/'
    if path.startswith('/'):
        return path.lstrip('/')
    
    # В остальных случаях возвращаем уть как есть
    return path

@router.message(F.text == "Сравнить папки")
async def compare_folders_start(message: types.Message, state: FSMContext):
    await message.answer("Отправьте ссылку на первую папку Яндекс.Диска:")
    await state.set_state(UploadStates.waiting_for_first_folder)

@router.message(UploadStates.waiting_for_first_folder)
async def process_first_folder(message: types.Message, state: FSMContext):
    folder_input = message.text
    finder = YandexImageSimilarityFinder(bins=16)
    
    try:
        # Нормализуем путь или обрабатываем ссылку
        if finder.is_yandex_link(folder_input):
            folder_meta = finder.yadisk.get_public_meta(folder_input)
            folder_path = os.path.join(finder.pathMain, folder_meta.name)
            folder_link = folder_input
        else:
            # Если передан путь
            folder_path = finder.normalize_path(folder_input)
            try:
                folder_meta = finder.yadisk.get_meta(folder_path)
                folder_link = finder.get_public_link(folder_path)
            except Exception as e:
                await message.answer(f"Ошибка при доступе к папке по пути {folder_path}: {str(e)}")
                await state.clear()
                return
        
        await message.answer(f"📂 Полный путь к папке:\n{folder_path}", parse_mode='HTML')
        
        # Сохраняем информацию о первой папке
        await state.update_data(
            finder=finder,
            first_folder_link=folder_link,
            first_folder_path=folder_path
        )
        
        await message.answer("Отправьте ссылку или путь ко второй папке для сравнения:")
        await state.set_state(UploadStates.waiting_for_second_folder)
            
    except Exception as e:
        await message.answer(f"Ошибка при доступе к папке: {str(e)}")
        await state.clear()

@router.message(UploadStates.waiting_for_second_folder)
async def process_second_folder(message: types.Message, state: FSMContext):
    folder_input = message.text
    data = await state.get_data()
    finder = data['finder']
    first_folder_path = data['first_folder_path']
    first_folder_link = data['first_folder_link']
    
    try:
        if finder.is_yandex_link(folder_input):
            folder_meta = finder.yadisk.get_public_meta(folder_input)
            second_folder_path = os.path.join(finder.pathMain, folder_meta.name)
            folder_link = folder_input
        else:
            second_folder_path = finder.normalize_path(folder_input)
            try:
                folder_meta = finder.yadisk.get_meta(second_folder_path)
                folder_link = finder.get_public_link(second_folder_path)
            except Exception as e:
                await message.answer(f"Ошибка при доступе к папке по пути {second_folder_path}: {str(e)}")
                await state.clear()
                return
        
        logger.info(f"📂 Полный путь к папке: {second_folder_path}")
        await message.answer(f"📂 Полный путь к папке:\n{second_folder_path}", parse_mode='HTML')
        
        status_message = await message.answer("⏳ Проверяю наличие папок в базе...")
        
        # Проверяем наличие папок в базе
        first_folder_exists = finder.is_folder_in_database(first_folder_path)
        second_folder_exists = finder.is_folder_in_database(second_folder_path)
        
        logger.info(f"Первая папка {first_folder_path}: {'найдена' if first_folder_exists else 'не найдена'} в базе")
        logger.info(f"Вторая папка {second_folder_path}: {'найдена' if second_folder_exists else 'не найдена'} в базе")
        
        scan_success = True
        
        if not first_folder_exists:
            await status_message.edit_text(f"Первая папка не найдена в базе, начинаю сканирование...")
            progress_text = "Сканирую первую папку:\n[□□□□□□□□□□] 0% (осталось: --)"
            await status_message.edit_text(progress_text)
            
            # Создаем nonlocal переменную для хранения времени начала
            progress_state = {'start_time': time.time()}

            async def update_progress(current, total, estimated_time):
                nonlocal progress_state
                #обновляем прогресс только если прошло больше 1 минуты
                if time.time() - progress_state['start_time'] > 60:
                    progress_state['start_time'] = time.time()
                    progress = int((current / total) * 10)
                    progress_bar = "■" * progress + "□" * (10 - progress)
                    percentage = int((current / total) * 100)
                    progress_text = f"Сканирую первую папку:\n[{progress_bar}] {percentage}%\nОсталось примерно: {estimated_time}"
                    await status_message.edit_text(progress_text)
            
            if first_folder_path.startswith('/'):
                scan_success = await finder.scan_directory_async(first_folder_path, update_progress, first_folder_path)
            else:
                scan_success = await finder.scan_directory_async(first_folder_link, update_progress)
            
            if not scan_success:
                await status_message.edit_text("❌ Ошибка при сканировании первой папки")
                await state.clear()
                return
            await status_message.edit_text("Первая папка отсканирована ✅")
            # Проверяем еще раз после сканирования
            first_folder_exists = finder.is_folder_in_database(first_folder_path)
            logger.info(f"Повторная проверка первой папки: {'найдена' if first_folder_exists else 'не найдена'}")
        
        if not second_folder_exists:
            await status_message.edit_text(f"Вторая папка не найдена в базе, ачинаю сканирование...")
            progress_text = "Сканирую вторую папку:\n[□□□□□□□□□□] 0% (осталось: --)"
            await status_message.edit_text(progress_text)
            
            # Создаем nonlocal переменную для хранения времени начала
            progress_state = {'start_time': time.time()}

            async def update_progress(current, total, estimated_time):
                nonlocal progress_state
                #обновляем прогресс только если прошло больше 1 минуты
                if time.time() - progress_state['start_time'] > 60:
                    progress_state['start_time'] = time.time()
                    progress = int((current / total) * 10)
                    progress_bar = "■" * progress + "□" * (10 - progress)
                    percentage = int((current / total) * 100)
                    progress_text = f"Сканирую вторую папку:\n[{progress_bar}] {percentage}%\nОсталось примерно: {estimated_time}"
                    await status_message.edit_text(progress_text)

            if second_folder_path.startswith('/'):
                scan_success = await finder.scan_directory_async(second_folder_path, update_progress, second_folder_path)
            else:
                scan_success = await finder.scan_directory_async(folder_link, update_progress)
            
            
            if not scan_success:
                await status_message.edit_text("❌ Ошибка при сканировании второй папки")
                await state.clear()
                return
            await status_message.edit_text("Вторая папка отсканирована ✅")
            # Проверяем еще раз после сканирования
            second_folder_exists = finder.is_folder_in_database(second_folder_path)
            logger.info(f"Повторная проверка второй папки: {'найдена' if second_folder_exists else 'не найдна'}")
        
        # Проверяем еще раз наличие папок в базе
        if not first_folder_exists or not second_folder_exists:
            error_text = "❌ Ошибка: "
            if not first_folder_exists:
                error_text += "первая папка не найдена в базе. "
            if not second_folder_exists:
                error_text += "вторая папка не найдена в базе. "
            await status_message.edit_text(error_text)
            await state.clear()
            return
        
        await status_message.edit_text("🔍 Ищу похожие фотографии...")
        # Ищем похожие фотографии
        similar_photos = finder.compare_folders(first_folder_path, second_folder_path)
        
        if similar_photos:
            # Группируем похожие фото по папкам
            folders_with_similar = {}
            for match in similar_photos:
                folder_path = os.path.dirname(match['full_path1'])
                if folder_path not in folders_with_similar:
                    folders_with_similar[folder_path] = {
                        'similar': [],
                        'all_files': [],
                        'similarity_groups': {}
                    }
                folders_with_similar[folder_path]['similar'].append(match)
                
                # Группируем по схожести
                similarity = round(match['similarity'], 2)
                if similarity not in folders_with_similar[folder_path]['similarity_groups']:
                    folders_with_similar[folder_path]['similarity_groups'][similarity] = []
                folders_with_similar[folder_path]['similarity_groups'][similarity].append(match)
            
            # Отправляем общую сводку
            summary_text = (
                f"📊 Найдено {len(similar_photos)} похожих фотографий "
                f"в {len(folders_with_similar)} папках\n"
            )
            await message.answer(summary_text)
            
            sent_messages = []
            folder_mapping = {}
            
            # Отправляем информацию о каждой папке отдельным сообщением
            for idx, (folder_path, folder_data) in enumerate(folders_with_similar.items(), 1):
                # Получаем все файлы из папки
                all_files = finder.get_all_files_from_folder(folder_path, set())
                folder_data['all_files'] = all_files
                
                # Сохраняем маппинг для папки
                folder_id = f"f{idx}"
                folder_mapping[folder_id] = {
                    'source_path': folder_path,
                    'target_path': second_folder_path
                }
                
                # Отправляем информацию о папке
                sent_msg = await send_folder_info(
                    message, 
                    finder,
                    folder_path, 
                    folder_data, 
                    idx, 
                    second_folder_path,
                    state  # Добавляем state в аргументы
                )
                sent_messages.append(sent_msg.message_id)
            
            # Добавляем кнопку отмены после всех сообщений
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="❌ Удалить все сообщения", callback_data="clear_all")
            keyboard.adjust(1)
            
            clear_message = await message.answer(
                "💡 Нажмите кнопку ниже, чтобы удалить все предыдущие сообщения",
                reply_markup=keyboard.as_markup()
            )
            sent_messages.append(clear_message.message_id)
            
            # Сохраняем все необходимые данные в state
            await state.update_data({
                'finder': finder,
                'first_folder_link': first_folder_link,
                'first_folder_path': first_folder_path,
                'second_folder_path': second_folder_path,
                'folders_with_similar': folders_with_similar,
                'folder_mapping': folder_mapping,
                'sent_messages': sent_messages
            })
            
        else:
            if status_message:
                await status_message.edit_text("Похожих фотографий не найдено")
            else:
                await message.answer("Похожих фотграфий не найдено")
            await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при сравнении папок: {str(e)}, {traceback.print_exc()}")
        
        await message.answer(f"Ошибка при сравнении папок: {str(e)}", parse_mode='HTML')
        await state.clear()

@router.callback_query(UploadStates.confirm_move, lambda c: c.data.startswith('move:'))
async def move_files_from_folder(callback: types.CallbackQuery, state: FSMContext):
    folder_id = callback.data.split(':')[1]
    data = await state.get_data()
    finder = data['finder']
    folders_with_similar = data['folders_with_similar']
    folder_mapping = data['folder_mapping']
    sent_messages = data.get('sent_messages', [])  # Получаем список ID отправленных сообщений
    
    folder_info = folder_mapping.get(folder_id)
    if not folder_info:
        await callback.message.answer("Ошибка: папка не найдена")
        return
    
    source_folder = folder_info['source_path']
    target_base_folder = folder_info['target_path']
    
    folder_data = folders_with_similar[source_folder]
    
    # Создаем маппинг подпапок на основе похожих файлов
    subfolder_mapping = {}
    for match in folder_data['similar']:
        source_file = match['full_path1']
        target_file = match['full_path2']
        source_subfolder = os.path.dirname(source_file)
        target_subfolder = os.path.dirname(target_file)
        subfolder_mapping[source_subfolder] = target_subfolder
    
    await callback.message.edit_text(
        f"Анализирую структуру папок:\n"
        f"Из: {os.path.basename(source_folder)}\n"
        f"В: {os.path.basename(target_base_folder)}"
    )
    
    # Группируем файлы по подпапкам
    files_by_subfolder = {}
    similar_files = set(m['file1'] for m in folder_data['similar'])
    
    for file_path in folder_data['all_files']:
        if os.path.basename(file_path) not in similar_files:
            source_subfolder = os.path.dirname(file_path)
            if source_subfolder not in files_by_subfolder:
                files_by_subfolder[source_subfolder] = []
            files_by_subfolder[source_subfolder].append(file_path)
    
    total_files = sum(len(files) for files in files_by_subfolder.values())
    await callback.message.edit_text(f"Начинаю перенос {total_files} файлов...")
    
    success_count = 0
    status_text = ""
    
    # Переносим файлы с сохранением структуры папок
    for source_subfolder, files in files_by_subfolder.items():
        target_subfolder = subfolder_mapping.get(source_subfolder)
        if not target_subfolder:
            # Если нет соответствующей подпапки, создаем аналогичную структуру в целевой папке
            relative_path = os.path.relpath(source_subfolder, source_folder)
            target_subfolder = os.path.join(target_base_folder, relative_path)
        
        subfolder_status = (
            f"\nПереношу файлы:\n"
            f"Из: {os.path.basename(source_subfolder)}\n"
            f"В: {os.path.basename(target_subfolder)}"
        )
        subfolder_success = 0
        
        for file_path in files:
            try:
                if finder.move_file(file_path, target_subfolder):
                    success_count += 1
                    subfolder_success += 1
            except Exception as e:
                logger.error(f"Ошибка при переносе файла {file_path}: {str(e)}")
        
        subfolder_status += f"\nПеренесено: {subfolder_success} из {len(files)}"
        status_text += subfolder_status
        
        if len(status_text) > 3000:
            await callback.message.edit_text(f"Прогресс переноса:\n{status_text}")
            status_text = ""
    
    if status_text:
        await callback.message.edit_text(f"Прогресс переноса:\n{status_text}")
    
    # Удаляем все предыдущие сообщения
    for message_id in sent_messages:
        try:
            await bot.delete_message(callback.message.chat.id, message_id)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {message_id}: {str(e)}")
    
    # Удаляем сообщение с кнопками
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения с кнопками: {str(e)}")
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Загрузить фото")],
            [KeyboardButton(text="Сравнить папки")]
        ], 
        resize_keyboard=True
    )
    
    final_message = (
        f"Перенос завершен\n"
        f"Всего перенесено: {success_count} из {total_files} файлов\n"
        f"Структура папок сохранена"
    )
    
    await callback.message.answer(final_message, reply_markup=keyboard)
    # await state.clear()

@router.message(F.text == "Загрузить фото")
async def upload_photos(message: types.Message, state: FSMContext):
    # Инициализируем YandexImageSimilarityFinder
    finder = YandexImageSimilarityFinder(bins=16)
    
    # Сохраняем finder в состоянии
    await state.update_data(finder=finder, photos=[], similar_folders={})
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Завершить добавление фото")]], 
        resize_keyboard=True
    )
    await message.answer("Отправляйте фотографии. Когда закончите, нажмите 'Завершить добавление фото'", 
                        reply_markup=keyboard)
    await state.set_state(UploadStates.waiting_for_photos)

@router.message(UploadStates.waiting_for_photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    finder = data['finder']
    
    # Сохраняем фото
    photo = message.photo[-1]
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    # Скачиваем файл
    local_path = f'photos/{file_id}.jpg'
    await bot.download_file(file_path, local_path)
    
    # Добавляе путь к файлу в список
    photos.append(local_path)
    
    # Проверяем на схожесть
    results = finder.check_local_image(local_path)
    if results:
        similar_folders = data.get('similar_folders', {})
        for match in results:
            folder = match['folder']
            if folder not in similar_folders:
                similar_folders[folder] = []
            similar_folders[folder].append({
                'file': match['file'],
                'similarity': match['similarity'],
                'local_path': local_path
            })
        await state.update_data(similar_folders=similar_folders)
    
    await state.update_data(photos=photos)
    await message.react(reaction=[ReactionTypeEmoji(emoji='👍')])

@router.message(UploadStates.waiting_for_photos, F.text == "Завершить добавление фото")
async def finish_adding_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    similar_folders = data.get('similar_folders', {})
    
    if not photos:
        await message.answer("Вы не отправили ни одной ф��тографии.")
        return
    
    if similar_folders:
        # Есть похожие фотографии
        text = "Найдены похожие фотографии в следующих папках:\n\n"
        keyboard = InlineKeyboardBuilder()
        
        # Сохраняем маппинг индексов к папкам
        folder_mapping = {}
        
        for idx, (folder, matches) in enumerate(similar_folders.items(), 1):
            folder_mapping[str(idx)] = folder
            text += f"{idx}. Папка: {folder}\n"
            text += "Найденные совпадения:\n"
            folderNameToButton=folder.split('/')[-1]
            for match in matches:
                # text += f"  - {match['file']} (схожесть: {match['similarity']:.2f}%)\n"
                text += f"  - (схожесть: {match['similarity']:.2f}%)\n"
            # keyboard.button(text=f"Папка {idx}", callback_data=f"up:{idx}")
            keyboard.button(text=f"Папка {folderNameToButton}", callback_data=f"up:{idx}")
        
        # Сохраняем маппинг в состоянии
        await state.update_data(folder_mapping=folder_mapping)
        
        keyboard.button(text="Новая папка", callback_data="new_folder")
        keyboard.adjust(1)
        
        await message.answer(text, reply_markup=keyboard.as_markup())
    else:
        # Нет похожи фотографий
        await message.answer("Похожих фотографий не найдено. Хотите создать новую папку?",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                               [InlineKeyboardButton(text="Да", callback_data="new_folder")],
                               [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
                           ]))
    
    await state.set_state(UploadStates.confirm_upload)

@router.callback_query(UploadStates.confirm_upload, lambda c: c.data.startswith('up:'))
async def upload_to_existing_folder(callback: types.CallbackQuery, state: FSMContext):
    folder_idx = callback.data.split(':')[1]
    data = await state.get_data()
    folder_mapping = data.get('folder_mapping', {})
    target_folder = folder_mapping.get(folder_idx)
    
    if not target_folder:
        await callback.message.answer("Ошибка: папка не найдена")
        return
    
    photos = data['photos']
    finder = data['finder']
    
    await callback.message.edit_text(f"Загружаю фотографии в папку...")
    
    success_count = 0
    for photo_path in photos:
        if finder.upload_to_folder(photo_path, target_folder):
            success_count += 1
            os.remove(photo_path)  # Удаляем локальный фйл после загрузки
    
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
    await callback.message.answer(
        f"Загружено {success_count} из {len(photos)} фотографий", keyboard=keyboard
    )
    # await state.clear()
    return 0

@router.callback_query(lambda c: c.data == "cancel")
async def cancel_upload(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    sent_messages = data.get('sent_messages', [])
    
    # Удаляем временные файлы
    for photo_path in photos:
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    # Удаляем отправленные сообщения
    for message_id in sent_messages:
        try:
            await bot.delete_message(callback.message.chat.id, message_id)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {message_id}: {str(e)}")
    
    # Удаляем сообщение с кнопками
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения с кнопками: {str(e)}")
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Загрузить фото")],
            [KeyboardButton(text="Сравнить папки")]
        ], 
        resize_keyboard=True
    )
    await callback.message.answer("Загрузка отменена", reply_markup=keyboard)
    # await state.clear()

@router.callback_query(lambda c: c.data.startswith('page:'))
async def process_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split(':')[1])
    data = await state.get_data()
    paginator = data['paginator']
    
    await callback_query.message.edit_reply_markup(reply_markup=paginator.get_keyboard(page))


@router.callback_query(lambda c: c.data.startswith('deal:'))
async def process_deal_selection(callback_query: types.CallbackQuery, state: FSMContext):
    deal_id = callback_query.data.split(':')[1]
    data = await state.get_data()
    deals = data['deals']
    # a=data['folder'] 
    # pprint(a)
    selected_deal = next((deal for deal in deals.values() if str(deal['ID']) == deal_id), None)
    if selected_deal:
        await state.update_data(selected_deal=selected_deal)
        
        # Получаем список папок
        pprint(selected_deal)
        try:
            folders = Yd.get_all_folders(selected_deal[Deal.urlFolder])
        except:
            await callback_query.message.answer(f"Не удалось найти папку по пути {Yd.pathMain} \nпроверте корректность ссылки в сделке (https://yadi.sk/d/_6GQU5TALotu1Q) и \nрасположение папки проекта на диске")

        folder_paginator = FolderPaginator(folders)
        
        await state.update_data(folder_paginator=folder_paginator, dealUrlFolder=selected_deal[Deal.urlFolder])
        await callback_query.message.edit_text("Выберите существующую папку или создайте новую:", reply_markup=folder_paginator.get_keyboard(1))
        await state.set_state(UploadStates.waiting_for_folder)
    else:
        await callback_query.message.answer("Произошла ошибка при выборе сделки. Попробуйте ее раз.")

    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith('folderpage:'))
async def process_folder_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split(':')[1])
    data = await state.get_data()
    folder_paginator = data['folder_paginator']
    
    await callback_query.message.edit_reply_markup(reply_markup=folder_paginator.get_keyboard(page))


@router.callback_query(lambda c: c.data.startswith('folder:'))
async def process_folder_selection(callback_query: types.CallbackQuery, state: FSMContext):
    folder = callback_query.data.split(':')[1]
    data = await state.get_data()
    selected_deal = data['selected_deal']
    
    await state.update_data(folder=folder)
    await callback_query.message.answer(f"Вы выбрали папку: {folder}\nТеперь отправьте фотографии (можно несколько):")
    
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Завершить загрузку")]], resize_keyboard=True)
    await callback_query.message.answer("Вы можете отправить фотографии или нажать кнопку ниже, чтобы завершить агрузку.", reply_markup=keyboard)
    await state.set_state(UploadStates.waiting_for_photos)


@router.callback_query(lambda c: c.data == "new_folder")
async def create_new_folder(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название новой папки:")
    await state.set_state(UploadStates.waiting_for_new_folder)

@router.message(UploadStates.waiting_for_new_folder)
async def process_new_folder(message: types.Message, state: FSMContext):
    new_folder = message.text
    data = await state.get_data()
    finder = data['finder']
    photos = data['photos']
    
    # Создаем полный путь к новй папке
    new_folder_path = os.path.join(finder.pathMain, 'ТЕСТИРУЕМ БОТА - 1', new_folder)
    
    try:
        # Создаем папку на Яндекс.Диске и получаем публичную ссылку
        folder_path, public_url = Yd.create_folder(new_folder_path)
        await message.answer(
            f"Создана новая папка:\nПуть: {folder_path}\nПубличная ссылка: {public_url}"
        )
        
        # Загружаем все фотографии
        success_count = 0
        for photo_path in photos:
            if finder.upload_to_folder(photo_path, folder_path):
                success_count += 1
                os.remove(photo_path)  # Удаляем лоальный файл осле загрузки
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Загрузить фото")]], 
            resize_keyboard=True
        )
        await message.answer(
            f"Загружено {success_count} из {len(photos)} фотографий в новую папку",
            reply_markup=keyboard
        )
    except Exception as e:
        await message.answer(f"Ошибка при создании папки: {str(e)}")
    
    # await state.clear()

@router.message(UploadStates.waiting_for_photos)
async def process_non_photo(message: types.Message):
    await message.answer("Пожалуйста, отправьте фото или нажмите 'Завершить загрузку', чтобы закончить.")
    return 0

# @router.message(UploadStates.waiting_for_photos, F.text == "Завершить загрузку")
# async def finish_upload(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     pprint(data)
#     folder = data['folder']
#     photos = data['photos']

#     # Загружаем все собранные фотографии на Яндекс Диск
#     # for downloaded_file in photos:
#     #     filename = f"{downloaded_file.file_id}.jpg"  # Или используйте дру��ой способ генерации имени
#     #     yadisk_path = f"/{folder}/{filename}"
#     #     yadisk_manager.upload_file(downloaded_file, yadisk_path)
#     pprint(photos)
#     await message.answer(f"Все фото успешно загружены на Яндекс.Диск в папку '{folder}'")
#     await state.clear()  # Завершаем состояние
#     return 0
# async def main():
#     await router.start_polling(bot)


async def send_folder_info(message: types.Message, finder, folder_path, folder_data, idx, second_folder_path, state: FSMContext):
    """Отправляет информацию о папке с кнопками управления"""
    # Получаем публичные ссылки на папки
    folder_url = finder.get_public_link(folder_path)
    target_folder_url = finder.get_public_link(second_folder_path)
    
    folder_name = os.path.basename(folder_path)
    target_folder_name = os.path.basename(second_folder_path)
    
    # Проверяем, все ли файлы имеют 100% совпадение
    all_perfect_match = all(
        match['similarity'] == 100.0 
        for match in folder_data['similar']
    )
    
    # Получаем общее количество файлов в папке
    total_files = len(folder_data['all_files'])
    
    # Разделяем совпадения на высокие (>=91%) и низкие (<91%)
    high_matches = []
    low_matches = []
    for match in folder_data['similar']:
        if match['similarity'] >= 98:
            high_matches.append(match)
        else:
            low_matches.append(match)

    target_subfolder = os.path.dirname(match['full_path2'])
    subfolder_name = os.path.basename(target_subfolder)
    
    folder_text = f"📁 Папка: [{folder_name}]({folder_url}) ({total_files})\n"
    folder_text += f"Сравнение с папкой [{subfolder_name}]({finder.get_public_link(target_subfolder)}):\n\n"
    folder_text += "Найденные совпадения:\n"
    
    # Группируем высокие совпадения по схожести
    similarity_groups = {}
    for match in high_matches:
        similarity = round(match['similarity'], 2)
        if similarity not in similarity_groups:
            similarity_groups[similarity] = []
        similarity_groups[similarity].append(match)
    
    countHighMatches = 0
    # Выводим информацию о высоких совпадениях
    for similarity, matches in sorted(similarity_groups.items(), reverse=True):
        if len(matches) > 1:
            folder_text += f"  - (схожесть: {similarity:.2f}%) ({len(matches)} шт)\n"
            countHighMatches += len(matches)
            continue
        else:
            match = matches[0]
            file_url = finder.get_public_link(match['full_path2'])
            folder_text += f"  - (схожесть: {similarity:.2f}%) на [фото]({file_url})\n"
        countHighMatches += 1
    # Добавляем информацию о файлах с низкой схожестью
    if countHighMatches < total_files:
        folder_text += f"\nДругие ({total_files-countHighMatches}) похожи менее 91%\n"
    
    # Создаем клавиатуру для папки
    keyboard = InlineKeyboardBuilder()
    
    # Сокращаем длинные названия папок
    def truncate_name(name, max_length=20):
        return f"{name[:max_length]}..." if len(name) > max_length else name
    
    source_name = truncate_name(os.path.basename(folder_path))
    target_name = truncate_name(os.path.basename(target_subfolder))  # Используем имя целевой подпапки
    
    # Подсчитываем количество непохожих файлов и файлов с низкой схожестью
    similar_files = set(m['file1'] for m in folder_data['similar'])
    high_similarity_files = set(m['file1'] for m in folder_data['similar'] if m['similarity'] >= 91)
    
    # Файлы для переноса - это файлы с низкой схожестью и непохожие файлы
    files_to_move = len([f for f in folder_data['all_files'] 
                        if os.path.basename(f) not in high_similarity_files])
    
    # Сохраняем информацию о целевой подпапке в folder_mapping
    folder_id = f"f{idx}"
    folder_mapping = {
        # folder_id: {
            "mainFolder": folder_path,
            "secondFolder": target_subfolder  # Используем target_subfolder из найденного совпадения
        # }
    }
    
    # Обновляем state с новым folder_mapping
    state_data = await state.get_data()
    if 'folder_mapping_move' not in state_data:
        state_data['folder_mapping_move'] = {}
    state_data['folder_mapping_move'][folder_id] = folder_mapping
    await state.update_data(**state_data)
    
    if all_perfect_match and countHighMatches == 0:
        keyboard.button(text="✅Завершить работу", callback_data=f"finish:{idx}")
    else:
        # Если есть файлы для переноса
        if files_to_move > 0:
            # Если есть и похожие, и непохожие файлы
            if len(high_similarity_files) > 0:
                keyboard.button(
                    text=f"➡️ Перенести остальные ({files_to_move} шт)", 
                    callback_data=f"move:{idx}"
                )
                keyboard.button(
                    text=f"➡️ Перенести в {target_name}", 
                    callback_data=f"move_all:{idx}"
                )
            else:
                # Если есть только непохожие файлы
                keyboard.button(
                    text=f"➡️ Перенести в {target_name}", 
                    callback_data=f"move:{idx}"
                )
            keyboard.button(text="👋 Вручную", callback_data=f"manual:{idx}")
    
    keyboard.button(text="✅ Папка разобрана", callback_data=f"done:{idx}")
    keyboard.adjust(1)
    
    return await message.answer(
        folder_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(lambda c: c.data.startswith('done:'))
async def process_folder_done(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Папка разобрана'"""
    try:
        folder_idx = callback.data.split(':')[1]
        data = await state.get_data()
        
        # Безопасное получение данных из state
        finder = data.get('finder')
        folder_mapping = data.get('folder_mapping', {})
        
        if not finder or not folder_mapping:
            logger.error(f"Отсутствуют необходимые данные в state: {data}")
            await callback.message.edit_text("Ошибка: данные сессии утеряны")
            # await state.clear()
            return
        
        folder_info = folder_mapping.get(f"f{folder_idx}")
        if not folder_info:
            await callback.message.edit_text("Ошибка: папка не найдена")
            return
        
        source_folder = folder_info['source_path']
        target_folder = folder_info['target_path']
        
        try:
            source_folder_name = os.path.basename(source_folder)
            await finder.add_folder_tag(target_folder, source_folder_name)

            completed_folder = os.path.join(os.path.dirname('/Производственный отдел/BBase/'), 'завершено') 
            # completed_folder = os.path.join(os.path.dirname(source_folder), 'завершено')
            if not finder.folder_exists(completed_folder):
                finder.create_folder(completed_folder)
            
            new_path = await finder.move_folder(source_folder, completed_folder)
            
            await finder.update_folder_status(
                source_folder=source_folder,
                target_folder=target_folder,
                new_path=new_path,
                status='completed',
                processed_at=datetime.datetime.now()
            )
            
            tags = finder.get_folder_tags(target_folder)
            tags_str = ", ".join(tags) if tags else "нет тегов"
            
            await callback.message.edit_text(
                f"✅ Папка {source_folder_name} обработана:\n"
                f"- Добавлен тег в базу данных\n"
                f"- Папка перемещена в 'завершено'\n"
                f"- Теги целевой папки: {tags_str}"
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке папки {source_folder}: {str(e)}")
            await callback.message.edit_text(f"Ошибка при обработке папки: {str(e)}")
        
        # await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в process_folder_done: {str(e)}")
        await callback.message.edit_text("Произошла ошибка при обработке")
        # await state.clear()

@router.callback_query(lambda c: c.data.startswith('finish:'))
async def process_folder_finish(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Завершить работу'"""
    try:
        folder_idx = callback.data.split(':')[1]
        data = await state.get_data()
        
        # Безопасное получение данных из state
        finder = data.get('finder')
        folder_mapping = data.get('folder_mapping', {})
        
        if not finder or not folder_mapping:
            logger.error(f"Отсутствуют необходимые данные в state: {data}")
            await callback.message.edit_text("Ошибка: данные сессии утеряны")
            # await state.clear()
            return
        
        folder_info = folder_mapping.get(f"f{folder_idx}")
        if not folder_info:
            await callback.message.edit_text("Ошибка: папка не найдена")
            return
        
        source_folder = folder_info['source_path']
        target_folder = folder_info['target_path']
        
        try:
            source_folder_name = os.path.basename(source_folder)
            
            await finder.add_folder_tag(target_folder, source_folder_name)
            
            # target_folder='/Производственный отдел/BBase/завершено'
            completed_folder = os.path.join(os.path.dirname('/Производственный отдел/BBase/'), 'завершено')
            if not finder.folder_exists(completed_folder):
                finder.create_folder(completed_folder)
            

            await finder.move_folder(source_folder, completed_folder)
            
            await callback.message.edit_text(
                f"✅ Работа с папкой {source_folder_name} завершена", 
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при завершении работы с папкой {source_folder}: {str(e)}")
            await callback.message.edit_text(f"Ошибка при завершении работы: {str(e)}")
        
        # await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в process_folder_finish: {str(e)}")
        await callback.message.edit_text("Произошла ошибка при обработке")
        # await state.clear()

@router.callback_query(lambda c: c.data.startswith('manual:'))
async def process_folder_manual(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Я буду работать вручную'"""
    try:
        folder_idx = callback.data.split(':')[1]
        data = await state.get_data()
        
        # Безопасное получение данных из state
        finder = data.get('finder')
        folder_mapping = data.get('folder_mapping', {})
        
        if not finder or not folder_mapping:
            logger.error(f"Отсутствуют необходимые данные в state: {data}")
            await callback.message.edit_text("Ошибка: данные сессии утеряны")
            # await state.clear()
            return
        
        folder_info = folder_mapping.get(f"f{folder_idx}")
        if not folder_info:
            await callback.message.edit_text("Ошибка: папка не найдена")
            return
        
        source_folder = folder_info['source_path']
        target_folder = folder_info['target_path']
        
        try:
            # Получаем публичные ссылки на папки
            source_url = finder.get_public_link(source_folder)
            target_url = finder.get_public_link(target_folder)
            
            # Получаем названия папок
            source_name = os.path.basename(source_folder)
            target_name = os.path.basename(target_folder)
            
            # Создаем клавиатуру с кнопкой "Папка разобрана"
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="Папка разобрана", callback_data=f"done:{folder_idx}")
            keyboard.adjust(1)
            
            # Сохраняем данные в state перед отправкой нового сообщения
            await state.update_data({
                'finder': finder,
                'folder_mapping': folder_mapping,
                'source_folder': source_folder,
                'target_folder': target_folder
            })
            
            await callback.message.edit_text(
                f"👌 Вы работаете в папках:\n"
                f"[{source_name}]({source_url}) и [{target_name}]({target_url})",
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при получении информации о папках: {str(e)}")
            await callback.message.edit_text(f"Ошибка при получении информации о папках: {str(e)}")
    
    except Exception as e:
        logger.error(f"Ошибка в process_folder_manual: {str(e)}")
        await callback.message.edit_text("Произошла ошибка при обработке")
        # await state.clear()

@router.callback_query(lambda c: c.data.startswith('move:'))
async def move_remaining_files(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Перенести остальные'"""
    try:
        folder_idx = callback.data.split(':')[1]
        data = await state.get_data()
        finder = data['finder']
        folder_mapping = data['folder_mapping']
        folders_with_similar = data['folders_with_similar']
        folder_mapping_move = data['folder_mapping_move'][f'f{folder_idx}'] 
        folder_info = folder_mapping.get(f"f{folder_idx}")
        if not folder_info:
            await callback.message.edit_text("Ошибка: папка не найдена")
            return
        
        source_folder = folder_mapping_move['mainFolder']
        target_folder = folder_mapping_move['secondFolder']
        
        await callback.message.edit_text("Получаю актуальный список файлов...")
        
        # Получаем актуальный список файлов из исходной папки
        current_files = finder.get_current_folder_files(source_folder)
        
        # Получаем список файлов для переноса (исключаем похожие)
        similar_files = set(m['file1'] for m in folders_with_similar[source_folder]['similar'])
        files_to_move = [f for f in current_files if os.path.basename(f) not in similar_files]
        
        if not files_to_move:
            await callback.message.edit_text("Нет файлов для переноса")
            return
        
        await callback.message.edit_text(f"Переношу {len(files_to_move)} файлов...")
        
        success_count = 0
        for file_path in files_to_move:
            try:
                # Добавляем await перед вызовом асинхронного метода
                if await finder.move_file(file_path, target_folder):
                    success_count += 1
            except Exception as e:
                logger.error(f"Ошибка при переносе файла {file_path}: {str(e)}")
        
        await finder.update_folder_status(
            source_folder=source_folder,
            target_folder=target_folder,
            new_path=None,
            status='files_moved',
            processed_at=datetime.datetime.now()
        )
        
        await callback.message.edit_text(
            f"✅ Перенесено {success_count} из {len(files_to_move)} файлов\n"
            f"Из папки: {os.path.dirname(source_folder)}/[{os.path.basename(source_folder)}]({finder.get_public_link(source_folder)})\n"
            f"В папку: {os.path.dirname(target_folder)}/[{os.path.basename(target_folder)}]({finder.get_public_link(target_folder)})"
        )
        
    except Exception as e:
        error_message = f"Ошибка при переносе файлов"
        logger.error(f"{error_message}: {str(e)}")
        await callback.message.edit_text(error_message)

@router.callback_query(lambda c: c.data == "clear_all")
async def clear_all_messages(callback: types.CallbackQuery, state: FSMContext):
    """Удаляет все предыдущие сообщения"""
    data = await state.get_data()
    sent_messages = data.get('sent_messages', [])
    
    # Удаляем все отправленные сообщения
    for message_id in sent_messages:
        try:
            await bot.delete_message(callback.message.chat.id, message_id)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {message_id}: {str(e)}")
    
    # Возвращаем основную клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Загрузить фото")],
            [KeyboardButton(text="Сравнить папки")]
        ], 
        resize_keyboard=True
    )
    
    await callback.message.answer(
        "Сообщения удалены",
        reply_markup=keyboard
    )
    
    # Очищаем состояние
    await state.clear()

@router.message(Command("reindex"))
async def reindex_root_folder(message: types.Message):
    """Полное сканирование корневой папки"""
    try:
        status_message = await message.answer("🔄 Начинаю полное сканирование базы...")
        finder = YandexImageSimilarityFinder(bins=16)
        public_link = finder.get_public_link(finder.pathMain) 
        # Поучаем общее количество файлов в корневой папке
        await status_message.edit_text("📊 Подсчитываю количество файлов...")
        total_files = finder.count_files_recursive(finder.pathMain)
        
        if total_files == 0:
            await status_message.edit_text("❌ Не найдено файлов для обработки")
            return
        
        await status_message.edit_text(
            f"📁 Найдено {total_files} файлов\n"
            "Начинаю сканирование..."
        )
        
        async def update_progress(current, total, estimated_time):
            progress = int((current / total) * 10)
            progress_bar = "■" * progress + "□" * (10 - progress)
            percentage = int((current / total) * 100)
            progress_text = (
                f"🔍 Сканирование базы:\n"
                f"[{progress_bar}] {percentage}%\n"
                f"Обработано: {current}/{total}\n"
                f"Осталось примерно: {estimated_time}"
            )
            await status_message.edit_text(progress_text)
        
        # Очищаем старую базу данных
        # with sqlite3.connect(finder.db_path) as conn:
        #     cursor = conn.cursor()
        #     cursor.execute('DELETE FROM images')
        #     conn.commit()
        
        # Сканируем корневую папку
        # public_link = finder.get_public_link(finder.pathMain)
        scan_success = await finder.scan_directory_async(public_link, update_progress)
        
        if scan_success:
            await status_message.edit_text(
                "✅ Сканирование завершено\n"
                f"Обработано файлов: {total_files}\n"
                f"База данных обновлена"
            )
        else:
            await status_message.edit_text(
                "⚠️ Сканирование завершено с ошибками\n"
                "Проверьте логи для получения дополнительной информации"
            )
            
    except Exception as e:
        error_message = f"❌ Ошибка при сканировании: {str(e)}"
        logger.error(error_message)
        if status_message:
            await status_message.edit_text(error_message)
        else:
            await message.answer(error_message)

@router.callback_query(lambda c: c.data.startswith('move_all:'))
async def move_all_files(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Перенести в [папка]'"""
    try:
        folder_idx = callback.data.split(':')[1]
        data = await state.get_data()
        finder = data['finder']
        folder_mapping_move = data['folder_mapping_move']
        
        folder_info = folder_mapping_move.get(f"f{folder_idx}")
        if not folder_info:
            await callback.message.edit_text("Ошибка: папка не найдена")
            return
        
        source_folder = folder_info['mainFolder']
        target_folder = folder_info['secondFolder']
        
        await callback.message.edit_text("Получаю актуальный список файлов...")
        
        # Получаем все файлы из исходной папки
        current_files = finder.get_current_folder_files(source_folder)
        
        if not current_files:
            await callback.message.edit_text("Нет файлов для переноса")
            return
        
        await callback.message.edit_text(f"Переношу {len(current_files)} файлов...")
        
        success_count = 0
        for file_path in current_files:
            try:
                # Добавляем await перед вызовом асинхронного метода
                if await finder.move_file(file_path, target_folder):
                    success_count += 1
            except Exception as e:
                logger.error(f"Ошибка при переносе файла {file_path}: {str(e)}")
        
        await finder.update_folder_status(
            source_folder=source_folder,
            target_folder=target_folder,
            new_path=None,
            status='all_files_moved',
            processed_at=datetime.datetime.now()
        )
        
        await callback.message.edit_text(
            f"✅ Перенесено {success_count} из {len(current_files)} файлов\n"
            f"Из папки: {os.path.dirname(source_folder)}/[{os.path.basename(source_folder)}]({finder.get_public_link(source_folder)})\n"
            f"В папку: {os.path.dirname(target_folder)}/[{os.path.basename(target_folder)}]({finder.get_public_link(target_folder)})"
        )
        
    except Exception as e:
        error_message = f"Ошибка при переносе файлов"
        logger.error(f"{error_message}: {str(e)}")
        await callback.message.edit_text(error_message)

if __name__ == "__main__":
    # import asyncio
    pass
    # asyncio.run(main())