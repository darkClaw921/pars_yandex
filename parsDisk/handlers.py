import asyncio
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
TOKEN = os.getenv('SENDER_BOT_TOKEN')

router = Router()

bot = Bot(token=TOKEN,)

s=Sheet('profzaboru-5f6f677a3cd8.json','Объекты тест','Объекты')

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
            nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"folderpage:{current_page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{current_page}/{self.total_pages}", callback_data="ignore"))
        if current_page < self.total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"folderpage:{current_page+1}"))
        
        # Добавляем навигационные кнопки в конец
        builder.row(*nav_buttons)
        
        return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        postgreWork.add_new_user(
            userID=message.from_user.id,
            nickname=message.from_user.username
        )
    except:
        pass
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Загрузить фото")],
            [KeyboardButton(text="Сравнить папки")]
        ], 
        resize_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)
    return 0

@router.message(F.text == "Сравнить папки")
async def compare_folders_start(message: types.Message, state: FSMContext):
    await message.answer("Отправьте ссылку на первую папку Яндекс.Диска:")
    await state.set_state(UploadStates.waiting_for_first_folder)

@router.message(UploadStates.waiting_for_first_folder)
async def process_first_folder(message: types.Message, state: FSMContext):
    folder_link = message.text
    finder = YandexImageSimilarityFinder(bins=16)
    
    try:
        # Проверяем наличие папки в базе
        folder_meta = finder.yadisk.get_public_meta(folder_link)
        folder_path = finder.pathMain + folder_meta.name
        
        # Сохраняем информацию о первой папке
        await state.update_data(
            finder=finder,
            first_folder_link=folder_link,
            first_folder_path=folder_path
        )
        
        await message.answer("Отправьте ссылку на вторую папку для сравнения:")
        await state.set_state(UploadStates.waiting_for_second_folder)
        
    except Exception as e:
        await message.answer(f"Ошибка при доступе к папке: {str(e)}")
        await state.clear()

@router.message(UploadStates.waiting_for_second_folder)
async def process_second_folder(message: types.Message, state: FSMContext):
    folder_link = message.text
    data = await state.get_data()
    finder = data['finder']
    first_folder_path = data['first_folder_path']
    first_folder_link = data['first_folder_link']
    
    try:
        # Проверяем наличие второй папки
        folder_meta = finder.yadisk.get_public_meta(folder_link)
        second_folder_path = finder.pathMain + folder_meta.name
        
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
            
            async def update_progress(current, total, estimated_time):
                progress = int((current / total) * 10)
                progress_bar = "■" * progress + "□" * (10 - progress)
                percentage = int((current / total) * 100)
                progress_text = f"Сканирую первую папку:\n[{progress_bar}] {percentage}%\nОсталось примерно: {estimated_time}"
                await status_message.edit_text(progress_text)
            
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
            await status_message.edit_text(f"Вторая папка не найдена в базе, начинаю сканирование...")
            progress_text = "Сканирую вторую папку:\n[□□□□□□□□□□] 0% (осталось: --)"
            await status_message.edit_text(progress_text)
            
            async def update_progress(current, total, estimated_time):
                progress = int((current / total) * 10)
                progress_bar = "■" * progress + "□" * (10 - progress)
                percentage = int((current / total) * 100)
                progress_text = f"Сканирую вторую папку:\n[{progress_bar}] {percentage}%\nОсталось примерно: {estimated_time}"
                await status_message.edit_text(progress_text)
            
            scan_success = await finder.scan_directory_async(folder_link, update_progress)
            if not scan_success:
                await status_message.edit_text("❌ Ошибка при сканировании второй папки")
                await state.clear()
                return
            await status_message.edit_text("Вторая папка отсканирована ✅")
            # Проверяем еще раз после сканирования
            second_folder_exists = finder.is_folder_in_database(second_folder_path)
            logger.info(f"Повторная проверка второй папки: {'найдена' if second_folder_exists else 'не найдена'}")
        
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
            # Группируем похожие фото по подпапкам первой папки
            folders_with_similar = {}
            for match in similar_photos:
                folder_path = os.path.dirname(match['full_path1'])
                if folder_path not in folders_with_similar:
                    folders_with_similar[folder_path] = {
                        'similar': [],
                        'all_files': []
                    }
                folders_with_similar[folder_path]['similar'].append(match)
            
            # Получаем все файлы из каждой папки, где есть совпадения
            for folder_path in folders_with_similar:
                all_files = finder.get_all_files_from_folder(folder_path, set())
                folders_with_similar[folder_path]['all_files'] = all_files
            
            # Формируем сообщение о результатах
            text_parts = ["Найдены похожие фотографии:\n\n"]
            current_part = ""
            sent_messages = []
            
            for folder_path, folder_data in folders_with_similar.items():
                folder_text = f"В папке: {folder_path}\n"
                folder_text += "Найдены похожие:\n"
                
                for match in folder_data['similar']:
                    match_text = (
                        f"Файл: {match['file1']}\n"
                        f"Похож на: {match['file2']}\n"
                        f"Схожесть: {match['similarity']:.2f}%\n"
                    )
                    folder_text += match_text
                
                remaining_files = [f for f in folder_data['all_files'] 
                                 if os.path.basename(f) not in [m['file1'] for m in folder_data['similar']]]
                folder_text += f"\nОстальные файлы в этой папке ({len(remaining_files)} шт):\n"
                for file in remaining_files:
                    folder_text += f"- {os.path.basename(file)}\n"
                
                if len(current_part + folder_text) > 4000:
                    text_parts.append(current_part)
                    current_part = folder_text
                else:
                    current_part += folder_text
            
            if current_part:
                text_parts.append(current_part)
            
            # Отправляем сообщения частями
            for part in text_parts:
                sent_msg = await message.answer(part, parse_mode='HTML') #обязательно HTML
                sent_messages.append(sent_msg.message_id)
            
            # Создаем клавиатуру для выбора папок с короткими идентификаторами
            keyboard = InlineKeyboardBuilder()
            folder_mapping = {}  # Словарь для хранения соответствия ID и путей
            
            for idx, folder_path in enumerate(folders_with_similar.keys(), 1):
                folder_name = os.path.basename(folder_path)
                folder_id = f"f{idx}"  # Короткий ID для папки
                folder_mapping[folder_id] = folder_path
                
                remaining_files = len([f for f in folders_with_similar[folder_path]['all_files'] 
                                    if os.path.basename(f) not in 
                                    [m['file1'] for m in folders_with_similar[folder_path]['similar']]])
                
                keyboard.button(
                    text=f"Перенести из {folder_name} ({remaining_files} файлов)", 
                    callback_data=f"move:{folder_id}"
                )
            
            keyboard.button(text="Отмена", callback_data="cancel")
            keyboard.adjust(1)
            
            # Сохраняем маппинг в состоянии
            await state.update_data(
                sent_messages=sent_messages,
                second_folder_path=second_folder_path,
                folders_with_similar=folders_with_similar,
                folder_mapping=folder_mapping
            )
            
            await message.answer(
                "Выберите папку, из которой нужно перенести оставшиеся файлы:",
                reply_markup=keyboard.as_markup()
            )
            await state.set_state(UploadStates.confirm_move)
        else:
            await status_message.edit_text("Похожих фотографий не найдено")
            await state.clear()
            
    except Exception as e:
        await message.answer(f"Ошибка при сравнении папок: {str(e)}")
        await state.clear()

@router.callback_query(UploadStates.confirm_move, lambda c: c.data.startswith('move:'))
async def move_files_from_folder(callback: types.CallbackQuery, state: FSMContext):
    folder_id = callback.data.split(':')[1]
    data = await state.get_data()
    finder = data['finder']
    folders_with_similar = data['folders_with_similar']
    folder_mapping = data['folder_mapping']
    target_folder = data['second_folder_path']
    
    # Получаем реальный путь к папке из маппинга
    source_folder = folder_mapping.get(folder_id)
    if not source_folder:
        await callback.message.answer("Ошибка: папка не найдена")
        return
    
    folder_data = folders_with_similar[source_folder]
    similar_files = [m['file1'] for m in folder_data['similar']]
    files_to_move = [f for f in folder_data['all_files'] 
                     if os.path.basename(f) not in similar_files]
    
    await callback.message.edit_text(f"Начинаю перенос {len(files_to_move)} файлов...")
    
    success_count = 0
    for file_path in files_to_move:
        try:
            if finder.move_file(file_path, target_folder):
                success_count += 1
        except Exception as e:
            await callback.message.answer(f"Ошибка при переносе {file_path}: {str(e)}")
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Загрузить фото")],
            [KeyboardButton(text="Сравнить папки")]
        ], 
        resize_keyboard=True
    )
    
    await callback.message.answer(
        f"Перенесено {success_count} из {len(files_to_move)} файлов",
        reply_markup=keyboard
    )
    await state.clear()

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
    
    # Добавляем путь к файлу в список
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
        await message.answer("Вы не отправили ни одной фотографии.")
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
    await state.clear()
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
    await state.clear()

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
    await callback_query.message.answer("Вы можете отправить фотографии или нажать кнопку ниже, чтобы завершить загрузку.", reply_markup=keyboard)
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
    
    # Создаем полный путь к новой папке
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
                os.remove(photo_path)  # Удаляем локальный файл осле загрузки
        
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
    
    await state.clear()

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
#     #     filename = f"{downloaded_file.file_id}.jpg"  # Или используйте другой способ генерации имени
#     #     yadisk_path = f"/{folder}/{filename}"
#     #     yadisk_manager.upload_file(downloaded_file, yadisk_path)
#     pprint(photos)
#     await message.answer(f"Все фото успешно загружены на Яндекс.Диск в папку '{folder}'")
#     await state.clear()  # Завершаем состояние
#     return 0
# async def main():
#     await router.start_polling(bot)

if __name__ == "__main__":
    # import asyncio
    pass
    # asyncio.run(main())