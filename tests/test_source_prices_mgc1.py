#!/usr/bin/env python3
"""
test_source_prices_mgc1.py
=============================================================================
Compare Supertrend Source Prices on COMEX Micro Gold Futures (MGC1! - 5m)
Sources tested: hl2, close, open, hlc3, ohlc4, hlcc4
=============================================================================
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any

def run_supertrend_source_sim(
    bars: List[List[float]],
    atr_period: int,
    multiplier: float,
    source_name: str,
    atr_method: str = "RMA (Wilder)",
    point_value: float = 10.0,
    friction_usd: float = 3.40
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

    # Calculate ATR (RMA Wilder)
    atr = [0.0] * n
    initial_sma = sum(tr[:atr_period]) / atr_period
    atr[atr_period - 1] = initial_sma
    for i in range(atr_period, n):
        atr[i] = (atr[i - 1] * (atr_period - 1) + tr[i]) / atr_period

    # Compute source series
    # Bar structure: [timestamp, open, high, low, close, volume]
    src = [0.0] * n
    for i in range(n):
        o, h, l, c = bars[i][1], bars[i][2], bars[i][3], bars[i][4]
        if source_name == "hl2":
            src[i] = (h + l) / 2.0
        elif source_name == "close":
            src[i] = c
        elif source_name == "open":
            src[i] = o
        elif source_name == "hlc3":
            src[i] = (h + l + c) / 3.0
        elif source_name == "ohlc4":
            src[i] = (o + h + l + c) / 4.0
        elif source_name == "hlcc4":
            src[i] = (h + l + c + c) / 4.0

    # Supertrend State Machine
    up = [0.0] * n
    dn = [0.0] * n
    trend = [1] * n

    start_idx = atr_period - 1
    for i in range(start_idx, n):
        basic_up = src[i] - (multiplier * atr[i])
        basic_dn = src[i] + (multiplier * atr[i])

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

        # Trend transition (evaluated against previous bar's band)
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
            exec_price = bars[exec_bar][1]
            exec_time = bars[exec_bar][0]

            if current_trade is not None:
                current_trade['exit_bar'] = exec_bar
                current_trade['exit_time'] = exec_time
                current_trade['exit_price'] = exec_price

                pnl_pts = (exec_price - current_trade['entry_price']) if current_trade['direction'] == 'LONG' else (current_trade['entry_price'] - exec_price)
                current_trade['pnl_points'] = round(pnl_pts, 2)
                current_trade['pnl_gross_usd'] = round(pnl_pts * point_value, 2)
                current_trade['pnl_net_usd'] = round(pnl_pts * point_value - friction_usd, 2)
                trades.append(current_trade)

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
        pnl_pts = (last_close - current_trade['entry_price']) if current_trade['direction'] == 'LONG' else (current_trade['entry_price'] - last_close)
        current_trade['pnl_points'] = round(pnl_pts, 2)
        current_trade['pnl_gross_usd'] = round(pnl_pts * point_value, 2)
        current_trade['pnl_net_usd'] = round(pnl_pts * point_value - friction_usd, 2)
        trades.append(current_trade)

    if not trades:
        return None

    wins = [t for t in trades if t['pnl_net_usd'] > 0]
    losses = [t for t in trades if t['pnl_net_usd'] <= 0]
    gross_profits = sum(t['pnl_gross_usd'] for t in trades if t['pnl_gross_usd'] > 0)
    gross_losses = abs(sum(t['pnl_gross_usd'] for t in trades if t['pnl_gross_usd'] < 0))
    net_profit_gross = sum(t['pnl_gross_usd'] for t in trades)
    net_profit_net = sum(t['pnl_net_usd'] for t in trades)
    total_trades = len(trades)
    win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0

    net_wins_sum = sum(t['pnl_net_usd'] for t in wins)
    net_losses_sum = abs(sum(t['pnl_net_usd'] for t in losses))
    pf_net = (net_wins_sum / net_losses_sum) if net_losses_sum > 0 else (999.0 if net_wins_sum > 0 else 0.0)
    pf_gross = (gross_profits / gross_losses) if gross_losses > 0 else (999.0 if gross_profits > 0 else 0.0)

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

    avg_trade_net = net_profit_net / total_trades

    return {
        'source': source_name,
        'atr_period': atr_period,
        'multiplier': multiplier,
        'total_trades': total_trades,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': round(win_rate, 2),
        'net_profit_gross_usd': round(net_profit_gross, 2),
        'net_profit_usd': round(net_profit_net, 2),
        'net_profit_pts': round(net_profit_net / point_value, 2),
        'profit_factor': round(pf_net, 3),
        'profit_factor_gross': round(pf_gross, 3),
        'max_drawdown_usd': round(max_dd, 2),
        'avg_trade_usd': round(avg_trade_net, 2),
    }

def main():
    with open('data_mgc1_5m.json') as f:
        bars = json.load(f)

    sources = ["hl2", "close", "hlc3", "ohlc4", "hlcc4", "open"]
    configs = [
        {"period": 12, "mult": 2.8, "name": "Optimized MGC (12, 2.8)"},
        {"period": 10, "mult": 3.0, "name": "Default Baseline (10, 3.0)"},
        {"period": 18, "mult": 2.4, "name": "High-Profit MGC (18, 2.4)"}
    ]

    print("==========================================================================================")
    print("MGC1! 5m SUPERSTORE SOURCE PRICE PERFORMANCE AUDIT (02 Nov - 12 Nov)")
    print("==========================================================================================")

    for cfg in configs:
        p, m, cfg_name = cfg['period'], cfg['mult'], cfg['name']
        print(f"\n--- Strategy Configuration: {cfg_name} (ATR={p}, Mult={m}) ---")
        cfg_results = []
        for s in sources:
            res = run_supertrend_source_sim(bars, p, m, s)
            cfg_results.append(res)
        
        # Sort by Profit Factor
        cfg_results_sorted = sorted(cfg_results, key=lambda x: x['profit_factor'], reverse=True)
        print(f"{'Source':<8} | {'PF (Net)':<8} | {'PF (Gross)':<10} | {'Net PnL ($)':<12} | {'Net PnL (pts)':<14} | {'Win Rate':<9} | {'Trades':<7} | {'Max DD ($)':<10} | {'Avg Trade':<10}")
        print("-" * 105)
        for r in cfg_results_sorted:
            print(f"{r['source']:<8} | {r['profit_factor']:<8.3f} | {r['profit_factor_gross']:<10.3f} | ${r['net_profit_usd']:<11.2f} | +{r['net_profit_pts']:<13.2f} | {r['win_rate_pct']:<8.2f}% | {r['total_trades']:<7} | ${r['max_drawdown_usd']:<9.2f} | +${r['avg_trade_usd']:<9.2f}")

if __name__ == '__main__':
    main()
