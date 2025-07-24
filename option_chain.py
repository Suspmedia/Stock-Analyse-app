# --- Improved option_chain.py with error handling and fallback ---
import requests
import pandas as pd
import streamlit as st


def get_oi_levels(stock):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com",
        "Accept-Language": "en-US,en;q=0.9"
    }
    url = f"https://www.nseindia.com/api/option-chain-equities?symbol={stock.upper()}"

    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise ValueError(f"NSE returned status code {response.status_code}")

        try:
            data = response.json()
        except Exception as e:
            st.error(f"Failed to decode NSE JSON: {e}")
            st.text(response.text[:500])  # show start of HTML error if any
            raise

        rows = []
        for d in data.get("records", {}).get("data", []):
            strike = d.get("strikePrice")
            ce = d.get("CE", {})
            pe = d.get("PE", {})

            rows.append({
                "strike": strike,
                "CE_price": ce.get("lastPrice", 0),
                "PE_price": pe.get("lastPrice", 0),
                "CE_OI": ce.get("openInterest", 0),
                "PE_OI": pe.get("openInterest", 0),
                "CE_vol": ce.get("totalTradedVolume", 0),
                "PE_vol": pe.get("totalTradedVolume", 0)
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("strike")

        return {"df": df}

    except Exception as e:
        st.error(f"Option Chain fetch failed: {e}")
        return {"df": pd.DataFrame()}
