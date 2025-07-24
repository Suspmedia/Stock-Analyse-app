import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"

# --- Full stock_engine.py with robust logging ---
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime, timedelta
import numpy as np
import streamlit as st

# ------------------ Fetch OHLC + Indicators ------------------
def fetch_data(symbol):
    try:
        df = yf.download(symbol + ".NS", period="10d", interval="5m", progress=False)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}.NS")

        df.dropna(inplace=True)
        df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
        macd = MACD(close=df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_signal"] = macd.macd_signal()
        df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df["Volume"].cumsum()
        return df
    except Exception as e:
        st.error(f"fetch_data Error for {symbol}: {e}")
        return None

# ------------------ Signal Logic ------------------
def evaluate_signal(df, strategy):
    last = df.iloc[-1]
    if strategy == "Safe":
        if last["RSI"] < 35 and last["MACD"] > last["MACD_signal"] and last["Close"] > last["VWAP"]:
            return "BUY"
    elif strategy == "Min Investment":
        if last["RSI"] < 30 and last["Close"] < last["VWAP"]:
            return "BUY"
    elif strategy == "Max Profit":
        if last["MACD"] > last["MACD_signal"] and last["RSI"] < 40:
            return "BUY"
    elif strategy == "Reversal":
        if last["RSI"] < 25:
            return "BUY"
        elif last["RSI"] > 75:
            return "SELL"
    elif strategy == "Breakout":
        if last["Close"] > df["Close"].rolling(20).max().iloc[-1]:
            return "BUY"
    return None

# ------------------ Signal Generator ------------------
def generate_stock_signals(symbol, strategy, strike_type, expiry):
    df = fetch_data(symbol)
    if df is None: return pd.DataFrame()
    signal = evaluate_signal(df, strategy)
    if signal is None: return pd.DataFrame()

    last_price = df["Close"].iloc[-1]
    atm = round(last_price / 50) * 50
    if strike_type == "ATM":
        strike = atm
    elif strike_type == "ITM":
        strike = atm - 100
    else:
        strike = atm + 100

    option_type = "CE" if signal == "BUY" else "PE"
    entry = round(last_price % 100 + 40, 2)
    target = round(entry * 2, 2)
    sl = round(entry * 0.5, 2)

    return pd.DataFrame({
        "Signal": [f"{symbol} {signal} {strike} {option_type}"],
        "Entry": [f"₹{entry}"],
        "Target": [f"₹{target}"],
        "Stop Loss": [f"₹{sl}"],
        "Strategy": [strategy],
        "Expiry": [expiry.strftime("%d %b %Y")]
    })

# ------------------ Strategy Backtest ------------------
def backtest_strategy(symbol, strategy):
    result = []
    today = datetime.now()
    for i in range(5):
        date_check = today - timedelta(days=i+1)
        try:
            df = yf.download(symbol + ".NS", start=date_check.strftime("%Y-%m-%d"),
                             end=(date_check + timedelta(days=1)).strftime("%Y-%m-%d"),
                             interval="5m", progress=False)
            if df.empty:
                continue

            df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
            macd = MACD(close=df["Close"])
            df["MACD"] = macd.macd()
            df["MACD_signal"] = macd.macd_signal()
            df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df["Volume"].cumsum()

            sig = evaluate_signal(df, strategy)
            if sig == "BUY":
                entry = df["Close"].iloc[-2]
                exit = df["Close"].iloc[-1]
                result.append({
                    "Date": date_check.strftime("%d-%b"),
                    "Strategy": strategy,
                    "Signal": "BUY",
                    "Entry": round(entry, 2),
                    "Exit": round(exit, 2),
                    "Result": "Win" if exit > entry else "Loss"
                })
        except Exception as e:
            st.warning(f"Backtest failed on {date_check.strftime('%Y-%m-%d')}: {e}")

    return pd.DataFrame(result)
