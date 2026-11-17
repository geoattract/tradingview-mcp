import json

with open('/Users/melvin/.gemini/antigravity/brain/71dab95d-dfed-40d5-b5f4-dcdc835396d8/.system_generated/steps/110/output.txt') as f:
    raw = json.load(f)

bars = raw['result']['bars']
bars_by_idx = {b['index']: b for b in bars}

trades = [
    {
        "trade_no": 1,
        "type": "BUY (Long)",
        "entry_idx": 124,
        "entry_time": "09:35 SGT",
        "entry_close": bars_by_idx[124]['close'],
        "exit_idx": 128,
        "exit_time": "09:55 SGT",
        "exit_close": bars_by_idx[128]['close'],
        "exit_reason": "First curl DOWN arrow (▼)",
        "alt_exit_idx": 129,
        "alt_exit_time": "10:00 SGT",
        "alt_exit_close": bars_by_idx[129]['close'],
    },
    {
        "trade_no": 2,
        "type": "SELL (Short)",
        "entry_idx": 156,
        "entry_time": "12:15 SGT",
        "entry_close": bars_by_idx[156]['close'],
        "exit_idx": 162,
        "exit_time": "12:45 SGT",
        "exit_close": bars_by_idx[162]['close'],
        "exit_reason": "First curl UP arrow (▲)",
        "alt_exit_idx": None,
    },
    {
        "trade_no": 3,
        "type": "BUY (Long)",
        "entry_idx": 164,
        "entry_time": "12:55 SGT",
        "entry_close": bars_by_idx[164]['close'],
        "exit_idx": 171,
        "exit_time": "13:30 SGT",
        "exit_close": bars_by_idx[171]['close'],
        "exit_reason": "First curl DOWN arrow (▼)",
        "alt_exit_idx": 172,
        "alt_exit_time": "13:35 SGT",
        "alt_exit_close": bars_by_idx[172]['close'],
    },
    {
        "trade_no": 4,
        "type": "SELL (Short)",
        "entry_idx": 179,
        "entry_time": "14:10 SGT",
        "entry_close": bars_by_idx[179]['close'],
        "exit_idx": 182,
        "exit_time": "14:25 SGT",
        "exit_close": bars_by_idx[182]['close'],
        "exit_reason": "First curl UP arrow (▲)",
        "alt_exit_idx": None,
    }
]

total_pts = 0.0
total_pnl = 0.0

print(f"{'#':<2} | {'Type':<12} | {'Entry Time':<10} | {'Entry Px':<8} | {'Exit Time':<10} | {'Exit Px':<8} | {'Exit Signal':<25} | {'Pts':<8} | {'P&L ($)':<9}")
print("-" * 105)

for t in trades:
    en_px = t['entry_close']
    ex_px = t['exit_close']
    if "BUY" in t['type']:
        pts = round(ex_px - en_px, 2)
    else:
        pts = round(en_px - ex_px, 2)
    pnl = round(pts * 10.0, 2)
    total_pts += pts
    total_pnl += pnl
    print(f"{t['trade_no']:<2} | {t['type']:<12} | {t['entry_time']:<10} | {en_px:<8.1f} | {t['exit_time']:<10} | {ex_px:<8.1f} | {t['exit_reason']:<25} | {pts:+7.1f}  | ${pnl:+8.2f}")

print("-" * 105)
print(f"TOTAL: {total_pts:+.1f} points | ${total_pnl:+.2f}")
