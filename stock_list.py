import requests
import pandas as pd
import streamlit as st
import time
from datetime import datetime, timedelta
import os

# Extended fallback list (updated July 2024)
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR",
    "KOTAKBANK", "BAJFINANCE", "LT", "HCLTECH", "TCS",
    "MARUTI", "ITC", "NTPC", "ONGC", "POWERGRID",
    "ULTRACEMCO", "NESTLEIND", "WIPRO", "HDFCLIFE", "DRREDDY"
]

def get_nse_headers():
    """Generate realistic browser headers"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Origin": "https://www.nseindia.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

def get_fo_stocks():
    """Main function with multiple fallback layers"""
    # Method 1: Try official NSE API with proper session
    try:
        session = requests.Session()
        
        # Initial request to set cookies
        session.get("https://www.nseindia.com", headers=get_nse_headers(), timeout=10)
        time.sleep(2)  # Critical delay
        
        # API request
        response = session.get(
            "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",
            headers=get_nse_headers(),
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        if "data" in data:
            return sorted(list(set(item["symbol"] for item in data["data"])))
    except Exception as e:
        st.warning(f"API attempt failed: {str(e)}")

    # Method 2: Try archived CSV
    try:
        today = datetime.now().strftime("%d%m%Y")
        url = f"https://archives.nseindia.com/content/fo/fo_mktlots_{today}.csv"
        df = pd.read_csv(url)
        return sorted(df["SYMBOL"].unique().tolist())
    except:
        pass

    # Method 3: Try static underlying list
    try:
        url = "https://www.nseindia.com/products/content/derivatives/equities/fo_underlying.htm"
        response = requests.get(url, headers=get_nse_headers(), timeout=15)
        tables = pd.read_html(response.text)
        if tables:
            return sorted(tables[0]["SYMBOL"].dropna().unique().tolist())
    except:
        pass

    # Method 4: Cached version
    cache_file = "fo_stocks_cache.json"
    try:
        if os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < timedelta(days=1):
                with open(cache_file, "r") as f:
                    return sorted(json.load(f))
    except:
        pass

    # Final fallback
    st.warning("Using default stock list")
    return DEFAULT_FO_STOCKS
