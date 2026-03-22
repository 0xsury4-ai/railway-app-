import os
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8651110879:AAHOFcHVVazuUaGhxFTfNjVwFIVJwEgwVkg"  # set in Render dashboard
API_KEY = "30c382602bfa67c8a7c580e6cfe2becb"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def get_train_status(train_number, date):
    url = f"http://indianrailapi.com/api/v2/livetrainstatus/apikey/{API_KEY}/trainnumber/{train_number}/date/{date}/"
    r = requests.get(url, timeout=10)
    return r.json()

def format_status(data):
    if data.get("ResponseCode") != "200":
        return "Could not fetch status. Check train number."

    train = data["TrainNumber"]
    route = data["TrainRoute"]
    current = data["CurrentStation"]
    current_code = current["StationCode"]

    idx = next((i for i, s in enumerate(route) if s["StationCode"] == current_code), None)
    prev = route[idx - 1] if idx and idx > 0 else None
    nxt  = route[idx + 1] if idx is not None and idx < len(route) - 1 else None

    lines = [f"Train {train} - Live Status\n"]

    if prev:
        lines.append(f"[Previous] {prev['StationName']} ({prev['StationCode']})")
        lines.append(f"  Left at : {prev['ActualDeparture']}  Delay: {prev['DelayInDeparture']}\n")

    lines.append(f"[NOW] {current['StationName']} ({current_code})")
    lines.append(f"  Arrived : {current['ActualArrival']}")
    lines.append(f"  Departed: {current['ActualDeparture']}  Delay: {current['DelayInDeparture']}\n")

    if nxt:
        lines.append(f"[Next] {nxt['StationName']} ({nxt['StationCode']})")
        lines.append(f"  Sched arr : {nxt['ScheduleArrival']}")
        lines.append(f"  Est arr   : {nxt['ActualArrival']}  Delay: {nxt['DelayInArrival']}")

    return "\n".join(lines)

@app.route(f"/webhook", methods=["POST"])
def webhook():
    data = request.json
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()

    if not chat_id or not text:
        return "ok"

    parts = text.replace("/status", "").strip().split()

    if not parts or not parts[0].isdigit():
        send_message(chat_id,
            "Send your train number like this:\n/status 12565\n\nOr with a date:\n/status 12565 20260322")
        return "ok"

    train = parts[0]
    date = parts[1] if len(parts) > 1 else datetime.now().strftime("%Y%m%d")

    try:
        result = get_train_status(train, date)
        send_message(chat_id, format_status(result))
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

    return "ok"

if __name__ == "__main__":
    app.run(debug=True)
