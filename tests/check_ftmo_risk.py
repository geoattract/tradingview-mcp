#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta

with open('tests/merged_mgc1_5m.json') as f:
    bars = json.load(f)

bar_list = [[b['time'], b['open'], b['high'], b['low'], b['close'], b['volume']] for b in bars]
n = len(bar_list)

# 1. Supertrend (12, 2.8, RMA)
tr = [0.0] * n
tr[0] = bar_list[0][2] - bar_list[0][3]
for i in range(1, n):
    h = bar_list[i][2]
    l = bar_list[i][3]
    pc = bar_list[i-1][4]
    tr[i] = max(h - l, abs(h - pc), abs(l - pc))

atr = [0.0] * n
atr_period = 12
mult = 2.8
atr[atr_period - 1] = sum(tr[:atr_period]) / atr_period
for i in range(atr_period, n):
    atr[i] = (atr[i - 1] * (atr_period - 1) + tr[i]) / atr_period

up = [0.0] * n
dn = [0.0] * n
st_trend = [1] * n

for i in range(atr_period - 1, n):
    hl2 = (bar_list[i][2] + bar_list[i][3]) / 2.0
    basic_up = hl2 - (mult * atr[i])
    basic_dn = hl2 + (mult * atr[i])

    if i == atr_period - 1:
        up[i] = basic_up
        dn[i] = basic_dn
        st_trend[i] = 1
        continue

    prev_up = up[i - 1]
    prev_dn = dn[i - 1]
    prev_close = bar_list[i - 1][4]

    up[i] = max(basic_up, prev_up) if prev_close > prev_up else basic_up
    dn[i] = min(basic_dn, prev_dn) if prev_close < prev_dn else basic_dn

    curr_close = bar_list[i][4]
    prev_trend = st_trend[i - 1]

    if prev_trend == -1 and curr_close > prev_dn:
        st_trend[i] = 1
    elif prev_trend == 1 and curr_close < prev_up:
        st_trend[i] = -1
    else:
        st_trend[i] = prev_trend

nov9_ts = 1794178800 # Nov 08 23:00 UTC = Nov 09 07:00 SGT

# Find index of nov9_ts
start_idx = 0
for idx, b in enumerate(bar_list):
    if b[0] >= nov9_ts:
        start_idx = idx
        break

CONTRACTS = 2
PT_VALUE = 10.0 * CONTRACTS # $20.00 / pt
FRICTION_PER_TRADE = 3.40 * CONTRACTS # $6.80 RT ($1.40 comm + $2 slippage per contract)

# Let's run a bar-by-bar simulation tracking:
# Position: 1 (Long), -1 (Short), 0 (Flat)
# Entry price
# Cumulative Realized PnL
# Equity curve bar by bar (including worst floating intra-bar low/high)

# We will test two reset timezones for FTMO daily loss:
# 1) FTMO Standard CE(S)T midnight (UTC+1 in Nov) -> tz_offset = +1 hour
# 2) CME session reset at 17:00 EST / 22:00 UTC (New York / Chicago futures day)

def analyze_ftmo(tz_offset_hours=1, name='CE(S)T (FTMO Server Midnight)'):
    print('=' * 85)
    print(f'FTMO DAILY LOSS AUDIT: {name} | 2 CONTRACTS MGC1! ($20/pt)')
    print('=' * 85)

    pos = 0 # 1 or -1
    entry_price = 0.0
    realized_pnl = 0.0
    
    # We will track equity at each bar
    # Day tracking
    current_day = None
    day_start_equity = 0.0
    day_min_equity = 0.0
    day_max_equity = 0.0
    
    daily_stats = {}
    
    # Also individual trade tracking
    trades = []
    current_trade = None

    for i in range(start_idx, n):
        t_sec = bar_list[i][0]
        dt = datetime.fromtimestamp(t_sec, timezone(timedelta(hours=tz_offset_hours)))
        day_key = dt.strftime('%Y-%m-%d (%a)')

        # Check day reset
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
            # Start equity of the new day is the closing equity of previous bar
            # (or realized + floating at bar open)
            prev_close_price = bar_list[i-1][4] if i > 0 else bar_list[i][1]
            if pos == 1:
                floating = (bar_list[i][1] - entry_price) * PT_VALUE
            elif pos == -1:
                floating = (entry_price - bar_list[i][1]) * PT_VALUE
            else:
                floating = 0.0
            day_start_equity = realized_pnl + floating
            day_min_equity = day_start_equity
            day_max_equity = day_start_equity

        # Execute signal from previous bar if trend changed
        prev_trend = st_trend[i-1]
        prev_prev_trend = st_trend[i-2] if i >= 2 else prev_trend
        
        # If trend flipped on bar i-1, we enter on bar i open!
        if prev_trend != prev_prev_trend:
            open_price = bar_list[i][1]
            # Close existing position if any
            if pos != 0:
                pts = (open_price - entry_price) if pos == 1 else (entry_price - open_price)
                trade_net = pts * PT_VALUE - FRICTION_PER_TRADE
                realized_pnl += trade_net
                if current_trade:
                    current_trade['exit_time'] = dt
                    current_trade['exit_price'] = open_price
                    current_trade['pts'] = pts
                    current_trade['net'] = trade_net
                    trades.append(current_trade)
                    current_trade = None

            # Open new position
            pos = 1 if prev_trend == 1 else -1
            entry_price = open_price
            current_trade = {
                'entry_time': dt,
                'type': 'BUY' if pos == 1 else 'SELL',
                'entry_price': entry_price,
                'min_pts': 0.0,
                'max_pts': 0.0
            }

        # Evaluate bar i floating PnL
        # Worst case intra-bar floating PnL:
        # If Long: worst price is Low, best is High
        # If Short: worst price is High, best is Low
        if pos == 1:
            worst_floating = (bar_list[i][3] - entry_price) * PT_VALUE # Low
            best_floating = (bar_list[i][2] - entry_price) * PT_VALUE  # High
            current_bar_equity = realized_pnl + (bar_list[i][4] - entry_price) * PT_VALUE
            if current_trade:
                current_trade['min_pts'] = min(current_trade['min_pts'], bar_list[i][3] - entry_price)
                current_trade['max_pts'] = max(current_trade['max_pts'], bar_list[i][2] - entry_price)
        elif pos == -1:
            worst_floating = (entry_price - bar_list[i][2]) * PT_VALUE # High
            best_floating = (entry_price - bar_list[i][3]) * PT_VALUE  # Low
            current_bar_equity = realized_pnl + (entry_price - bar_list[i][4]) * PT_VALUE
            if current_trade:
                current_trade['min_pts'] = min(current_trade['min_pts'], entry_price - bar_list[i][2])
                current_trade['max_pts'] = max(current_trade['max_pts'], entry_price - bar_list[i][3])
        else:
            worst_floating = 0.0
            best_floating = 0.0
            current_bar_equity = realized_pnl

        bar_min_equity = realized_pnl + worst_floating
        day_min_equity = min(day_min_equity, bar_min_equity)
        day_max_equity = max(day_max_equity, realized_pnl + best_floating)

    # Save last day
    if current_day:
        daily_stats[current_day] = {
            'start_equity': day_start_equity,
            'min_equity': day_min_equity,
            'max_loss': day_start_equity - day_min_equity,
            'end_equity': current_bar_equity,
            'net_day': current_bar_equity - day_start_equity
        }

    print(f"{'Date':<18} | {'Start Eq':<10} | {'End Eq':<10} | {'Net Day':<10} | {'Max Intraday DD':<16} | {'$1,000 Breach?'}")
    print('-' * 85)
    breached = False
    for day, stat in daily_stats.items():
        dd = stat['max_loss']
        status = 'BREACHED!!' if dd >= 1000.0 else f'SAFE (buffer: ${1000.0 - dd:.2f})'
        if dd >= 1000.0:
            breached = True
        print(f"{day:<18} | ${stat['start_equity']:>9.2f} | ${stat['end_equity']:>9.2f} | ${stat['net_day']:>9.2f} | -${dd:>14.2f} | {status}")

    print('-' * 85)
    print(f'Overall Realized + Floating P&L: ${current_bar_equity:.2f}')
    print(f'Did account hit FTMO $1,000 Daily Loss Limit? {"YES - FAILED" if breached else "NO - FULLY COMPLIANT"}')
    print()
    return trades

t_cet = analyze_ftmo(tz_offset_hours=1, name='CE(S)T Midnight (FTMO Default Platform Server Time)')
t_cme = analyze_ftmo(tz_offset_hours=-5, name='US Eastern 17:00 (CME Trading Day Close)')
