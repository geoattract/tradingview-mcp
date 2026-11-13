#!/usr/bin/env python3
"""
optimize_mgc1_5m_supertrend.py
=============================================================================
Grid Search Optimization Engine for Supertrend on COMEX Micro Gold Futures (MGC1!)
Timeframe: 5-Minute (5m)
Period: 02 Nov 2026 Asian Open to 12 Nov 2026 Live Bar
=============================================================================
"""

import json
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

def run_supertrend_sim(
    bars: List[List[float]],
    atr_period: int,
    multiplier: float,
    atr_method: str = "RMA (Wilder)",
    point_value: float = 10.0,
    friction_usd: float = 3.40  # $1.40 comms + $2.00 slippage (1 tick in, 1 tick out)
) -> Dict[str, Any]:
    n = len(bars)
    if n < atr_period + 5:
        return None

    # Calculate True Range
    tr = [0.0] * n
    tr[0] = bars[0][2] - bars[0][3]
    for i in range(1, n):
        h = bars[i][2]
        l = bars[i][3]
        pc = bars[i-1][4]
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))

    # Calculate ATR
    atr = [0.0] * n
    if atr_method == "SMA":
        for i in range(n):
            if i < atr_period - 1:
                atr[i] = 0.0
            else:
                atr[i] = sum(tr[i - atr_period + 1 : i + 1]) / atr_period
    else:  # RMA (Wilder's)
        initial_sma = sum(tr[:atr_period]) / atr_period
        atr[atr_period - 1] = initial_sma
        for i in range(atr_period, n):
            atr[i] = (atr[i - 1] * (atr_period - 1) + tr[i]) / atr_period

    # Supertrend State Machine
    up = [0.0] * n
    dn = [0.0] * n
    trend = [1] * n

    # Initialize from atr_period - 1
    start_idx = atr_period - 1
    for i in range(start_idx, n):
        hl2 = (bars[i][2] + bars[i][3]) / 2.0
        basic_up = hl2 - (multiplier * atr[i])
        basic_dn = hl2 + (multiplier * atr[i])

        if i == start_idx:
            up[i] = basic_up
            dn[i] = basic_dn
            trend[i] = 1
            continue

        prev_up = up[i - 1]
        prev_dn = dn[i - 1]
        prev_close = bars[i - 1][4]

        # Ratchet logic
        up[i] = max(basic_up, prev_up) if prev_close > prev_up else basic_up
        dn[i] = min(basic_dn, prev_dn) if prev_close < prev_dn else basic_dn

        # Trend transition
        curr_close = bars[i][4]
        prev_trend = trend[i - 1]

        if prev_trend == -1 and curr_close > prev_dn:
            trend[i] = 1
        elif prev_trend == 1 and curr_close < prev_up:
            trend[i] = -1
        else:
            trend[i] = prev_trend

    # Trade simulation (Next-Bar Open Execution)
    trades = []
    current_trade = None

    for i in range(start_idx + 1, n - 1):
        prev_trend = trend[i - 1]
        curr_trend = trend[i]

        is_bull_flip = (curr_trend == 1 and prev_trend == -1)
        is_bear_flip = (curr_trend == -1 and prev_trend == 1)

        if is_bull_flip or is_bear_flip:
            exec_bar = i + 1
            exec_price = bars[exec_bar][1]  # open of bar i+1
            exec_time = bars[exec_bar][0]

            # Close existing trade
            if current_trade is not None:
                current_trade['exit_bar'] = exec_bar
                current_trade['exit_time'] = exec_time
                current_trade['exit_price'] = exec_price

                if current_trade['direction'] == 'LONG':
                    pnl_pts = exec_price - current_trade['entry_price']
                else:
                    pnl_pts = current_trade['entry_price'] - exec_price

                current_trade['pnl_points'] = round(pnl_pts, 2)
                current_trade['pnl_gross_usd'] = round(pnl_pts * point_value, 2)
                current_trade['pnl_net_usd'] = round(pnl_pts * point_value - friction_usd, 2)
                trades.append(current_trade)

            # Open new trade
            new_dir = 'LONG' if is_bull_flip else 'SHORT'
            current_trade = {
                'direction': new_dir,
                'entry_bar': exec_bar,
                'entry_time': exec_time,
                'entry_price': exec_price,
            }

    # Mark to market last trade
    if current_trade is not None:
        last_bar = n - 1
        last_close = bars[last_bar][4]
        current_trade['exit_bar'] = last_bar
        current_trade['exit_time'] = bars[last_bar][0]
        current_trade['exit_price'] = last_close
        if current_trade['direction'] == 'LONG':
            pnl_pts = last_close - current_trade['entry_price']
        else:
            pnl_pts = current_trade['entry_price'] - last_close
        current_trade['pnl_points'] = round(pnl_pts, 2)
        current_trade['pnl_gross_usd'] = round(pnl_pts * point_value, 2)
        current_trade['pnl_net_usd'] = round(pnl_pts * point_value - friction_usd, 2)
        trades.append(current_trade)

    if not trades:
        return None

    # Compute metrics
    wins = [t for t in trades if t['pnl_net_usd'] > 0]
    losses = [t for t in trades if t['pnl_net_usd'] <= 0]
    gross_profits = sum(t['pnl_gross_usd'] for t in trades if t['pnl_gross_usd'] > 0)
    gross_losses = abs(sum(t['pnl_gross_usd'] for t in trades if t['pnl_gross_usd'] < 0))
    net_profit_gross = sum(t['pnl_gross_usd'] for t in trades)
    net_profit_net = sum(t['pnl_net_usd'] for t in trades)
    total_trades = len(trades)
    win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0
    pf_gross = (gross_profits / gross_losses) if gross_losses > 0 else (999.0 if gross_profits > 0 else 0.0)

    # Net PF
    net_profits_sum = sum(t['pnl_net_usd'] for t in wins)
    net_losses_sum = abs(sum(t['pnl_net_usd'] for t in losses))
    pf_net = (net_profits_sum / net_losses_sum) if net_losses_sum > 0 else (999.0 if net_profits_sum > 0 else 0.0)

    # Max Drawdown
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        equity += t['pnl_net_usd']
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd

    avg_win = (net_profits_sum / len(wins)) if wins else 0.0
    avg_loss = (net_losses_sum / len(losses)) if losses else 0.0
    payoff = (avg_win / avg_loss) if avg_loss > 0 else 0.0
    avg_trade_net = net_profit_net / total_trades

    return {
        'atr_period': atr_period,
        'multiplier': multiplier,
        'atr_method': atr_method,
        'total_trades': total_trades,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': round(win_rate, 2),
        'gross_profit_usd': round(gross_profits, 2),
        'gross_loss_usd': round(gross_losses, 2),
        'net_profit_gross_usd': round(net_profit_gross, 2),
        'net_profit_gross_pts': round(net_profit_gross / point_value, 2),
        'net_profit_usd': round(net_profit_net, 2),
        'net_profit_pts': round(net_profit_net / point_value, 2),
        'profit_factor': round(pf_net, 3),
        'profit_factor_gross': round(pf_gross, 3),
        'max_drawdown_usd': round(max_dd, 2),
        'max_drawdown_pts': round(max_dd / point_value, 2),
        'avg_trade_usd': round(avg_trade_net, 2),
        'avg_win_usd': round(avg_win, 2),
        'avg_loss_usd': round(avg_loss, 2),
        'payoff_ratio': round(payoff, 2),
    }

def main():
    with open('data_mgc1_5m.json') as f:
        bars = json.load(f)

    print(f"Loaded {len(bars)} 5m bars for MGC1!.")
    print(f"Start: {datetime.fromtimestamp(bars[0][0], tz=timezone.utc)}")
    print(f"End:   {datetime.fromtimestamp(bars[-1][0], tz=timezone.utc)}")

    # Parameter grid
    periods = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20]
    multipliers = [1.5, 1.8, 2.0, 2.2, 2.4, 2.5, 2.6, 2.8, 3.0, 3.2, 3.5, 4.0]
    methods = ["RMA (Wilder)", "SMA"]

    results = []
    for m in methods:
        for p in periods:
            for mult in multipliers:
                res = run_supertrend_sim(bars, p, mult, m)
                if res:
                    results.append(res)

    print(f"Executed {len(results)} backtest simulations.")

    # Sort by Net Profit (Realistic Net)
    results_by_profit = sorted(results, key=lambda x: x['net_profit_usd'], reverse=True)
    # Sort by Profit Factor (minimum 20 trades)
    results_by_pf = sorted([r for r in results if r['total_trades'] >= 20], key=lambda x: x['profit_factor'], reverse=True)

    # Save all results to JSON
    with open('mgc1_5m_optimization_results.json', 'w') as out:
        json.dump({
            'symbol': 'MGC1!',
            'timeframe': '5m',
            'bars_count': len(bars),
            'start_utc': str(datetime.fromtimestamp(bars[0][0], tz=timezone.utc)),
            'end_utc': str(datetime.fromtimestamp(bars[-1][0], tz=timezone.utc)),
            'total_tested': len(results),
            'top_10_by_net_profit': results_by_profit[:10],
            'top_10_by_profit_factor': results_by_pf[:10],
            'baseline_10_3_rma': next(r for r in results if r['atr_period'] == 10 and r['multiplier'] == 3.0 and r['atr_method'] == 'RMA (Wilder)'),
            'baseline_10_3_sma': next(r for r in results if r['atr_period'] == 10 and r['multiplier'] == 3.0 and r['atr_method'] == 'SMA')
        }, out, indent=2)

    print("\nSaved full optimization results to mgc1_5m_optimization_results.json")

if __name__ == '__main__':
    main()
