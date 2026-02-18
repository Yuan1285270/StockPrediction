import yfinance as yf
import pandas as pd

def safe_info(tk):
    try:
        return tk.info or {}
    except Exception:
        return {}

def get_price(tk):
    info = safe_info(tk)
    return info.get("currentPrice") or info.get("regularMarketPrice")

def get_trailing_eps(tk):
    return safe_info(tk).get("trailingEps")

def get_shares_outstanding(tk):
    sh = safe_info(tk).get("sharesOutstanding")
    return float(sh) if isinstance(sh, (int, float)) and sh > 0 else None

def get_dividend_by_year(dividends):
    if dividends is None or dividends.empty:
        return {}
    df = dividends.reset_index()
    df.columns = ["Date", "Dividend"]
    df["Year"] = df["Date"].dt.year
    return df.groupby("Year")["Dividend"].sum().to_dict()

def latest_news_ts(tk):
    try:
        news = tk.news or []
    except Exception:
        news = []
    times = [item.get("providerPublishTime") for item in news if isinstance(item.get("providerPublishTime"), (int, float))]
    return max(times) if times else None