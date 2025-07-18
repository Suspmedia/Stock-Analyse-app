import requests
import pandas as pd
import streamlit as st
import time
from fake_useragent import UserAgent

# Extended fallback list
DEFAULT_FO_STOCKS = [
    "RELIANCE", "TATASTEEL", "HDFCBANK", "ICICIBANK", "INFY",
    "BHARTIARTL", "SBIN", "ADANIPORTS", "TATAMOTORS", "HINDUNILVR",
    "KOTAKBANK", "BAJFINANCE", "LT", "HCLTECH", "ASIANPAINT",
    "MARUTI", "TITAN", "NTPC", "ONGC", "POWERGRID"
]

def get_nse_headers():
    """Generate dynamic headers with random user agent"""
    ua = UserAgent()
    return {
        "User-Agent": ua.random,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.nseindia.com/",
        "Origin": "https://www.nseindia.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

def get_nse_session():
    """Create authenticated session with cookies"""
    session = requests.Session()
    try:
        # First request to set cookies
        session.get(
            "https://www.nseindia.com",
            headers=get_nse_headers(),
            timeout=10
        )
        time.sleep(2)  # Critical delay for cookie setting
        return session
    except Exception as e:
        st.warning(f"Session creation failed: {str(e)}")
        return None

def get_fo_stocks():
    """Fetch F&O stocks with multiple fallback methods"""
    # Method 1: Try live API with proper authentication
    session = get_nse_session()
    if session:
        try:
            url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
            response = session.get(
                url,
                headers=get_nse_headers(),
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            if "data" in data:
                symbols = [item["symbol"] for item in data["data"]]
                return sorted(list(set(symbols)))
        except Exception as e:
            st.warning(f"API Error: {str(e)}")

    # Method 2: Try web scraping fallback
    try:
        from bs4 import BeautifulSoup
        response = requests.get(
            "https://www.nseindia.com/products/content/derivatives/equities/fo_underlying.htm",
            headers=get_nse_headers(),
            timeout=15
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'octable'})
        symbols = [row.find_all('td')[0].text.strip() for row in table.find_all('tr')[1:]]
        return sorted(list(set(symbols)))
    except:
        pass

    # Method 3: Static CSV fallback
    try:
        url = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
        df = pd.read_csv(url)
        return sorted(df["SYMBOL"].unique().tolist())
    except:
        pass

    # Final fallback
    return DEFAULT_FO_STOCKS
