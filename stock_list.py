import requests
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Fallback list of common F&O stocks
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR"
]

def get_fo_stocks():
    """Fetch F&O stocks from NSE with fallback to cached/default list"""
    url = "https://www.nseindia.com/api/master-fo-symbols"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        # Create session and set cookies
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        
        # Get F&O symbols
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not isinstance(data, list):
            st.warning("Unexpected API response format, using fallback data")
            return DEFAULT_FO_STOCKS
            
        symbols = [item["symbol"] for item in data if item.get("instrumentType") == "OPTSTK"]
        unique_symbols = sorted(list(set(symbols)))
        
        if not unique_symbols:
            return DEFAULT_FO_STOCKS
        return unique_symbols
        
    except Exception as e:
        st.warning(f"Couldn't fetch live F&O stocks (Error: {str(e)}). Using fallback list.")
        return DEFAULT_FO_STOCKS
