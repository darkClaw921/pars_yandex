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
load_dotenv()
TOKEN = os.getenv('TOKEN_BOT_EVENT')

router = Router()

bot = Bot(token=TOKEN,)

from loguru import logger
logger.add("logs/file_{time}.log",format="{time} - {level} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")


@router.message(lambda message: re.match(r'https://.*', message.text))
async def messagetry(msg: Message, state: FSMContext):
    url = msg.text
    logger.info(f"Получена ссылка {url} от пользователя {msg.from_user.id} с ником {msg.from_user.username}")
    await msg.reply("Начинаю сбор, может занять некоторое время ⏱️")
    try:
        phone, imgInside, imgOutside = get_info(url)  # Вызов функции из workSelenium.py
    except Exception as e:
        logger.error(e)
        await msg.reply(f"Ошибка при обработке ссылки")
        return
    
    await msg.reply(phone)  # Отправка информации обратно пользователю

    # Подготовка медиа группы
    
    await bot.send_message("Фотографии Внутри:")
    media = [InputMediaPhoto(media=str(img)) for img in imgInside]
    # Отправка медиа группы
    await msg.answer_media_group(media)
    

    await bot.send_message("Фотографии Снаружи:")
    media = [InputMediaPhoto(media=str(img)) for img in imgOutside]
    # Отправка медиа группы
    await msg.answer_media_group(media)

@router.message(lambda message: not re.match(r'https://.*', message.text))
async def message(msg: Message, state: FSMContext):
    await msg.reply("Пожалуйста, отправьте корректную HTTPS ссылку.") 
    
    

if __name__ == '__main__':
    

    pass
