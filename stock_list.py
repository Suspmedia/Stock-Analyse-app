import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# Fallback list (only used if ALL methods fail)
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR"
]

def get_nse_session():
    """Creates a session with proper NSE cookies"""
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

def fetch_live_fo_stocks():
    """Fetches ALL F&O stocks from NSE with proper API handling"""
    session = get_nse_session()
    if not session:
        return None

    try:
        # New NSE API endpoint for F&O stocks
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
        st.error(f"Failed to fetch F&O stocks: {str(e)}")
        return None

def get_fo_stocks():
    """Main function with fallback logic"""
    # Try live fetch first
    live_stocks = fetch_live_fo_stocks()
    if live_stocks:
        return live_stocks
    
    # If live fetch fails, try secondary method
    st.warning("Primary API failed, trying alternative source...")
    try:
        # Alternative method - web scraping from NSE website
        session = get_nse_session()
        if session:
            response = session.get(
                "https://www.nseindia.com/products/content/derivatives/equities/fo_underlying.htm",
                timeout=15
            )
            if response.status_code == 200:
                # Parse HTML table (example - may need adjustment)
                dfs = pd.read_html(response.text)
                if dfs and len(dfs) > 0:
                    symbols = dfs[0].iloc[:, 0].dropna().tolist()
                    return sorted(list(set(symbols)))
    except:
        pass
    
    # Final fallback to default list
    st.warning("All methods failed, using default stock list")
    return DEFAULT_FO_STOCKS
