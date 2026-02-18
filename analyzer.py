from datetime import datetime
import data_fetcher
import yfinance as yf

def avg_payout_ratio(div_by_year, eps_ttm, years):
    if not div_by_year or not eps_ttm or eps_ttm <= 0:
        return None
    cur_year = datetime.now().year
    ratios = [div_by_year[y] / eps_ttm for y in range(cur_year - 1, cur_year - 1 - years, -1) if y in div_by_year]
    return sum(ratios) / len(ratios) if ratios else None

def estimate_next_q_eps(tk):
    shares = data_fetcher.get_shares_outstanding(tk)
    if not shares: return None
    try:
        stmt = tk.quarterly_income_stmt
        if stmt.empty: stmt = tk.quarterly_financials
    except Exception: return None

    for key in ["Net Income", "NetIncome", "Net Income Common Stockholders"]:
        if key in stmt.index:
            eps_series = (stmt.loc[key].dropna().astype(float) / shares).tolist()
            recent = eps_series[:3]
            return sum(recent) / len(recent) if recent else None
    return None

def calculate_yield(symbol, years_for_payout):
    tk = yf.Ticker(symbol)
    price = data_fetcher.get_price(tk)
    eps_ttm = data_fetcher.get_trailing_eps(tk)
    
    if not price or not eps_ttm or eps_ttm <= 0:
        return None, tk

    # 估算 Next-Q EPS，若無資料則用 TTM/4 代替 
    next_q_eps = estimate_next_q_eps(tk) or (float(eps_ttm) / 4.0)
    next_year_eps = next_q_eps * 4.0
    
    div_by_year = data_fetcher.get_dividend_by_year(tk.dividends)
    payout = avg_payout_ratio(div_by_year, float(eps_ttm), years_for_payout)
    
    if payout is None:
        return None, tk

    est_div = next_year_eps * payout
    return {
        "symbol": symbol,
        "price": round(float(price), 2),
        "trailing_eps_ttm": round(float(eps_ttm), 2),
        "next_q_eps_est": round(float(next_q_eps), 3),
        "est_yield_%": round((est_div / price) * 100, 2),
        "avg_payout_ratio": round(float(payout), 3)
    }, tk