import json
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

import config
from data_fetcher import (
    get_trailing_eps,
    get_dividend_by_year,
    latest_dividend_snapshot,
    latest_news_ts,
)
from analyzer import estimate_yield_for_symbol


def load_state():
    if config.STATE_FILE.exists():
        try:
            return json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    config.STATE_FILE.write_text(
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
    - Output ONLY rows with est_yield_% >= (yield_threshold*100) to CSV
    """
    import pandas as pd
    import yfinance as yf
    from datetime import datetime

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

            triggered, reasons = detect_triggers(
                sym, eps_now, latest_year, latest_amt, news_ts_now, state
            )
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

    # High yield filter
    threshold_pct = float(yield_threshold) * 100.0
    if not df_trig.empty:
        df_high = df_trig[df_trig["est_yield_%"] >= threshold_pct]
    else:
        df_high = pd.DataFrame()

    print(f"\n=== High Yield among Triggered (>= {int(threshold_pct)}%) ===")
    print(df_high if not df_high.empty else "(none)")

    # ✅ Output ONLY high-yield rows
    # - If none, no file is written.
    if not df_high.empty:
        out_dir = getattr(config, "RESULT_DIR", None)
        if out_dir is None:
            # fallback if you didn't add RESULT_DIR in config.py
            from pathlib import Path
            out_dir = Path("result")
            out_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"event_high_yield_{int(threshold_pct)}pct_{ts}.csv"
        df_high.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ 只輸出 >= {int(threshold_pct)}% 到檔案：{out_path}")
    else:
        print(f"\n(沒有 >= {int(threshold_pct)}% 的觸發標的，所以不輸出檔案)")

    return df_trig, df_high