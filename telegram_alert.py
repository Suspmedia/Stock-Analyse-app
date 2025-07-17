import requests
import streamlit as st
import csv
import os
from datetime import datetime

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Telegram Error: {e}")
        return False

def log_trade(row):
    file = "trade_log.csv"
    file_exists = os.path.exists(file)
    with open(file, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Signal", "Entry", "Target", "Stop Loss", "Strategy", "Expiry"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            row["Signal"],
            row["Entry"],
            row["Target"],
            row["Stop Loss"],
            row["Strategy"],
            row["Expiry"]
        ])

def load_trade_log():
    file = "trade_log.csv"
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame()
