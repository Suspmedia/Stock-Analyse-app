import pandas as pd
import requests

def get_fo_stocks():
    url = "https://www.nseindia.com/api/master-fo-symbols"
    headers = {"User-Agent": "Mozilla/5.0"}

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(url, headers=headers)
    data = response.json()

    symbols = [item["symbol"] for item in data if item.get("instrumentType") == "OPTSTK"]
    return sorted(list(set(symbols)))
