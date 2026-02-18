import json
import argparse
import pandas as pd
from datetime import datetime, timezone
import config
import data_fetcher
import analyzer
import yfinance as yf

def load_state():
    if config.STATE_FILE.exists():
        return json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
    return {}

def save_state(state):
    config.STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def run_event_mode(symbols, force_all):
    state = load_state()
    triggered = []
    
    print("正在檢查更新...")
    for sym in symbols:
        tk = yf.Ticker(sym)
        eps_now = data_fetcher.get_trailing_eps(tk)
        
        # 簡單判定：若強迫重算或無歷史紀錄則觸發 
        if force_all or sym not in state:
            triggered.append(sym)
            state[sym] = {
                "trailing_eps_ttm": eps_now,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
    
    save_state(state)
    
    results = []
    for sym in triggered:
        try:
            row, _ = analyzer.calculate_yield(sym, config.YEARS_FOR_PAYOUT)
            if row: results.append(row)
        except Exception as e:
            print(f"計算錯誤 {sym}: {e}")
    
    df = pd.DataFrame(results)
    if not df.empty:
        print("\n=== 分析結果 ===")
        print(df.sort_values("est_yield_%", ascending=False))
    else:
        print("\n無觸發更新或無符合條件資料")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["yield", "event"], default="event")
    parser.add_argument("--force-all", action="store_true")
    args = parser.parse_args()
    
    run_event_mode(config.SYMBOLS, args.force_all)