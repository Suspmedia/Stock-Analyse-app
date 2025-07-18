import requests
import pandas as pd
import streamlit as st
import time

DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR"
]

def get_nse_session():
    """Create session with proper cookies and headers"""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        # Initial request to set cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(2)  # Important delay
        return session
    except Exception as e:
        st.warning(f"Session creation failed: {str(e)}")
        return None

def get_fo_stocks():
    """Fetch F&O stocks with multiple fallback methods"""
    # Method 1: Try NSE API
    session = get_nse_session()
    if session:
        try:
            url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"  # Alternative index
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com/market-data/live-equity-market"
            }
            
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data:
                return sorted(list(set(item["symbol"] for item in data["data"])))
        except Exception as e:
            st.warning(f"API Error: {str(e)}")

    # Method 2: Try static CSV fallback
    try:
        url = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
        df = pd.read_csv(url)
        return sorted(df["SYMBOL"].unique().tolist())
    except:
        pass

    # Final fallback
    return DEFAULT_FO_STOCKS
