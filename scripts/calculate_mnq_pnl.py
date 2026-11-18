import json

trades_primary = [
    {
        "trade_no": 1,
        "type": "SELL (Short)",
        "entry_time": "11:55 SGT",
        "entry_close": 27383.00,
        "exit_time": "12:05 SGT",
        "exit_close": 27367.00,
        "exit_reason": "First curl UP arrow (▲)",
        "pts": 27383.00 - 27367.00,
    },
    {
        "trade_no": 2,
        "type": "BUY (Long)",
        "entry_time": "15:05 SGT",
        "entry_close": 27322.75,
        "exit_time": "15:50 SGT",
        "exit_close": 27341.00,
        "exit_reason": "First curl DOWN arrow (▼) after upward hook",
        "pts": 27341.00 - 27322.75,
        "alt_exit_time": "15:10 SGT",
        "alt_exit_close": 27310.50,
        "alt_pts": 27310.50 - 27322.75
    },
    {
        "trade_no": 3,
        "type": "SELL (Short)",
        "entry_time": "16:15 SGT",
        "entry_close": 27279.75,
        "exit_time": "16:55 SGT",
        "exit_close": 27252.75,
        "exit_reason": "First curl UP arrow (▲)",
        "pts": 27279.75 - 27252.75,
        "alt_exit_time": "17:30 SGT (post-17:00 bottom)",
        "alt_exit_close": 27119.50,
        "alt_pts": 27279.75 - 27119.50
    }
]

print("=== MNQ STRATEGY P&L (Strict First Arrow Exit) ===")
tot_pts = 0
tot_pnl = 0
for t in trades_primary:
    pts = t['pts']
    pnl = pts * 2.0 # $2/pt for MNQ
    tot_pts += pts
    tot_pnl += pnl
    print(f"Trade {t['trade_no']}: {t['type']} | In: {t['entry_time']} @ {t['entry_close']:.2f} | Out: {t['exit_time']} @ {t['exit_close']:.2f} | Pts: {pts:+.2f} | P&L: ${pnl:+.2f}")

print(f"TOTAL: {tot_pts:+.2f} points | ${tot_pnl:+.2f}")

print("\n=== MNQ STRATEGY P&L (With Trade 3 running past 17:00 to bottom curl at 17:30) ===")
tot_pts_ext = trades_primary[0]['pts'] + trades_primary[1]['pts'] + trades_primary[2]['alt_pts']
tot_pnl_ext = tot_pts_ext * 2.0
print(f"Trade 1: {trades_primary[0]['pts']:+.2f} pts (${trades_primary[0]['pts']*2:+.2f})")
print(f"Trade 2: {trades_primary[1]['pts']:+.2f} pts (${trades_primary[1]['pts']*2:+.2f})")
print(f"Trade 3 (exit 17:30 SGT): {trades_primary[2]['alt_pts']:+.2f} pts (${trades_primary[2]['alt_pts']*2:+.2f})")
print(f"TOTAL EXTENDED: {tot_pts_ext:+.2f} points | ${tot_pnl_ext:+.2f}")
