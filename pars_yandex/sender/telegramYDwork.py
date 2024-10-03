
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
from ydWork import YandexDiskManager  # Импортируем менеджер Яндекс Диска
from dotenv import load_dotenv
import os
load_dotenv()
APLICATION_ID = os.getenv('APLICATION_ID')
APLICATION_SECRET = os.getenv('APLICATION_SECRET')
TOKEN_YD = os.getenv('TOKEN_YD')
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
yadisk_manager = YandexDiskManager(APLICATION_ID=APLICATION_ID, 
                                   APLICATION_SECRET=APLICATION_SECRET,
                                   TOKEN_YD=TOKEN_YD)  # Создаем экземпляр менеджера

class UploadStates(StatesGroup):
    waiting_for_folder = State()
    waiting_for_photos = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Загрузить фото")]], resize_keyboard=True)
    await message.answer("Привет! Нажми кнопку, чтобы начать загрузку фото.", reply_markup=keyboard)

@dp.message(F.text == "Загрузить фото")
async def upload_photos(message: types.Message, state: FSMContext):
    await message.answer("Введите название папки на Яндекс.Диске, куда нужно загрузить фото:")
    await state.set_state(UploadStates.waiting_for_folder)

@dp.message(UploadStates.waiting_for_folder)
async def process_folder(message: types.Message, state: FSMContext):
    await state.update_data(folder=message.text, photos=[])  # Инициализируем список фотографий
    await message.answer("Теперь отправьте фотографии (можно несколько):")
    
    # Создаем клавиатуру с кнопкой "Завершить загрузку"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Завершить загрузку"))
    
    await message.answer("Вы можете отправить фотографии или нажать кнопку ниже, чтобы завершить загрузку.", reply_markup=keyboard)
    await state.set_state(UploadStates.waiting_for_photos)

@dp.message(UploadStates.waiting_for_photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    folder = data['folder']
    photos = data['photos']

    # Обработка фотографии
    for photo in message.photo:
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        downloaded_file = await bot.download_file(file_path)
        
        filename = f"{file_id}.jpg"
        yadisk_path = f"/{folder}/{filename}"

        # Сохраняем файл в список
        photos.append(downloaded_file)

    # Обновляем состояние с новыми фотографиями
    await state.update_data(photos=photos)
    await message.answer("Фото добавлены в очередь. Вы можете отправить еще фотографии или завершить загрузку.")

@dp.message(UploadStates.waiting_for_photos, F.text == "Завершить загрузку")
async def finish_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    folder = data['folder']
    photos = data['photos']

    # Загружаем все собранные фотографии на Яндекс Диск
    for downloaded_file in photos:
        filename = f"{downloaded_file.file_id}.jpg"  # Или используйте другой способ генерации имени
        yadisk_path = f"/{folder}/{filename}"
        yadisk_manager.upload_file(downloaded_file, yadisk_path)

    await message.answer(f"Все фото успешно загружены на Яндекс.Диск в папку '{folder}'")
    await state.finish()  # Завершаем состояние

@dp.message(UploadStates.waiting_for_photos)
async def process_non_photo(message: types.Message):
    await message.answer("Пожалуйста, отправьте фото или нажмите 'Завершить загрузку', чтобы закончить.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())