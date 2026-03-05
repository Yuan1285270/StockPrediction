from datetime import datetime
from fileinput import filename
import yfinance as yf
import pandas as pd
import config

from data_fetcher import (
    get_price,
    get_trailing_eps,
    get_shares_outstanding,
    get_dividend_by_year,
)


def avg_payout_ratio(div_by_year: dict, eps_ttm: float, years: int):
    """Average payout ratio over last N years: annual_dividend / eps_ttm."""
    if not div_by_year or not eps_ttm or eps_ttm <= 0:
        return None

    cur_year = datetime.now().year
    ratios = []
    for y in range(cur_year - 1, cur_year - 1 - years, -1):
        if y in div_by_year:
            ratios.append(div_by_year[y] / eps_ttm)

    if not ratios:
        return None
    return sum(ratios) / len(ratios)


def estimate_next_quarter_eps_from_quarterly(tk: yf.Ticker):
    """Estimate next-quarter EPS using quarterly net income / shares.

    Steps:
      1) sharesOutstanding from tk.info
      2) quarterly income statement net income row
      3) quarter EPS series = netIncome / shares
      4) next-quarter EPS = conservative weighted moving average of recent quarters

    Returns:
      (eps_q_series, next_q_eps_est)
      - eps_q_series: list[float] (most recent first in many yfinance outputs)
      - next_q_eps_est: float
      or (None, None) if insufficient.
    """
    shares = get_shares_outstanding(tk)
    if not shares:
        return None, None

    stmt = None
    try:
        stmt = tk.quarterly_income_stmt
    except Exception:
        stmt = None

    if stmt is None or getattr(stmt, "empty", True):
        try:
            stmt = tk.quarterly_financials  # older yfinance
        except Exception:
            stmt = None

    if stmt is None or getattr(stmt, "empty", True):
        return None, None

    # Find net income row (yfinance label varies)
    net_income_row = None
    for key in [
        "Net Income",
        "NetIncome",
        "Net Income Common Stockholders",
        "Net Income Continuous Operations",
    ]:
        if key in stmt.index:
            net_income_row = key
            break

    if net_income_row is None:
        return None, None

    net_incomes = stmt.loc[net_income_row].dropna()
    if net_incomes.empty:
        return None, None

    # Compute quarter EPS series
    eps_q_series = (net_incomes.astype(float) / shares).tolist()

    if len(eps_q_series) < 2:
        return eps_q_series, float(eps_q_series[-1])

    # ✅ 這裡只修你貼的原檔那個「註解縮排會炸」的問題（不改邏輯）
    # Simple average of recent 3 quarters (align with "use first three quarters to estimate next")
    recent = eps_q_series[:3]
    if not recent:
        return None, None
    next_q_eps_est = sum(recent) / len(recent)

    return eps_q_series, float(next_q_eps_est)


def estimate_yield_for_symbol(symbol: str, years_for_payout: int, trigger_reasons=None):
    """Compute estimated yield based on Next-Q EPS estimate.

    Logic:
      - Get price and trailingEps (TTM)
      - Estimate next-quarter EPS (from quarterly statements)
        - fallback to base_q_eps = trailingEps/4 if quarterly data missing
      - next_year_eps_est = next_q_eps_est * 4
      - payout_ratio = avg dividend payout ratio from last N years
      - estimated_dividend = next_year_eps_est * payout_ratio
      - estimated_yield = estimated_dividend / price

    Returns: (row_dict_or_None, tk)
    """
    tk = yf.Ticker(symbol)

    price = get_price(tk)
    eps_ttm = get_trailing_eps(tk)
    dividends = tk.dividends

    if not price or not eps_ttm or eps_ttm <= 0:
        return None, tk

    # Next-quarter EPS estimate (yfinance-only, from quarterly net income)
    eps_q_series, next_q_eps_est = estimate_next_quarter_eps_from_quarterly(tk)

    base_q_eps = float(eps_ttm) / 4.0

    # Fallback: if quarterly data missing, use base_q_eps
    if next_q_eps_est is None:
        next_q_eps_est = base_q_eps

    next_year_eps_est = float(next_q_eps_est) * 4.0

    # payout ratio
    div_by_year = get_dividend_by_year(dividends)
    payout = avg_payout_ratio(div_by_year, float(eps_ttm), years_for_payout)
    if payout is None:
        return None, tk

    est_dividend = float(next_year_eps_est) * float(payout)
    est_yield = float(est_dividend) / float(price)

    row = {
        "symbol": symbol,
        "price": round(float(price), 2),

        # historical / baseline
        "trailing_eps_ttm": round(float(eps_ttm), 2),
        "base_q_eps": round(float(base_q_eps), 3),

        # next-quarter estimate (what your project claims)
        "next_q_eps_est": round(float(next_q_eps_est), 3),
        "next_year_eps_est": round(float(next_year_eps_est), 2),

        # payout + yield
        "avg_payout_ratio": round(float(payout), 3),
        "est_dividend": round(float(est_dividend), 2),
        "est_yield_%": round(float(est_yield) * 100, 2),
    }

    return row, tk


def yield_mode(symbols, years_for_payout, yield_threshold):
    rows = []
    for sym in symbols:
        try:
            row, _tk = estimate_yield_for_symbol(sym, years_for_payout, trigger_reasons=None)
            if row is not None:
                rows.append(row)
        except Exception as e:
            print(f"[WARN] {sym}: {e}")

    df_all = pd.DataFrame(rows)

    if not df_all.empty:
        df_all = df_all.sort_values("est_yield_%", ascending=False)

    df_high = df_all[df_all["est_yield_%"] >= 6]

    if not df_high.empty:
        filename = "result/high_yield.csv"
        df_high.to_csv(filename, index=False)
        print(f"輸出完成: {filename}")
    else:
        print("沒有大於6%的股票")
    return df_all, df_high