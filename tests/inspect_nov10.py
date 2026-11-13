#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from check_ftmo_risk import bar_list, st_trend, start_idx, PT_VALUE, FRICTION_PER_TRADE

pos = 0
entry_price = 0.0
realized_pnl = 0.0
day_start_equity = None
current_day = None

for i in range(start_idx, len(bar_list)):
    t_sec = bar_list[i][0]
    dt = datetime.fromtimestamp(t_sec, timezone(timedelta(hours=1)))
    day_key = dt.strftime('%Y-%m-%d')

    if day_key != current_day:
        current_day = day_key
        if pos == 1:
            floating = (bar_list[i][1] - entry_price) * PT_VALUE
        elif pos == -1:
            floating = (entry_price - bar_list[i][1]) * PT_VALUE
        else:
            floating = 0.0
        day_start_equity = realized_pnl + floating
        if day_key == '2026-11-10':
            print(f'Nov 10 CET Start: dt={dt}, pos={pos}, entry={entry_price}, day_start_equity={day_start_equity}')

    prev_trend = st_trend[i-1]
    prev_prev_trend = st_trend[i-2] if i >= 2 else prev_trend
    if prev_trend != prev_prev_trend:
        open_p = bar_list[i][1]
        if pos != 0:
            pts = (open_p - entry_price) if pos == 1 else (entry_price - open_p)
            realized_pnl += pts * PT_VALUE - FRICTION_PER_TRADE
        pos = 1 if prev_trend == 1 else -1
        entry_price = open_p

    if day_key == '2026-11-10':
        if pos == 1:
            worst = (bar_list[i][3] - entry_price) * PT_VALUE
        elif pos == -1:
            worst = (entry_price - bar_list[i][2]) * PT_VALUE
        else:
            worst = 0.0
        cur_min_eq = realized_pnl + worst
        dd_from_start = day_start_equity - cur_min_eq
        if dd_from_start > 500:
            print(f'{dt.strftime("%H:%M")} CET ({dt.astimezone(timezone(timedelta(hours=8))).strftime("%H:%M")} SGT) | pos={pos} entry={entry_price} low={bar_list[i][3]} high={bar_list[i][2]} close={bar_list[i][4]} | real={realized_pnl:.1f} float={worst:.1f} | DD=${dd_from_start:.2f}')
