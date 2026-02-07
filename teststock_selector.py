import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

import yfinance as yf
import pandas as pd

# ========= 你要改的只有這裡 =========
SYMBOLS = [
    "1301.TW",  # 台塑
    "1303.TW",  # 南亞
    "1326.TW",  # 台化
    "2002.TW",  # 中鋼
    "2207.TW",  # 和泰車
    "2308.TW",  # 台達電
    "2327.TW",  # 國巨
    "2357.TW",  # 華碩
    "2379.TW",  # 瑞昱
    "2382.TW",  # 廣達
    "2395.TW",  # 研華
    "2408.TW",  # 南亞科
    "2412.TW",  # 中華電
    "2603.TW",  # 長榮
    "2609.TW",  # 陽明
    "2615.TW",  # 萬海
    "2884.TW",  # 玉山金
    "2891.TW",  # 中信金
    "2892.TW",  # 第一金
    "5871.TW",  # 中租-KY
]

YEARS_FOR_PAYOUT = 5       # 平均配息率使用年數
YIELD_THRESHOLD = 0.06     # 6%
STATE_FILE = Path("state.json")
# ====================================


# ---------- Data fetch helpers ----------
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


# ---------- Next-quarter EPS estimation (yfinance-only) ----------
def estimate_next_quarter_eps_from_quarterly(tk: yf.Ticker):
    """Estimate next-quarter EPS using quarterly net income / shares.

    Steps:
      1) sharesOutstanding from tk.info
      2) quarterly income statement net income row
      3) quarter EPS series = netIncome / shares
      4) next-quarter EPS = conservative weighted moving average of recent quarters

    Returns:
      (eps_q_series, next_q_eps_est)
      - eps_q_series: list[float] (most recent first)
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

    # Compute quarter EPS series (most recent first in many yfinance outputs)
    eps_q_series = (net_incomes.astype(float) / shares).tolist()

    if len(eps_q_series) < 2:
        return eps_q_series, float(eps_q_series[-1])

            # Simple average of recent 3 quarters (align with "use first three quarters to estimate next")
    recent = eps_q_series[:3]
    if not recent:
        return None, None
    next_q_eps_est = sum(recent) / len(recent)

    return eps_q_series, float(next_q_eps_est)


# ---------- Yield engine ----------
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

    print("\n=== All Estimated Yields (Next-Q EPS -> Next-Year EPS) ===")
    print(df_all if not df_all.empty else "(no valid rows)")

    if not df_all.empty:
        df_high = df_all[df_all["est_yield_%"] >= yield_threshold * 100]
    else:
        df_high = pd.DataFrame()

    print(f"\n=== High Yield (>= {int(yield_threshold*100)}%) ===")
    print(df_high if not df_high.empty else "(none)")

    return df_all, df_high


# ---------- Event-driven controller ----------
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def detect_triggers(symbol: str, eps_now, latest_div_year, latest_div_amt, news_ts_now, state: dict):
    """Compare current snapshot vs previous snapshot.

    Triggers:
      - EPS change (trailingEps)
      - Dividend latest year or amount change
      - News timestamp updated (aux)
    """
    prev = state.get(symbol, {})
    reasons = []

    # EPS trigger
    eps_prev = prev.get("trailing_eps_ttm")
    if eps_now is not None and eps_prev is not None:
        if round(float(eps_now), 4) != round(float(eps_prev), 4):
            reasons.append(f"EPS updated: {eps_prev} -> {eps_now}")
    elif eps_now is not None and eps_prev is None:
        reasons.append("EPS became available")

    # Dividend trigger
    div_year_prev = prev.get("latest_div_year")
    div_amt_prev = prev.get("latest_div_amt")
    if latest_div_year is not None:
        if div_year_prev is None:
            reasons.append("Dividend history became available")
        else:
            if int(latest_div_year) != int(div_year_prev):
                reasons.append(f"Dividend year updated: {div_year_prev} -> {latest_div_year}")
            if div_amt_prev is not None and round(float(latest_div_amt), 4) != round(float(div_amt_prev), 4):
                reasons.append(f"Dividend amount updated: {div_amt_prev} -> {latest_div_amt}")

    # News trigger (aux)
    news_prev = prev.get("latest_news_ts")
    if news_ts_now is not None and news_prev is not None:
        if int(news_ts_now) > int(news_prev):
            reasons.append("New news item detected")
    elif news_ts_now is not None and news_prev is None:
        reasons.append("News became available")

    return (len(reasons) > 0), reasons


def update_state_for_symbol(symbol: str, eps_now, latest_div_year, latest_div_amt, news_ts_now, state: dict):
    state[symbol] = {
        "trailing_eps_ttm": eps_now,
        "latest_div_year": latest_div_year,
        "latest_div_amt": latest_div_amt,
        "latest_news_ts": news_ts_now,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def event_mode(symbols, years_for_payout, yield_threshold, force_recalc_all=False):
    """Event-driven mode:
    - Detect triggers for each symbol
    - Recalculate yield only for triggered (or all if force_recalc_all)
    - Update state.json
    """
    state = load_state()
    triggered_symbols = []
    trigger_log = []

    # First pass: detect triggers
    for sym in symbols:
        try:
            tk = yf.Ticker(sym)

            eps_now = get_trailing_eps(tk)
            div_by_year = get_dividend_by_year(tk.dividends)
            latest_year, latest_amt = latest_dividend_snapshot(div_by_year)
            news_ts_now = latest_news_ts(tk)

            triggered, reasons = detect_triggers(sym, eps_now, latest_year, latest_amt, news_ts_now, state)
            update_state_for_symbol(sym, eps_now, latest_year, latest_amt, news_ts_now, state)

            if force_recalc_all:
                triggered = True
                if not reasons:
                    reasons = ["Forced recalculation"]

            if triggered:
                triggered_symbols.append(sym)
                trigger_log.append({"symbol": sym, "reasons": reasons})

        except Exception as e:
            trigger_log.append({"symbol": sym, "reasons": [f"ERROR: {e}"]})

    save_state(state)

    # Second pass: recalc yields for triggered
    rows = []
    for sym in triggered_symbols:
        try:
            reasons = next((x["reasons"] for x in trigger_log if x["symbol"] == sym), [])
            row, _tk = estimate_yield_for_symbol(sym, years_for_payout, trigger_reasons=reasons)
            if row is not None:
                rows.append(row)
        except Exception as e:
            trigger_log.append({"symbol": sym, "reasons": [f"RECALC ERROR: {e}"]})

    df_trig = pd.DataFrame(rows)
    if not df_trig.empty:
        df_trig = df_trig.sort_values("est_yield_%", ascending=False)

    print("\n=== Triggered Symbols (this run) ===")
    print(triggered_symbols if triggered_symbols else "(none)")

    print("\n=== Trigger Reasons ===")
    for item in trigger_log:
        print(f"- {item['symbol']}: " + " | ".join(item["reasons"]))

    print("\n=== Recalculated Yields (Triggered, Next-Q EPS based) ===")
    print(df_trig if not df_trig.empty else "(no triggered & valid rows)")

    if not df_trig.empty:
        df_high = df_trig[df_trig["est_yield_%"] >= yield_threshold * 100]
    else:
        df_high = pd.DataFrame()

    print(f"\n=== High Yield among Triggered (>= {int(yield_threshold*100)}%) ===")
    print(df_high if not df_high.empty else "(none)")

    return df_trig, df_high


# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser(
        description="Taiwan stock selector (yfinance-only): estimate next-quarter EPS -> estimate yield, with event-driven trigger."
    )
    p.add_argument(
        "--mode",
        choices=["yield", "event"],
        default="event",
        help="yield: compute for all symbols; event: detect updates and recalc only triggered symbols",
    )
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Optional comma-separated symbols, e.g., 2330.TW,2317.TW",
    )
    p.add_argument("--years", type=int, default=YEARS_FOR_PAYOUT, help="Years for payout ratio averaging")
    p.add_argument(
        "--threshold",
        type=float,
        default=YIELD_THRESHOLD,
        help="Yield threshold (e.g., 0.06 for 6%%)",
    )
    p.add_argument(
        "--force-all",
        action="store_true",
        help="(event mode) force recalculation for all symbols this run",
    )
    return p.parse_args()


def main():
    args = parse_args()
    symbols = SYMBOLS
    if args.symbols.strip():
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    if args.mode == "yield":
        yield_mode(symbols, args.years, args.threshold)
    else:
        event_mode(symbols, args.years, args.threshold, force_recalc_all=args.force_all)


if __name__ == "__main__":
    main()
