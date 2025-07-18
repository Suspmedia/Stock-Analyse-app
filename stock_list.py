import requests
import streamlit as st
import pandas as pd

# Default fallback if all fetch attempts fail
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR"
]

def get_nse_session():
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9"
        }, timeout=10)
        return session
    except Exception as e:
        st.warning(f"Session creation failed: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_live_fo_stocks():
    session = get_nse_session()
    if not session:
        return None
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
        res = session.get(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com/market-data/live-equity-market"
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
        return sorted(set(item["symbol"] for item in data["data"]))
    except Exception as e:
        st.error(f"Live F&O fetch failed: {e}")
        return None

@st.cache_data(ttl=3600)
def get_fo_stocks():
    live = fetch_live_fo_stocks()
    if live:
        return live

    # Try alternative scraping
    st.warning("Primary API failed, trying alternative source...")
    try:
        session = get_nse_session()
        url = "https://www.nseindia.com/products/content/derivatives/equities/fo_underlying.htm"
        res = session.get(url, timeout=10)
        dfs = pd.read_html(res.text)
        if dfs:
            alt = dfs[0].iloc[:, 0].dropna().unique().tolist()
            return sorted(alt)
    except:
        pass

    st.warning("All methods failed. Using default fallback list.")
    return DEFAULT_FO_STOCKS
