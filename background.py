from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

# Изначальные пороговые значения
thresholds = {
    'temp': 25,
    'humidity': 60
}

@app.route('/')
def home():
    return "I'm alive"

@app.route('/set-thresholds', methods=['GET'])
def set_thresholds():
    temp = request.args.get('temp', type=float)
    humidity = request.args.get('humidity', type=float)

    if temp is not None and humidity is not None:
        thresholds['temp'] = temp
        thresholds['humidity'] = humidity
        return jsonify({"status": "success", "message": "Thresholds updated"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

@app.route('/get-thresholds', methods=['GET'])
def get_thresholds():
    return jsonify(thresholds)

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
