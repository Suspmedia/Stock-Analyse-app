import requests
import pandas as pd

def get_oi_levels(stock):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.nseindia.com/api/option-chain-equities?symbol={stock.upper()}"

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(url, headers=headers)
    data = response.json()

    rows = []
    for d in data["records"]["data"]:
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
