from flask import Flask, request, jsonify
from threading import Thread
import os

app = Flask(__name__)

# Храним текущие пороги в памяти
current_thresholds = {
    "temp": 25,
    "humidity": 60
}

@app.route('/get-thresholds')
def get_thresholds():
    return jsonify(current_thresholds)

@app.route('/set-thresholds')
def set_thresholds():
    try:
        temp = float(request.args.get("temp", ""))
        humidity = float(request.args.get("humidity", ""))
        current_thresholds["temp"] = temp
        current_thresholds["humidity"] = humidity
        return "OK", 200
    except:
        return "Invalid parameters", 400


@app.route('/')
def home():
    return "✅ I'm alive"


def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def keep_alive():
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()
