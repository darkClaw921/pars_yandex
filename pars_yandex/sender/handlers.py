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

BOT_TOKEN = os.getenv('SENDER_BOT_TOKEN')
# YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')
APLICATION_ID = os.getenv('APLICATION_ID')
APLICATION_SECRET = os.getenv('APLICATION_SECRET')
TOKEN_YD = os.getenv('TOKEN_YD')

bot = Bot(token=BOT_TOKEN)
# dp = Dispatcher()
# yadisk_manager = YandexDiskManager(token=YANDEX_TOKEN)  # Создаем экземпляр менеджера
# yandexManager=YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD)

Yd=YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD, isTest=False)

class UploadStates(StatesGroup):
    waiting_for_folder = State()
    waiting_for_photos = State()
    get_deal_id=State()
    folder=State()
    waiting_for_new_folder = State()

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

    print('start')
    try:
        postgreWork.add_new_user(
            userID=message.from_user.id,
            nickname=message.from_user.username
        )
    except:
        1+0
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
    await message.answer("Привет! Нажми кнопку, чтобы начать загрузку фото.", reply_markup=keyboard)
    return 0

@router.message(F.text == "Загрузить фото")
async def upload_photos(message: types.Message, state: FSMContext):
    deals, dealDict = await get_prepare_active_deals()
    paginator = DealPaginator(list(dealDict.values()))
    
    await message.answer("Выберите сделку:", reply_markup=paginator.get_keyboard(1))
    
    projectID = postgreWork.get_last_project_for_user(userID=message.from_user.id)
    
    if projectID is None:
        projectID = 0
    else:
        projectID = projectID.id
    
    await state.update_data(deals=dealDict, projectID=projectID, paginator=paginator, photos=[])
    await state.set_state(UploadStates.waiting_for_folder)


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
        folders = Yd.get_all_folders(selected_deal[Deal.urlFolder])
        folder_paginator = FolderPaginator(folders)
        
        await state.update_data(folder_paginator=folder_paginator, dealUrlFolder=selected_deal[Deal.urlFolder])
        await callback_query.message.edit_text("Выберите существующую папку или создайте новую:", reply_markup=folder_paginator.get_keyboard(1))
        await state.set_state(UploadStates.waiting_for_folder)
    else:
        await callback_query.message.answer("Произошла ошибка при выборе сделки. Попробуйте еще раз.")

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


@router.callback_query(lambda c: c.data == 'new_folder')
async def create_new_folder(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название новой папки:")
    await state.set_state(UploadStates.waiting_for_new_folder)


@router.message(UploadStates.waiting_for_new_folder)
async def process_new_folder(message: types.Message, state: FSMContext):
    new_folder = message.text
    data = await state.get_data()
    selected_deal = data['selected_deal']
    
    # Здесь нужно добавить логику создания новой папки на Яндекс.Диске
    # Например: Yd.create_folder(f"{selected_deal[Deal.urlFolder]}/{new_folder}")
    
    await state.update_data(folder=new_folder)
    await message.answer(f"Создана новая папка: {new_folder}\nТеперь отправьте фотографии (можно несколько):")
    
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Завершить загрузку")]], resize_keyboard=True)
    await message.answer("Вы можете отправить фотографии или нажать кнопку ниже, чтобы завершить загрузку.", reply_markup=keyboard)
    
    await state.set_state(UploadStates.waiting_for_photos)


@router.message(UploadStates.waiting_for_photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pprint(data)
    folder = data['folder']
    photos = data['photos']
    
    projectID=data['projectID']

    pprint(message.photo)
    # Обработка фотографии
    photo=message.photo[-1]
    # for photo in message.photo[-1]:
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    downloaded_file = await bot.download_file(file_path=file_path, destination=f'photos/{file_id}.jpg')
    
    filename = f"{file_id}.jpg"
    yadisk_path = f"/{folder}/{filename}"
    
    # Сохраняем файл в список
    pathFile=f'photos/{file_id}.jpg'
    photos.append(pathFile)
    pprint(photos)


    folder_path, publickURL = Yd.create_folder_and_upload_file(publickURL=data['dealUrlFolder'], 
                                                    folderName=folder, 
                                                    fileName=filename, 
                                                    fileURL=pathFile,
                                                    projectID=projectID)
                                                    
    # Обновляем состояние с новыми фотографиями
    await state.update_data(photos=photos)
    
    await message.react(reaction=[ReactionTypeEmoji(emoji='🫡')], is_big=True)
    # await message.answer("Фото добавлены в очередь. Вы можете отправить еще фотографии или завершить загрузку.")
    
    return 0






@router.message(F.text == "Завершить загрузку")
async def upload_photos(message: types.Message, state: FSMContext):
    data=await state.get_data()
    keyboard=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="ДА ✅")], [KeyboardButton(text="НЕТ ❌")]], resize_keyboard=True)

    
    userID=message.from_user.id

     
    project=postgreWork.get_last_project_for_user(userID)
    if project is None:
        await message.answer(f"Это правильные данные?\nУ вас данных. Для загрузки просто одних фото нажмите \"НЕТ ❌\"", reply_markup=keyboard, parse_mode='HTML')
        return 0
        
    dat=f"""{project.name}
Адрес: {project.address}
Телефон: {project.phone}
Папка: {project.folder_url}
Время работы: {project.time_work}
"""
    await message.answer(f"Это правильные данные?\n{dat}", reply_markup=keyboard)
    return 0
    if not project.isAddtoSheet:
        
        s.add_new_location(name=project.name,
                    address=project.address,
                    phone=project.phone,
                    email='asd@asd.tu',
                    folderURL=project.folder_url,
                    timeWork=project.time_work,
                    status='Новый'
                       )
        
        s.add_new_location(name=project.name,
                    address='',
                    phone='',
                    email='',
                    folderURL=project.folder_url,
                    timeWork='',
                    status='Новый'
                       )
        postgreWork.update_project(projectID=project.id, isAddtoSheet=True)
        

    try:
        folder=data['folder']
    except:
        
        await message.answer("Загрузка фото завершена", reply_markup=keyboard)
        await state.clear()
        return 0
    await message.answer(f"Загрузка фото завершена. Все фото загружены в папку '{folder}' на Яндекс.Диск.", reply_markup=keyboard)
    # await state.set_state(UploadStates.waiting_for_folder)
    await state.clear()    
    return 0
@router.message(F.text == "ДА ✅")
async def upload_photos(message: types.Message, state: FSMContext):
    data=await state.get_data()

    keyboard1=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
    userID=message.from_user.id

    project=postgreWork.get_last_project_for_user(userID)
    
    # pprint(project.__dict__)
    if not project.is_add_to_sheet:
        
        s.add_new_location(name=project.name,
                    address=project.address,
                    phone=project.phone,
                    email='asd@asd.tu',
                    folderURL=project.folder_url,
                    timeWork=project.time_work,
                    status='Новый'
                       )
        
        # s.add_new_location(name=project.name,
        #             address='',
        #             phone='',
        #             email='',
        #             folderURL=project.folder_url,
        #             timeWork='',
        #             status='Новый'
        #                )
        postgreWork.update_project(projectID=project.id, isAddtoSheet=True)
        
    try:
        folder=data['folder']
    except:
        
        await message.answer("Загрузка фото завершена", reply_markup=keyboard1)
        await state.clear()
        return 0
    await message.answer(f"Загрузка фото завершена. Все фото загружены в папку '{folder}' на Яндекс.Диск.", reply_markup=keyboard1)
    # await state.set_state(UploadStates.waiting_for_folder)
    await state.clear()    
    return 0


@router.message(F.text == "НЕТ ❌")
async def upload_photos(message: types.Message, state: FSMContext):
    data=await state.get_data()

    keyboard2=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
    userID=message.from_user.id

    
    project=postgreWork.get_last_project_for_user(userID)
    if project is None:
        # nameProject='******'
        nameProject=data['folder']
        folderURL='******'
    else:
        nameProject=project.name   
        folderURL=project.folder_url

    nameProject=data['folder']

    s.add_new_location(name=nameProject,
                    address='',
                    phone='',
                    email='',
                    folderURL=folderURL,
                    timeWork='',
                    status='Новый'
                    )
    try:
        # project=postgreWork.get_last_project_for_user(userID) 
        postgreWork.update_project(projectID=project.id, isAddtoSheet=True)
    except:
        1+0
        
    # if not project.isAddtoSheet:
        
        # s.add_new_location(name=project.name,
        #             address=project.address,
        #             phone=project.phone,
        #             email='asd@asd.tu',
        #             folderURL=project.folder_url,
        #             timeWork=project.time_work,
        #             status='Новый'
        #                )
        
        
        
        
    try:
        folder=data['folder']
    except:
        
        await message.answer("Загрузка фото завершена", reply_markup=keyboard2)
        await state.clear()
        return 0
    
    await message.answer(f"Загрузка фото завершена. Все фото загружены в папку '{folder}' на Яндекс.Диск. ура", reply_markup=keyboard2)
    # await state.set_state(UploadStates.waiting_for_folder)
    await state.clear()    
    return 0





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