import asyncio
import requests
from background import keep_alive
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import pytz

TOKEN = "7639996461:AAE1Grm61BEjUb6uGqdIz1pvmTO5z4n6-Ak"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbz5DH-UVC3OJGBq_cwbqnHYcQ8yQrNXM3-5Eae46Lg5RiIN2RJkpU4L8D49dAnMRME5/exec"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🖥️ LAN")],
        [KeyboardButton(text="🌍 WAN")],
    ],
    resize_keyboard=True
)

# Подменю для LAN
lan_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Переглянути історію показників мікроклімату (LAN)")],
        [KeyboardButton(text="🌤️ Переглянути дані про мікроклімат (LAN)")],
        [KeyboardButton(text="📊 Переглянути графік мікроклімату (LAN)")],
        [KeyboardButton(text="📅 Переглянути календар мікроклімату (LAN)")],
        [KeyboardButton(text="📋 Переглянути поточні параметри мікроклімату (LAN)")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Подменю для WAN
wan_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Переглянути історію показників мікроклімату (WAN)")],
        [KeyboardButton(text="🌤️ Переглянути дані про мікроклімат (WAN)")],
        [KeyboardButton(text="📊 Переглянути графік мікроклімату (WAN)")],
        [KeyboardButton(text="📅 Переглянути календар мікроклімату (WAN)")],
        [KeyboardButton(text="📋 Переглянути поточні параметри мікроклімату (WAN)")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)


# Функция для получения данных из Google Таблицы
def get_data_from_google_sheet():
    try:
        response = requests.get(GOOGLE_SHEET_URL)
        data = response.json()
        if data:
            return data
        return None
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        return None


# Преобразуем строку в datetime с UTC
def convert_to_local_time(timestamp):
    utc_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)  # Указываем, что это UTC
    local_tz = pytz.timezone("Europe/Kyiv")
    local_time = utc_time.astimezone(local_tz)
    return local_time.strftime("%d-%m-%Y %H:%M:%S")


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Оберіть звідки ви бажаєте почати користування:", reply_markup=main_keyboard)


@dp.message()
async def menu_handler(message: types.Message):
    # Обрабатываем основное меню
    if message.text == "🖥️ LAN":
        await message.answer("Виберіть дію:", reply_markup=lan_keyboard)
    elif message.text == "🌍 WAN":
        await message.answer("Виберіть дію:", reply_markup=wan_keyboard)
    
    # Кнопки LAN
    elif message.text == "ℹ️ Переглянути історію показників мікроклімату (LAN)":
        await message.answer("🔗 [Історія (LAN)](https://surl.li/harpcn)", parse_mode="Markdown", reply_markup=lan_keyboard)
    elif message.text == "🌤️ Переглянути дані про мікроклімат (LAN)":
        await message.answer("🔗 [Дані (LAN)](http://192.168.0.100)", parse_mode="Markdown", reply_markup=lan_keyboard)
    elif message.text == "📊 Переглянути графік мікроклімату (LAN)":
        await message.answer("🔗 [Графік (LAN)](http://192.168.0.100/index)", parse_mode="Markdown", reply_markup=lan_keyboard)
    elif message.text == "📅 Переглянути календар мікроклімату (LAN)":
        await message.answer("🔗 [Календар (LAN)](http://192.168.0.100/calendar)", parse_mode="Markdown", reply_markup=lan_keyboard)
    elif message.text == "📋 Переглянути поточні параметри мікроклімату (LAN)":
        data = get_data_from_google_sheet()
        if data:
            last_entry = data[-1]
            timestamp = last_entry.get("timestamp", None)
            if timestamp:
                formatted_time = convert_to_local_time(timestamp)
                response_message = (
                    f"📋 <b>Поточні параметри мікроклімату (LAN):</b>\n"
                    f"🌡️ Температура: <b>{last_entry['temperature']}</b>\n"
                    f"💧 Вологість: <b>{last_entry['humidity']}</b>\n"
                    f"🔽 Атмосферний тиск: <b>{last_entry['pressure']}</b>\n"
                    f"⛰ Висота над рівнем моря: <b>{last_entry['altitude']}</b>\n"
                    f"🧑‍🔬 Рівень газу у повітрі: <b>{last_entry['gasValue']}</b>\n"
                    f"⚠️ Наявність газу у повітрі: <b>{last_entry['gasState']}</b>\n"
                    f"🕒 Час: <i>{formatted_time}</i>"
                )
                await message.answer(response_message, parse_mode="HTML", reply_markup=lan_keyboard)
            else:
                await message.answer("❌ Помилка: не вдалося знайти timestamp в даних.", reply_markup=lan_keyboard)
        else:
            await message.answer("❌ Помилка: дані не знайдені.", reply_markup=lan_keyboard)


 # Кнопки WAN
    elif message.text == "ℹ️ Переглянути історію показників мікроклімату (WAN)":
        await message.answer("🔗 [Історія (WAN)](https://surl.li/harpcn)", parse_mode="Markdown", reply_markup=wan_keyboard)
    elif message.text == "🌤️ Переглянути дані про мікроклімат (WAN)":
        await message.answer("🔗 [Дані (WAN)](https://duck-liked-slowly.ngrok-free.app/)", parse_mode="Markdown", reply_markup=wan_keyboard)
    elif message.text == "📊 Переглянути графік мікроклімату (WAN)":
        await message.answer("🔗 [Графік (WAN)](https://duck-liked-slowly.ngrok-free.app/index)", parse_mode="Markdown", reply_markup=wan_keyboard)
    elif message.text == "📅 Переглянути календар мікроклімату (WAN)":
        await message.answer("🔗 [Календар (WAN)](https://duck-liked-slowly.ngrok-free.app/ calendar)", parse_mode="Markdown", reply_markup=wan_keyboard)
    elif message.text == "📋 Переглянути поточні параметри мікроклімату (WAN)":
        data = get_data_from_google_sheet()
        if data:
            last_entry = data[-1]
            timestamp = last_entry.get("timestamp", None)
            if timestamp:
                formatted_time = convert_to_local_time(timestamp)
                response_message = (
                    f"📋 <b>Поточні параметри мікроклімату (WAN):</b>\n"
                    f"🌡️ Температура: <b>{last_entry['temperature']}</b>\n"
                    f"💧 Вологість: <b>{last_entry['humidity']}</b>\n"
                    f"🔽 Атмосферний тиск: <b>{last_entry['pressure']}</b>\n"
                    f"⛰ Висота над рівнем моря: <b>{last_entry['altitude']}</b>\n"
                    f"🧑‍🔬 Рівень газу у повітрі: <b>{last_entry['gasValue']}</b>\n"
                    f"⚠️ Наявність газу у повітрі: <b>{last_entry['gasState']}</b>\n"
                    f"🕒 Час: <i>{formatted_time}</i>"
                )
                await message.answer(response_message, parse_mode="HTML", reply_markup=wan_keyboard)
            else:
                await message.answer("❌ Помилка: не вдалося знайти timestamp в даних.", reply_markup=wan_keyboard)
        else:
            await message.answer("❌ Помилка: дані не знайдені.", reply_markup=wan_keyboard)

    # Назад в главное меню
    elif message.text == "🔙 Назад":
        await message.answer("Оберіть потрібну дію:", reply_markup=main_keyboard)
    else:
        await message.answer("Я не розумію цю команду. Будь ласка, оберіть опцію з меню.")


async def main():
    await dp.start_polling(bot)

keep_alive()

# 🔁 Пингуем себя, чтобы не засыпал
def ping_self():
    while True:
        try:
            requests.get("https://tgbot-2-354s.onrender.com")
        except:
            pass
        time.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())
