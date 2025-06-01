from flask import Flask, request
import requests
import os
from threading import Thread

app = Flask(__name__)

# Твой токен Telegram-бота и Chat ID (найди свой chat_id через BotFather или другой способ)
TOKEN = "7639996461:AAE1Grm61BEjUb6uGqdIz1pvmTO5z4n6-Ak"
CHAT_ID = "<879978878>"

# URL API Telegram для отправки сообщений
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Храним последний IP для отправки через бота
last_esp_ip = None

# Обработчик для "/update_ip" (получение IP от ESP8266)
@app.route('/update_ip', methods=['POST'])
def update_ip():
    global last_esp_ip
    data = request.get_json()
    
    # Получаем IP из тела запроса
    esp_ip = data.get("esp_ip", None)
    
    if esp_ip:
        # Сохраняем последний IP
        last_esp_ip = esp_ip
        # Отправляем IP в Telegram
        message = f"📡 Новый IP ESP8266: {esp_ip}"
        send_telegram_message(message)
        return "IP обновлен", 200
    else:
        return "IP не найден", 400

# Функция для отправки сообщений в Telegram
def send_telegram_message(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(TELEGRAM_URL, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
