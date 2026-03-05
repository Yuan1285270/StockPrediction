from datetime import datetime
import pandas as pd
import yfinance as yf


def safe_info(tk: yf.Ticker) -> dict:
    try:
        return tk.info or {}
    except Exception:
        return {}


def get_price(tk: yf.Ticker):
    info = safe_info(tk)
    return info.get("currentPrice") or info.get("regularMarketPrice")


def get_trailing_eps(tk: yf.Ticker):
    info = safe_info(tk)
    return info.get("trailingEps")


def get_shares_outstanding(tk: yf.Ticker):
    info = safe_info(tk)
    sh = info.get("sharesOutstanding")
    return float(sh) if isinstance(sh, (int, float)) and sh > 0 else None


def get_dividend_by_year(dividends: pd.Series):
    """Return {year: total_dividend_per_share}"""
    if dividends is None or dividends.empty:
        return {}
    df = dividends.reset_index()
    df.columns = ["Date", "Dividend"]
    df["Year"] = df["Date"].dt.year
    return df.groupby("Year")["Dividend"].sum().to_dict()


def latest_dividend_snapshot(div_by_year: dict):
    """Return (latest_year, latest_year_total_dividend)."""
    if not div_by_year:
        return None, 0.0
    y = max(div_by_year.keys())
    return int(y), float(div_by_year[y])


def latest_news_ts(tk: yf.Ticker):
    """Return latest news publish timestamp (epoch seconds), if available."""
    try:
        news = tk.news or []
    except Exception:
        news = []

    if not news:
        return None

    times = []
    for item in news:
        t = item.get("providerPublishTime")
        if isinstance(t, (int, float)):
            times.append(int(t))
    return max(times) if times else None