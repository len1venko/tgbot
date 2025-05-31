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
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxjXjYmRXTuHXJMXBF1lSBEVsqKuVf3aHrCCSS1_k5qq0O8I6BH1MI972D0bAcCTE3g/exec"

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
        [KeyboardButton(text="📊 Прогноз параметру на N годин")],  # 🔴 Новая кнопка
        [KeyboardButton(text="⚙️ Змінити порогові значення реле")],
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
    user_id = message.from_user.id
    text = message.text.strip()
    ESP_URL = "http://192.168.0.102/set-thresholds"  # Заміни <IP_ESP8266> на свій

    # ⚙️ Змінити порогові значення реле
    if text == "⚙️ Змінити порогові значення реле":
        user_state[user_id] = {"awaiting_temp_threshold": True}
        await message.answer("🌡 Введіть нове порогове значення температури (°C):")
        return

    if user_id in user_state and user_state[user_id].get("awaiting_temp_threshold"):
        try:
            temp = float(text)
        except ValueError:
            await message.answer("❌ Введіть коректне числове значення температури.")
            return
        user_state[user_id] = {
            "temp": temp,
            "awaiting_humidity_threshold": True
        }
        await message.answer("💧 Введіть нове порогове значення вологості (%):")
        return

    if user_id in user_state and user_state[user_id].get("awaiting_humidity_threshold"):
        try:
            humidity = float(text)
        except ValueError:
            await message.answer("❌ Введіть коректне числове значення вологості.")
            return

        temp = user_state[user_id]["temp"]
        user_state.pop(user_id, None)

        try:
            response = requests.get(f"{ESP_URL}?temp={temp}&humidity={humidity}", timeout=5)
            if response.ok:
                await message.answer(
                    f"✅ Порогові значення оновлено:\n"
                    f"🌡 Температура: {temp} °C\n"
                    f"💧 Вологість: {humidity} %",
                    reply_markup=wan_keyboard
                )
            else:
                await message.answer("❌ Помилка при збереженні порогів на ESP.", reply_markup=wan_keyboard)
        except Exception as e:
            print(f"❌ Помилка при з'єднанні з ESP: {e}")
            await message.answer("❌ Не вдалося з'єднатися з ESP. Перевірте з'єднання.", reply_markup=wan_keyboard)
        return

    # 📊 Прогноз параметра
    if text == "📊 Прогноз параметру на N годин":
        user_state[user_id] = {"awaiting_forecast_param": True}
        await message.answer("🧪 Введіть назву параметру (temperature, humidity, pressure, altitude, gasValue):")
        return

    if user_id in user_state and user_state[user_id].get("awaiting_forecast_param"):
        param = text
        allowed = ["temperature", "humidity", "pressure", "altitude", "gasValue"]
        if param not in allowed:
            await message.answer("❌ Невірний параметр. Виберіть з: temperature, humidity, pressure, altitude, gasValue.")
            return

        user_state[user_id] = {
            "forecast_param_selected": param,
            "awaiting_forecast_hours": True
        }
        await message.answer(f"⏳ Скільки годин уперед ви хочете передбачити параметр <b>{param}</b>? Введіть число:", parse_mode="HTML")
        return

    if user_id in user_state and user_state[user_id].get("awaiting_forecast_hours"):
        try:
            hours = int(text)
            if hours <= 0 or hours > 1000:
                raise ValueError
        except ValueError:
            await message.answer("❌ Введіть коректне число годин (1–1000).")
            return

        param = user_state[user_id]["forecast_param_selected"]
        user_state.pop(user_id, None)

        data = get_data_from_google_sheet()
        if not data:
            await message.answer("❌ Не вдалося отримати дані з Google Sheets.", reply_markup=wan_keyboard)
            return

        import re
        def extract_number(value_str):
            try:
                match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value_str)
                if match:
                    return float(match.group())
            except:
                pass
            return None

        param_data = [
            {
                "time": datetime.strptime(i["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                "value": extract_number(i.get(param, "0"))
            }
            for i in data
            if "timestamp" in i and extract_number(i.get(param, "0")) is not None
        ]

        if len(param_data) < 2:
            await message.answer("❌ Недостатньо даних для прогнозу.", reply_markup=wan_keyboard)
            return

        x = [(i["time"] - param_data[0]["time"]).total_seconds() / 3600 for i in param_data]
        y = [i["value"] for i in param_data]
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_xx = sum(xi ** 2 for xi in x)

        a = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
        b = (sum_y - a * sum_x) / n

        future_x = x[-1] + hours
        predicted = a * future_x + b

        units = {
            "temperature": "°C",
            "humidity": "%",
            "pressure": "hPa",
            "altitude": "m",
            "gasValue": "ppm"
        }

        await message.answer(
            f"📊 <b>Прогноз параметру {param} через {hours} год:</b>\n"
            f"🔮 Очікуване значення: <b>{predicted:.2f}</b> {units.get(param, '')}",
            parse_mode="HTML",
            reply_markup=wan_keyboard
        )
        return

    # 🌍 Почати користування
    if text == "🌍 Почати користування":
        user_state.pop(user_id, None)
        await message.answer("Виберіть дію:", reply_markup=wan_keyboard)
        return

    elif text == "ℹ️ Переглянути історію параметрів мікроклімату":
        await message.answer("🔗 [Історія (WAN)](https://surl.li/harpcn)", parse_mode="Markdown", reply_markup=wan_keyboard)
        return

    elif text == "🌤️ Перехід до головної сторінки веб-інтерфейсу (LAN)":
        await message.answer("🔗 [Дані (WAN)](https://duck-liked-slowly.ngrok-free.app/)", parse_mode="Markdown", reply_markup=wan_keyboard)
        return

    elif text == "📋 Переглянути поточні параметри мікроклімату":
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
        return

    elif text == "📈 Переглянути середні значення параметрів мікроклімату за дату":
        await message.answer("🗓 Введіть дату у форматі YYYY-MM-DD:")
        user_state[user_id] = {"awaiting_date": True}
        return

    elif text == "🔙 Назад":
        user_state.pop(user_id, None)
        await message.answer("Оберіть потрібну дію:", reply_markup=main_keyboard)
        return

    if user_id in user_state and user_state[user_id].get("awaiting_date"):
        try:
            dt_obj = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            await message.answer("❌ Неправильний формат дати. Введіть у форматі YYYY-MM-DD.")
            return

        data = get_data_from_google_sheet()
        if data:
            filtered = [item for item in data if "timestamp" in item and match_date(item["timestamp"], dt_obj)]
            import re
            def extract_number(value_str):
                try:
                    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value_str)
                    if match:
                        return float(match.group())
                except:
                    pass
                return 0.0

            if filtered:
                temp = sum(extract_number(i["temperature"]) for i in filtered) / len(filtered)
                hum = sum(extract_number(i["humidity"]) for i in filtered) / len(filtered)
                press = sum(extract_number(i["pressure"]) for i in filtered) / len(filtered)
                alt = sum(extract_number(i["altitude"]) for i in filtered) / len(filtered)
                gas = sum(extract_number(i["gasValue"]) for i in filtered) / len(filtered)

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

        user_state.pop(user_id, None)
        return

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
