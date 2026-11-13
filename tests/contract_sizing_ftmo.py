#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from check_ftmo_risk import bar_list, st_trend, start_idx

def test_contracts(num_contracts):
    pt_val = 10.0 * num_contracts
    friction = 3.40 * num_contracts
    
    pos = 0
    entry_price = 0.0
    realized_pnl = 0.0
    current_day = None
    daily_stats = {}
    
    for i in range(start_idx, len(bar_list)):
        t_sec = bar_list[i][0]
        dt = datetime.fromtimestamp(t_sec, timezone(timedelta(hours=1))) # CET
        day_key = dt.strftime('%Y-%m-%d (%a)')

        if day_key != current_day:
            if current_day is not None:
                daily_stats[current_day] = {
                    'start_equity': day_start_equity,
                    'min_equity': day_min_equity,
                    'max_loss': day_start_equity - day_min_equity,
                    'end_equity': current_bar_equity,
                    'net_day': current_bar_equity - day_start_equity
                }
            current_day = day_key
            if pos == 1:
                floating = (bar_list[i][1] - entry_price) * pt_val
            elif pos == -1:
                floating = (entry_price - bar_list[i][1]) * pt_val
            else:
                floating = 0.0
            day_start_equity = realized_pnl + floating
            day_min_equity = day_start_equity

        prev_trend = st_trend[i-1]
        prev_prev_trend = st_trend[i-2] if i >= 2 else prev_trend
        if prev_trend != prev_prev_trend:
            open_p = bar_list[i][1]
            if pos != 0:
                pts = (open_p - entry_price) if pos == 1 else (entry_price - open_p)
                realized_pnl += pts * pt_val - friction
            pos = 1 if prev_trend == 1 else -1
            entry_price = open_p

        if pos == 1:
            worst = (bar_list[i][3] - entry_price) * pt_val
            current_bar_equity = realized_pnl + (bar_list[i][4] - entry_price) * pt_val
        elif pos == -1:
            worst = (entry_price - bar_list[i][2]) * pt_val
            current_bar_equity = realized_pnl + (entry_price - bar_list[i][4]) * pt_val
        else:
            worst = 0.0
            current_bar_equity = realized_pnl

        bar_min_equity = realized_pnl + worst
        day_min_equity = min(day_min_equity, bar_min_equity)

    if current_day:
        daily_stats[current_day] = {
            'start_equity': day_start_equity,
            'min_equity': day_min_equity,
            'max_loss': day_start_equity - day_min_equity,
            'end_equity': current_bar_equity,
            'net_day': current_bar_equity - day_start_equity
        }
    
    worst_day_dd = max(s['max_loss'] for s in daily_stats.values())
    tot_pnl = current_bar_equity
    return daily_stats, worst_day_dd, tot_pnl

print("=== CONTRACT SIZING VS FTMO $1,000 DAILY LOSS RULE ===")
for c in [1, 2]:
    stats, worst_dd, tot = test_contracts(c)
    print(f"\nContracts: {c} (${c*10}/pt)")
    print(f"Total Net P&L: ${tot:.2f}")
    print(f"Worst Intraday Drawdown on any single day: ${worst_dd:.2f}")
    for d, s in stats.items():
        print(f"  {d}: DD = -${s['max_loss']:6.2f} | Net = ${s['net_day']:+7.2f} | {'FAIL' if s['max_loss'] >= 1000 else 'PASS'}")
