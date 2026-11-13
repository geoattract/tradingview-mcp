#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from check_ftmo_risk import bar_list, st_trend, start_idx

# Simulate 2 contracts with Tradovate $700 Daily Circuit Breaker
# Rule: If cumulative realized loss + floating loss from day start >= $700:
# Liquidate position immediately at market (with 2 ticks extra slippage penalty = $20 penalty)
# Lock account out from taking ANY new trades until next day 00:00 CET / 07:00 SGT.

def test_circuit_breaker(limit=700.0, extra_liquidation_slippage=20.0):
    CONTRACTS = 2
    PT_VAL = 20.0
    FRICTION = 6.80

    pos = 0
    entry_price = 0.0
    realized_pnl = 0.0
    current_day = None
    locked_out = False
    
    daily_stats = {}
    day_trades = []
    all_trades = []

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
                    'net_day': current_bar_equity - day_start_equity,
                    'locked_out': locked_out,
                    'trades_count': len(day_trades)
                }
            current_day = day_key
            locked_out = False
            day_trades = []
            
            # Start equity of the new day
            floating = 0.0
            if pos == 1:
                floating = (bar_list[i][1] - entry_price) * PT_VAL
            elif pos == -1:
                floating = (entry_price - bar_list[i][1]) * PT_VAL
            day_start_equity = realized_pnl + floating
            day_min_equity = day_start_equity

        # If locked out, we skip executing new signals
        if locked_out:
            current_bar_equity = realized_pnl
            continue

        prev_trend = st_trend[i-1]
        prev_prev_trend = st_trend[i-2] if i >= 2 else prev_trend

        # Signal flip
        if prev_trend != prev_prev_trend:
            open_p = bar_list[i][1]
            if pos != 0:
                pts = (open_p - entry_price) if pos == 1 else (entry_price - open_p)
                t_net = pts * PT_VAL - FRICTION
                realized_pnl += t_net
                day_trades.append({'type': 'EXIT', 'pts': pts, 'net': t_net, 'price': open_p, 'time': dt})
            pos = 1 if prev_trend == 1 else -1
            entry_price = open_p
            day_trades.append({'type': 'ENTRY_' + ('BUY' if pos==1 else 'SELL'), 'price': entry_price, 'time': dt})

        # Check intra-bar worst equity
        worst_float = (bar_list[i][3] - entry_price) * PT_VAL if pos == 1 else ((entry_price - bar_list[i][2]) * PT_VAL if pos == -1 else 0.0)
        close_float = (bar_list[i][4] - entry_price) * PT_VAL if pos == 1 else ((entry_price - bar_list[i][4]) * PT_VAL if pos == -1 else 0.0)

        bar_min_equity = realized_pnl + worst_float
        day_min_equity = min(day_min_equity, bar_min_equity)
        current_bar_equity = realized_pnl + close_float

        # Check if Circuit Breaker is triggered!
        current_loss = day_start_equity - bar_min_equity
        if current_loss >= limit and not locked_out and pos != 0:
            # LIQUIDATE NOW!
            locked_out = True
            # Liquidation price approximates the level that caused the loss
            # plus extra slippage
            loss_at_limit = -limit - extra_liquidation_slippage
            realized_pnl = day_start_equity + loss_at_limit
            pos = 0
            current_bar_equity = realized_pnl
            day_trades.append({'type': 'CIRCUIT_BREAKER_TRIGGERED', 'loss': loss_at_limit, 'time': dt})

    if current_day:
        daily_stats[current_day] = {
            'start_equity': day_start_equity,
            'min_equity': day_min_equity,
            'max_loss': day_start_equity - day_min_equity,
            'end_equity': current_bar_equity,
            'net_day': current_bar_equity - day_start_equity,
            'locked_out': locked_out,
            'trades_count': len(day_trades)
        }

    return daily_stats, current_bar_equity

stats, total_pnl = test_circuit_breaker(limit=700.0, extra_liquidation_slippage=20.0)

print("=" * 80)
print("TRADOVATE $700 HARD CIRCUIT BREAKER SIMULATION (2 CONTRACTS MGC1!)")
print("=" * 80)
print(f"{'Date':<18} | {'Start Eq':<10} | {'End Eq':<10} | {'Net Day':<10} | {'Circuit Breaker':<18} | {'FTMO Status'}")
print("-" * 80)
for d, s in stats.items():
    cb_txt = "TRIGGERED (Locked)" if s['locked_out'] else "Not Triggered"
    ftmo_status = "SAFE (Buffer $280)" if s['locked_out'] else "SAFE"
    print(f"{d:<18} | ${s['start_equity']:>9.2f} | ${s['end_equity']:>9.2f} | ${s['net_day']:>9.2f} | {cb_txt:<18} | {ftmo_status}")

print("-" * 80)
print(f"Total Net P&L for Week: ${total_pnl:.2f}")
print("=" * 80)
