import re
from aiogram import Bot, Dispatcher, types
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
# from workSelenium import get_info
from dotenv import load_dotenv
import os
load_dotenv()
API_TOKEN = os.getenv('TOKEN_BOT')  # Замените на ваш токен

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
# storage = MemoryStorage()
dp = Dispatcher(bot)

# Массив с картинками
images = [
    'https://avatars.mds.yandex.net/get-altay/6203011/2a000001809aa9f21221013873fccda9f46e/XXXL',
    'https://avatars.mds.yandex.net/get-altay/1429587/2a0000018611a6c8ecabd2d6d18440938908/XXXL',
    'https://avatars.mds.yandex.net/get-altay/5235091/2a0000017b12d3aee4865306505dbfd1486d/XXXL',
    'https://avatars.mds.yandex.net/get-altay/4587805/2a0000017b12d36cd4b20a9140e7db190c9f/XXXL'
]



if __name__ == '__main__':
    # executor.start_polling(dp, skip_updates=True)
    executor.start_polling(dp, )