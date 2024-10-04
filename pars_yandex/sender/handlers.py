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
from ydWork import YandexDiskManager  # Импортируем менеджер Яндекс Диска
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

Yd=YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD, isTest=True)

class UploadStates(StatesGroup):
    waiting_for_folder = State()
    waiting_for_photos = State()
    get_deal_id=State()
    folder=State()

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
    data = await state.get_data()
    await message.answer("Введите номер папки и название объекта\nНапример: 1 фото стадион зоркий ([номер сделки] [название подпапки]):")
    deals, dealDict= await get_prepare_active_deals()
    print(deals)
    print(repr(deals))  # This will show the raw string, including escape characters
    try:
        # deals =re.sub(r'[^\x20-\x7E]', '', deals)  # Remove non-printable characters

        await message.answer(f"{deals}", parse_mode="HTML")
    except:
        deals1=f"{deals[:len(deals)//2]}"
        await message.answer(deals1)
        deals1=f"{deals[len(deals)//2:]}"
        await message.answer(deals1)
    
    
    projectID=postgreWork.get_last_project_for_user(userID=message.from_user.id)
    
    if projectID==None:
        projectID=0
    else:
        projectID=projectID.id
    
    await state.set_state(UploadStates.waiting_for_folder)
    await state.update_data(deals=dealDict, projectID=projectID)
    # await state.set_state(UploadStates.get_deal_id)
    return 0




@router.message(UploadStates.waiting_for_folder)
async def process_folder(message: types.Message, state: FSMContext):
    data = await state.get_data()
    numberDeal=int(message.text.split(' ')[0])
    try:
        dealID=data['deals'][numberDeal]['ID']
        dealTitle=data['deals'][numberDeal]['TITLE']
        dealUrlFolder=data['deals'][numberDeal][Deal.urlFolder]
    except:
        await message.answer("Неверный номер сделки")
        return 0
    data = await state.update_data(deals=data['deals'][numberDeal])
    #удаляем номер сделки из названия
    folderTitle=message.text.replace(f'{numberDeal} ', '')
    
    await state.update_data(folder=folderTitle, 
                            folderTitle=dealTitle,
                            dealID=dealID,
                            dealUrlFolder=dealUrlFolder,
                            photos=[])  # Инициализируем список фотографий
    
    await message.answer(f"Вы работаете по проекту {dealTitle}.\n[ссылка на папку]({dealUrlFolder})\nТеперь отправьте фотографии (можно несколько):")
    # await message.answer("Теперь отправьте фотографии (можно несколько):")
    
    # Создаем клавиатуру с кнопкой "Завершить загрузку"
    # keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    # keyboard.add(KeyboardButton(text="Завершить загрузку"))
    
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Завершить загрузку")]], resize_keyboard=True)

    await message.answer("Вы можете отправить фотографии или нажать кнопку ниже, чтобы завершить загрузку.", reply_markup=keyboard)
    await state.set_state(UploadStates.waiting_for_photos)
    return 0

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


    Yd.create_folder_and_upload_file(publickURL=data['dealUrlFolder'], 
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
        await message.answer(f"Это правильные данные?\nУ вас данных. Для загрузки просто одних фото нажмите \"НЕТ ❌\"", reply_markup=keyboard)
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
    await message.answer(f"Загрузка фото завершена. Все фото загружены в папку '{folder}' на Яндекс.Диск.", keyboard=keyboard)
    # await state.set_state(UploadStates.waiting_for_folder)
    await state.clear()    
    return 0
@router.message(F.text == "ДА ✅")
async def upload_photos(message: types.Message, state: FSMContext):
    data=await state.get_data()

    keyboard=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
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
        
        await message.answer("Загрузка фото завершена", reply_markup=keyboard)
        await state.clear()
        return 0
    await message.answer(f"Загрузка фото завершена. Все фото загружены в папку '{folder}' на Яндекс.Диск.", keyboard=keyboard)
    # await state.set_state(UploadStates.waiting_for_folder)
    await state.clear()    
    return 0


@router.message(F.text == "НЕТ ❌")
async def upload_photos(message: types.Message, state: FSMContext):
    data=await state.get_data()

    keyboard=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
    userID=message.from_user.id

    project=postgreWork.get_last_project_for_user(userID)
    

    s.add_new_location(name=project.name,
                    address='',
                    phone='',
                    email='',
                    folderURL=project.folder_url,
                    timeWork='',
                    status='Новый'
                       )
    
    postgreWork.update_project(projectID=project.id, isAddtoSheet=True)
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
        
        await message.answer("Загрузка фото завершена", reply_markup=keyboard)
        await state.clear()
        return 0
    
    await message.answer(f"Загрузка фото завершена. Все фото загружены в папку '{folder}' на Яндекс.Диск.", keyboard=keyboard)
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