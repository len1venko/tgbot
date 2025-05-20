import asyncio
import requests
import time
from background import keep_alive
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import pytz

def match_date(timestamp_str, target_date):
    try:
        utc_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Europe/Kyiv"))
        return local_time.date() == target_date.date()
    except Exception as e:
        print(f"⚠️ Error parsing timestamp: {e}")
        return False


user_state = {}  # Временное хранилище состояний пользователей (например, ожидание даты)
TOKEN = "7639996461:AAE1Grm61BEjUb6uGqdIz1pvmTO5z4n6-Ak"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbyx9trfhFUWfJZoI6uIQzO06Cgqz8oXkLaNsFZKJkWTtVDplkhkaD75iJul-NNerah5/exec"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌍 Почати користування")],
    ],
    resize_keyboard=True
)


# Подменю для WAN
wan_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Переглянути історію параметрів мікроклімату")],
        [KeyboardButton(text="🌤️ Перехід до головної сторінки веб-інтерфейсу (LAN)")],
        [KeyboardButton(text="📋 Переглянути поточні параметри мікроклімату")],
        [KeyboardButton(text="📈 Переглянути середні значення параметрів мікроклімату за дату")],
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
    await message.answer("Натисніть на кнопку для продовження спілкування:", reply_markup=main_keyboard)


@dp.message()
async def menu_handler(message: types.Message):
    user_id = message.from_user.id  # Получаем user_id из сообщения
    
    # Если пользователь находится в состоянии ожидания даты
    if user_id in user_state and user_state[user_id].get("awaiting_date"):
        input_date = message.text.strip()  # Ожидаем YYYY-MM-DD
        print(f"Получена дата: {input_date}")  # Логируем дату

        try:
            # Преобразуем в формат DD.MM.YYYY
            dt_obj = datetime.strptime(input_date, "%Y-%m-%d")
            formatted_date = dt_obj.strftime("%d.%m.%Y")
            print(f"Дата преобразована: {formatted_date}")  # Логируем преобразованную дату
        except ValueError:
            await message.answer("❌ Неправильний формат дати. Введіть у форматі YYYY-MM-DD.")
            return

        data = get_data_from_google_sheet()
        if data:
            # Фильтруем данные по дате, введённой пользователем
            filtered = [item for item in data if "timestamp" in item and match_date(item["timestamp"], dt_obj)]
            
            if filtered:
                # Вычисляем средние значения, как и раньше
                temp = sum(float(i["temperature"]) for i in filtered) / len(filtered)
                hum = sum(float(i["humidity"]) for i in filtered) / len(filtered)
                press = sum(float(i["pressure"]) for i in filtered) / len(filtered)
                alt = sum(float(i["altitude"]) for i in filtered) / len(filtered)
                gas = sum(float(i["gasValue"]) for i in filtered) / len(filtered)

                response = (
                    f"📈 <b>Середні значення за {dt_obj.strftime('%d.%m.%Y')} (WAN):</b>\n"
                    f"🌡 Температура: <b>{temp:.2f}</b> °C\n"
                    f"💧 Вологість: <b>{hum:.2f}</b> %\n"
                    f"🔽 Тиск: <b>{press:.2f}</b> hPa\n"
                    f"⛰ Висота: <b>{alt:.2f}</b> m\n"
                    f"🛢 Газ: <b>{gas:.2f}</b> ppm"
                )
                await message.answer(response, parse_mode="HTML", reply_markup=wan_keyboard)
            else:
                await message.answer("❌ Немає даних за цю дату.", reply_markup=wan_keyboard)
        else:
            await message.answer("❌ Не вдалося отримати дані з Google Sheets.", reply_markup=wan_keyboard)

        # Сброс состояния
        user_state.pop(user_id, None)
        return


    # Обрабатываем основное меню
    if message.text == "🌍 Почати користування":
        await message.answer("Виберіть дію:", reply_markup=wan_keyboard)


    # Кнопки WAN
    elif message.text.strip() == "ℹ️ Переглянути історію параметрів мікроклімату":
        await message.answer("🔗 [Історія (WAN)](https://surl.li/harpcn)", parse_mode="Markdown", reply_markup=wan_keyboard)
    elif message.text.strip() == "🌤️ Перехід до головної сторінки веб-інтерфейсу (LAN)":
        await message.answer("🔗 [Дані (WAN)](https://duck-liked-slowly.ngrok-free.app/)", parse_mode="Markdown", reply_markup=wan_keyboard)
    elif message.text.strip() == "📋 Переглянути поточні параметри мікроклімату":
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

    elif message.text.strip() == "📈 Переглянути середні значення параметрів мікроклімату за дату":
        await message.answer("🗓 Введіть дату у форматі YYYY-MM-DD:")
        user_state[user_id] = {"awaiting_date": True}

    # Назад в главное меню
    elif message.text.strip() == "🔙 Назад":
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

from threading import Thread
Thread(target=ping_self).start()

if __name__ == "__main__":
    asyncio.run(main())
