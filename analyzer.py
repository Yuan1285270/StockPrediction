from datetime import datetime
import yfinance as yf
import pandas as pd
import config

from data_fetcher import (
    get_price,
    get_trailing_eps,
    get_shares_outstanding,
    get_dividend_by_year,
    get_annual_eps_by_year,
)


def avg_payout_ratio(div_by_year: dict, eps_by_year: dict, years: int):
    """Average payout ratio over the last N dividend years.

    Taiwan companies pay dividends in year y out of the earnings of fiscal
    year y-1, so each year's dividend is divided by the previous year's EPS.
    Years with non-positive or missing EPS are skipped, and each ratio is
    capped at config.MAX_PAYOUT_RATIO so a one-off payout from retained
    earnings does not inflate the estimate.

    Returns: (avg_ratio, n_years_used) or (None, 0)
    """
    if not div_by_year or not eps_by_year:
        return None, 0

    cur_year = datetime.now().year
    ratios = []
    for y in range(cur_year - 1, cur_year - 1 - years, -1):
        eps = eps_by_year.get(y - 1)
        if eps is None or eps <= 0:
            continue
        ratio = div_by_year.get(y, 0.0) / eps
        ratios.append(min(ratio, config.MAX_PAYOUT_RATIO))

    if not ratios:
        return None, 0
    return sum(ratios) / len(ratios), len(ratios)


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
      - payout_ratio = avg of (dividend paid in year y / EPS of year y-1)
        over the last N years
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
    eps_by_year = get_annual_eps_by_year(tk)
    payout, payout_years = avg_payout_ratio(div_by_year, eps_by_year, years_for_payout)
    if payout is None:
        return None, tk

    # A company cannot pay a negative dividend
    est_dividend = max(0.0, float(next_year_eps_est) * float(payout))
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
        "payout_years_used": payout_years,
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

    threshold_pct = float(yield_threshold) * 100.0
    if df_all.empty:
        print("沒有可計算的股票")
        return df_all, df_all

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_path = config.RESULT_DIR / f"yield_{ts}.csv"
    df_all.to_csv(all_path, index=False, encoding="utf-8-sig")
    print(f"輸出完成: {all_path}")

    df_high = df_all[df_all["est_yield_%"] >= threshold_pct]
    if not df_high.empty:
        high_path = config.RESULT_DIR / f"high_yield_{int(threshold_pct)}pct_{ts}.csv"
        df_high.to_csv(high_path, index=False, encoding="utf-8-sig")
        print(f"輸出完成: {high_path}")
    else:
        print(f"沒有大於{int(threshold_pct)}%的股票")
    return df_all, df_high
