from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import os
import requests

TOKEN = "7639996461:AAE1Grm61BEjUb6uGqdIz1pvmTO5z4n6-Ak"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню с кнопкой для получения IP
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌍 Почати користування")],
        [KeyboardButton(text="📡 Показати IP ESP8266")],  # Кнопка для отображения IP
    ],
    resize_keyboard=True
)

# Состояние последнего IP (будет обновляться через Flask)
last_esp_ip = None  # Это будет обновляться через Flask

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Натисніть на кнопку для продовження спілкування:", reply_markup=main_keyboard)

@dp.message()
async def menu_handler(message: types.Message):
    user_id = message.from_user.id  # Получаем user_id из сообщения
    
    if message.text.strip() == "🌍 Почати користування":
        await message.answer("Виберіть дію:", reply_markup=main_keyboard)
        return
    
    # Если нажата кнопка для получения IP
    elif message.text.strip() == "📡 Показати IP ESP8266":
        if last_esp_ip:
            await message.answer(f"📡 Поточний IP ESP8266: {last_esp_ip}")
        else:
            await message.answer("❌ IP не отримано. Спробуйте ще раз.")
        return

    # Если команда не распознана
    await message.answer("Я не розумію цю команду. Будь ласка, оберіть опцію з меню.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
