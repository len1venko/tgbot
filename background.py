from flask import Flask, request, jsonify
from threading import Thread
import json
import os

app = Flask(__name__)
THRESHOLD_FILE = "thresholds.json"

# Загружаем пороги из файла или ставим дефолт
def load_thresholds():
    if os.path.exists(THRESHOLD_FILE):
        with open(THRESHOLD_FILE, "r") as f:
            return json.load(f)
    else:
        return {"temp": 25, "humidity": 60}

# Сохраняем пороги в файл
def save_thresholds(thresholds):
    with open(THRESHOLD_FILE, "w") as f:
        json.dump(thresholds, f)

@app.route('/')
def index():
    return "Сервер працює!"

@app.route('/get-thresholds')
def get_thresholds():
    thresholds = load_thresholds()
    return jsonify(thresholds)

@app.route('/set-thresholds')
def set_thresholds():
    try:
        temp = float(request.args.get("temp"))
        humidity = float(request.args.get("humidity"))
        thresholds = {"temp": temp, "humidity": humidity}
        save_thresholds(thresholds)
        return "OK", 200
    except:
        return "Invalid parameters", 400



def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def keep_alive():
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()
