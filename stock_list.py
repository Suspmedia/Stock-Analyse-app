import pandas as pd
import streamlit as st
import requests
import time
from datetime import datetime, timedelta  # ✅ Added timedelta import
import os
import json

# Comprehensive fallback list (updated quarterly)
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR",
    "KOTAKBANK", "BAJFINANCE", "LT", "HCLTECH", "TCS",
    "MARUTI", "ITC", "NTPC", "ONGC", "POWERGRID",
    "ULTRACEMCO", "NESTLEIND", "WIPRO", "HDFCLIFE", "DRREDDY"
]

def get_cached_stocks():
    cache_file = "fo_stocks_cache.json"
    if os.path.exists(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_time < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    return None

def update_cache(stocks):
    with open("fo_stocks_cache.json", "w") as f:
        json.dump(stocks, f)

def get_fo_stocks_from_yfinance():
    try:
        nifty_50 = pd.read_html("https://en.wikipedia.org/wiki/NIFTY_50")[1]
        return sorted(nifty_50["Symbol"].tolist())
    except:
        return None

def get_fo_stocks():
    cached = get_cached_stocks()
    if cached:
        return cached

    stocks = get_fo_stocks_from_yfinance()
    if stocks:
        update_cache(stocks)
        return stocks

    try:
        today = datetime.now().strftime("%d%m%Y")
        url = f"https://archives.nseindia.com/content/fo/fo_mktlots_{today}.csv"
        df = pd.read_csv(url)
        stocks = sorted(df["SYMBOL"].unique().tolist())
        update_cache(stocks)
        return stocks
    except:
        pass

    st.warning("Using default stock list - consider manual update")
    update_cache(DEFAULT_FO_STOCKS)
    return DEFAULT_FO_STOCKS
