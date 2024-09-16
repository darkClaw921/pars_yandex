import asyncio
from aiogram import types, F, Router, html, Bot
from aiogram.types import (Message, CallbackQuery,
                           InputFile, FSInputFile,
                            MessageEntity, InputMediaDocument,
                            InputMediaPhoto, InputMediaVideo, Document)
from aiogram.filters import Command, StateFilter,ChatMemberUpdatedFilter

from pprint import pprint
from aiogram.fsm.context import FSMContext

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import re
from dotenv import load_dotenv
import os

from loguru import logger
from workSelenium import get_info
from pars_avito import get_info_avito
load_dotenv()
TOKEN = os.getenv('TOKEN_BOT_EVENT')

router = Router()

bot = Bot(token=TOKEN,)

from loguru import logger
logger.add("logs/file_{time}.log",format="{time} - {level} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")



def extract_https_link(text):
    # Ищем первую HTTPS ссылку в тексте
    match = re.search(r'https://[^\s]+', text)
    if match:
        return match.group(0)  # Возвращаем найденную ссылку
    return None  # Если ссылки не найдено, возвращаем Non

# @router.message(lambda message: re.match(r'https://.*', message.text))
# async def messagetry(msg: Message, state: FSMContext):
#отправка фото пачками по 10 штук
async def send_photos(msg: Message, photos: list):
    for i in range(0, len(photos), 10):
        await msg.answer_media_group([InputMediaPhoto(media=str(img)) for img in photos[i:i + 10]])
        
@router.message(lambda message: message.text.startswith('https'))
async def handle_link(msg: Message):
    try:
        url = extract_https_link(msg.text)
    except:
        logger.error(f"Ошибка при обработке ссылки {msg.text} от пользователя {msg.from_user.id} с ником {msg.from_user.username}")
        # await msg.reply("Ошибка при обработке ссылки")
        # return
        url=msg.text 
    # url = msg.text
    logger.info(f"Получена ссылка {url} от пользователя {msg.from_user.id} с ником {msg.from_user.username}")
    await msg.reply("Начинаю сбор, может занять некоторое время ⏱️")

    if 'avito.ru' in url:
        await handle_avito(msg, url)
    elif 'cian.ru' in url:
        await handle_cian(msg, url)
    elif 'yandex.ru' in url:
        await handle_yandex(msg, url)
    else:
        await msg.reply("Ссылка не распознана. Пожалуйста, отправьте ссылку на Avito, Cian или Yandex.")



async def handle_avito(msg: Message, url: str):
    adress, photo = get_info_avito(url)  
    if adress is None:
        await msg.reply(f"Адрес отсутсвует")
    else:
        await msg.reply(adress)
    if photo is None:
        await msg.reply(f"Фотографии отсутствуют")
    else:
        await msg.reply("Фотографии:")
        media = [InputMediaPhoto(media=str(img)) for img in photo]
        if len(media)==1:
            await msg.answer_media_group(media)
        else:
            #
            send_photos(msg, photo)


    await msg.reply("Это ссылка на Avito!")

async def handle_cian(msg: Message, url: str):
    # await message.reply("Это ссылка на Cian!")
    await msg.reply("Ссылки на Cian пока не поддерживаются")

async def handle_yandex(msg: Message, url: str):
    await msg.reply("Это ссылка на Yandex!")
           
    try:
        phone, imgInside, imgOutside = get_info(url)  # Вызов функции из workSelenium.py
    except Exception as e:
        logger.error(e)
        await msg.reply(f"Ошибка при обработке ссылки")
        return 0 
    if phone is None:
        await msg.reply(f"Телефон отсутсвует")
    else:
        await msg.reply(phone)  # Отправка информации обратно пользователю
        
    # Подготовка медиа группы
    if imgInside is None:
        await bot.send_message(msg.from_user.id,"Фотографии Внутри отсутствуют")
    else:
        await bot.send_message(msg.from_user.id,"Фотографии Внутри:")
        media = [InputMediaPhoto(media=str(img)) for img in imgInside]
    # Отправка медиа группы
    #первая половина фото
        if len(media)==1:
            await msg.answer_media_group(media)
        else:
            await msg.answer_media_group(media[:len(media)//2])
            await msg.answer_media_group(media[len(media)//2:])
    
    if imgOutside is None:
        await bot.send_message(msg.from_user.id,"Фотографии Снаружи отсутствуют")
    else:
        await bot.send_message(msg.from_user.id, "Фотографии Снаружи:")
        media = [InputMediaPhoto(media=str(img)) for img in imgOutside]
        # Отправка медиа группы
        if len(media)==1:
            await msg.answer_media_group(media)
        else:
            await msg.answer_media_group(media[:len(media)//2])
            await msg.answer_media_group(media[len(media)//2:])
    

@router.message(lambda message: not re.match(r'https://.*', message.text))
async def message(msg: Message, state: FSMContext):
    await msg.reply("Пожалуйста, отправьте корректную HTTPS ссылку.") 
    
    

if __name__ == '__main__':
    

    pass
