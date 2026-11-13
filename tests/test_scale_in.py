#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from check_ftmo_risk import bar_list, st_trend, start_idx

# Test Scale-in strategy:
# Base position: 1 contract
# Scale-in: Add 1 contract ONLY if floating profit reaches +12 points (and move stop of 1st contract to BE)
# If trend flips, close all.

def test_scale_in():
    pos = 0 # 0, 1, 2 (long) or -1, -2 (short)
    entry_1 = 0.0
    entry_2 = 0.0
    realized_pnl = 0.0
    current_day = None
    daily_stats = {}

    for i in range(start_idx, len(bar_list)):
        t_sec = bar_list[i][0]
        dt = datetime.fromtimestamp(t_sec, timezone(timedelta(hours=1)))
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
            # calculate floating at bar open
            floating = 0.0
            if pos == 1:
                floating += (bar_list[i][1] - entry_1) * 10.0
            elif pos == 2:
                floating += (bar_list[i][1] - entry_1) * 10.0 + (bar_list[i][1] - entry_2) * 10.0
            elif pos == -1:
                floating += (entry_1 - bar_list[i][1]) * 10.0
            elif pos == -2:
                floating += (entry_1 - bar_list[i][1]) * 10.0 + (entry_2 - bar_list[i][1]) * 10.0
            day_start_equity = realized_pnl + floating
            day_min_equity = day_start_equity

        prev_trend = st_trend[i-1]
        prev_prev_trend = st_trend[i-2] if i >= 2 else prev_trend
        
        # Check signal flip
        if prev_trend != prev_prev_trend:
            open_p = bar_list[i][1]
            # close existing
            if pos != 0:
                if abs(pos) == 1:
                    pts = (open_p - entry_1) if pos == 1 else (entry_1 - open_p)
                    realized_pnl += pts * 10.0 - 3.40
                elif abs(pos) == 2:
                    pts1 = (open_p - entry_1) if pos == 2 else (entry_1 - open_p)
                    pts2 = (open_p - entry_2) if pos == 2 else (entry_2 - open_p)
                    realized_pnl += (pts1 + pts2) * 10.0 - 6.80
            pos = 1 if prev_trend == 1 else -1
            entry_1 = open_p
            entry_2 = 0.0

        # Check scale in condition during the bar
        if pos == 1:
            if bar_list[i][2] >= entry_1 + 12.0: # high touched +12 pts
                pos = 2
                entry_2 = entry_1 + 12.0
        elif pos == -1:
            if bar_list[i][3] <= entry_1 - 12.0: # low touched -12 pts
                pos = -2
                entry_2 = entry_1 - 12.0

        # Bar floating & worst equity
        worst_floating = 0.0
        cur_floating = 0.0
        if pos == 1:
            worst_floating = (bar_list[i][3] - entry_1) * 10.0
            cur_floating = (bar_list[i][4] - entry_1) * 10.0
        elif pos == 2:
            worst_floating = (bar_list[i][3] - entry_1) * 10.0 + (bar_list[i][3] - entry_2) * 10.0
            cur_floating = (bar_list[i][4] - entry_1) * 10.0 + (bar_list[i][4] - entry_2) * 10.0
        elif pos == -1:
            worst_floating = (entry_1 - bar_list[i][2]) * 10.0
            cur_floating = (entry_1 - bar_list[i][4]) * 10.0
        elif pos == -2:
            worst_floating = (entry_1 - bar_list[i][2]) * 10.0 + (entry_2 - bar_list[i][2]) * 10.0
            cur_floating = (entry_1 - bar_list[i][4]) * 10.0 + (entry_2 - bar_list[i][4]) * 10.0

        current_bar_equity = realized_pnl + cur_floating
        bar_min_equity = realized_pnl + worst_floating
        day_min_equity = min(day_min_equity, bar_min_equity)

    if current_day:
        daily_stats[current_day] = {
            'start_equity': day_start_equity,
            'min_equity': day_min_equity,
            'max_loss': day_start_equity - day_min_equity,
            'end_equity': current_bar_equity,
            'net_day': current_bar_equity - day_start_equity
        }

    return daily_stats, current_bar_equity

stats, tot = test_scale_in()
print("=== SCALE-IN STRATEGY (1 Contract Base -> Add 2nd at +12 pts) ===")
print(f"Total Net P&L: ${tot:.2f}")
for d, s in stats.items():
    print(f"  {d}: Max Intraday DD = -${s['max_loss']:6.2f} | Net = ${s['net_day']:+7.2f} | {'FAIL' if s['max_loss'] >= 1000 else 'PASS'}")
