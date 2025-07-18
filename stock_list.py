import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Fallback list of common F&O stocks
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR"
]

def get_nse_session():
    """Create a session with proper NSE cookies"""
    session = requests.Session()
    try:
        # First request to set cookies
        session.get(
            "https://www.nseindia.com",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            },
            timeout=10
        )
        return session
    except Exception as e:
        st.warning(f"Session creation failed: {str(e)}")
        return None

def get_fo_stocks():
    """Fetch F&O stocks from NSE with proper API handling"""
    session = get_nse_session()
    if not session:
        return DEFAULT_FO_STOCKS

    try:
        # New working API endpoint for F&O stocks
        url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
        
        response = session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com/market-data/live-equity-market"
            },
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        if "data" not in data:
            raise ValueError("Unexpected API response format")
            
        symbols = [item["symbol"] for item in data["data"]]
        return sorted(list(set(symbols)))  # Remove duplicates
    
    except Exception as e:
        st.warning(f"Failed to fetch F&O stocks: {str(e)}. Using fallback list.")
        return DEFAULT_FO_STOCKS
