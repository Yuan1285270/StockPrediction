from pathlib import Path

# 500 檔台股清單 (節錄自原代碼)
SYMBOLS = [
    "1101.TW", "1102.TW", "1103.TW", "1104.TW", "1108.TW", "1109.TW", "1110.TW",
    "1201.TW", "1203.TW", "1210.TW", "1213.TW", "1215.TW", "1216.TW", "1217.TW",
    "2330.TW", "2317.TW", "2454.TW", "2303.TW", "2308.TW", "2382.TW", "2881.TW"
    # ... (請將原本 stock_selector.py 中的完整 SYMBOLS 清單貼於此)
]

YEARS_FOR_PAYOUT = 5       # 平均配息率使用年數 
YIELD_THRESHOLD = 0.06     # 篩選門檻 6% 
STATE_FILE = Path("state.json") # 紀錄歷史狀態的檔案