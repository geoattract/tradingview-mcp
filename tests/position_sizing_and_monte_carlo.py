#!/usr/bin/env python3
"""
position_sizing_and_monte_carlo.py
Simulates Fixed vs Dynamic Volatility Sizing, Drawdown Recovery Durations,
and runs 10,000-path Monte Carlo simulations for Funded Account Breach Analysis.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

POINT_VALUE = 2.0       # $2.00 per pt
COMMISSION_ROUNDTRIP = 1.20
SLIPPAGE_ROUNDTRIP = 1.00 # 2 fills * 0.25 pt * $2.00 = $1.00
FRICTION_PER_CONTRACT = 2.20

import risk_expectancy_modeling as rem
import run_risk_analysis as rra

def analyze_drawdown_recovery(trades, name):
    """
    Computes bar-level and day-level drawdown recovery times and underwater durations.
    """
    if not trades:
        return {}
    
    # Calculate cumulative net pnl after each trade
    net_pnls = [t['net_usd'] for t in trades]
    exit_times = [t['exit_time'] for t in trades]
    bars_held = [t['bars_held'] for t in trades]
    
    cum_pnl = np.cumsum(net_pnls)
    peak = cum_pnl[0]
    peak_idx = 0
    peak_time = exit_times[0]
    
    dd_durations_trades = []
    dd_durations_days = []
    dd_durations_bars = []
    
    cur_dd_trades = 0
    cur_dd_bars = 0
    in_dd = False
    dd_start_time = exit_times[0]
    
    for i in range(len(cum_pnl)):
        val = cum_pnl[i]
        if val >= peak:
            if in_dd:
                # Recovered!
                dd_durations_trades.append(cur_dd_trades)
                dd_durations_days.append((exit_times[i] - dd_start_time) / 86400.0)
                dd_durations_bars.append(cur_dd_bars)
                cur_dd_trades = 0
                cur_dd_bars = 0
                in_dd = False
            peak = val
            peak_idx = i
            peak_time = exit_times[i]
        else:
            if not in_dd:
                in_dd = True
                dd_start_time = peak_time
            cur_dd_trades += 1
            cur_dd_bars += bars_held[i]
            
    if in_dd:
        dd_durations_trades.append(cur_dd_trades)
        dd_durations_days.append((exit_times[-1] - dd_start_time) / 86400.0)
        dd_durations_bars.append(cur_dd_bars)
        
    avg_rec_trades = np.mean(dd_durations_trades) if dd_durations_trades else 0.0
    max_rec_trades = max(dd_durations_trades) if dd_durations_trades else 0.0
    avg_rec_days = np.mean(dd_durations_days) if dd_durations_days else 0.0
    max_rec_days = max(dd_durations_days) if dd_durations_days else 0.0
    avg_rec_bars = np.mean(dd_durations_bars) if dd_durations_bars else 0.0
    max_rec_bars = max(dd_durations_bars) if dd_durations_bars else 0.0
    
    return {
        'name': name,
        'avg_recovery_trades': avg_rec_trades,
        'max_recovery_trades': max_rec_trades,
        'avg_recovery_days': avg_rec_days,
        'max_recovery_days': max_rec_days,
        'avg_recovery_bars': avg_rec_bars,
        'max_recovery_bars': max_rec_bars
    }

def run_monte_carlo(trades, initial_capital=50000.0, max_trailing_dd=2000.0, max_daily_loss=1000.0, n_sims=10000):
    """
    Runs 10,000 bootstrap simulations of the trade sequence to determine:
    1. Probability of breaching $2,000 trailing drawdown
    2. Probability of breaching $1,500 drawdown
    3. Probability of breaching $1,000 daily loss limit
    4. Expected 95th and 99th percentile maximum drawdown
    """
    if not trades:
        return {}
        
    df_trades = pd.DataFrame(trades)
    net_pnls = df_trades['net_usd'].values
    n_trades = len(net_pnls)
    
    # Calculate daily loss distribution from original sequence
    df_trades['dt'] = pd.to_datetime(df_trades['exit_time'], unit='s', utc=True).dt.date
    daily_pnls = df_trades.groupby('dt')['net_usd'].sum().values
    
    rng = np.random.default_rng(42)
    max_drawdowns = np.zeros(n_sims)
    breached_2000 = 0
    breached_1500 = 0
    breached_1000 = 0
    
    # Run trade-level Monte Carlo for trailing drawdown
    for sim in range(n_sims):
        # Sample with replacement
        sample_pnls = rng.choice(net_pnls, size=n_trades, replace=True)
        equity = initial_capital + np.cumsum(sample_pnls)
        peak = np.maximum.accumulate(equity)
        dd = peak - equity
        sim_max_dd = np.max(dd)
        max_drawdowns[sim] = sim_max_dd
        
        if sim_max_dd >= 2000.0:
            breached_2000 += 1
        if sim_max_dd >= 1500.0:
            breached_1500 += 1
        if sim_max_dd >= 1000.0:
            breached_1000 += 1
            
    prob_breach_2000 = (breached_2000 / n_sims) * 100.0
    prob_breach_1500 = (breached_1500 / n_sims) * 100.0
    prob_breach_1000 = (breached_1000 / n_sims) * 100.0
    
    p50_dd = np.percentile(max_drawdowns, 50)
    p95_dd = np.percentile(max_drawdowns, 95)
    p99_dd = np.percentile(max_drawdowns, 99)
    
    # Daily loss breach probability from empirical daily distribution
    prob_daily_breach_1000 = np.mean(daily_pnls <= -1000.0) * 100.0 if len(daily_pnls) > 0 else 0.0
    worst_daily_loss = np.min(daily_pnls) if len(daily_pnls) > 0 else 0.0

    return {
        'prob_breach_2000_pct': prob_breach_2000,
        'prob_breach_1500_pct': prob_breach_1500,
        'prob_breach_1000_pct': prob_breach_1000,
        'median_max_dd': p50_dd,
        'p95_max_dd': p95_dd,
        'p99_max_dd': p99_dd,
        'prob_daily_breach_1000_pct': prob_daily_breach_1000,
        'worst_daily_loss': worst_daily_loss
    }

def simulate_dynamic_sizing(
    times, opens, highs, lows, closes,
    strategy_type,
    st_len=80, st_mult=1.4, st_meth="SMA",
    pb_mode="ALL", pb_zone=(30.0, 70.0),
    use_tp_dots=False,
    risk_pct=0.015, # 1.5% of account balance
    initial_capital=50000.0,
    max_contracts=5, # Cap at 5 MNQ (or 10 MNQ)
    filter_start_time=None
):
    """
    Simulates Dynamic Volatility Sizing where position size scales with account equity and ATR stop.
    Risk per trade = Account Equity * risk_pct.
    Stop distance = 1.5 * ATR (or distance to SuperTrend band).
    Contracts = floor(Risk_USD / (Stop_Distance_Pts * $2.00)), bounded [1, max_contracts].
    """
    n = len(closes)
    trend, up, dn, atr = rem.calc_supertrend(highs, lows, closes, length=st_len, mult=st_mult, method=st_meth)
    stochK, stochD, srsi = rem.calc_stoch_rsi(closes)
    g_dots, y_dots = rem.calc_early_wick_dots(highs, lows, closes, opens)
    
    lowK = pd.Series(stochK).rolling(3, min_periods=1).min().values
    lowD = pd.Series(stochD).rolling(3, min_periods=1).min().values
    highK = pd.Series(stochK).rolling(3, min_periods=1).max().values
    highD = pd.Series(stochD).rolling(3, min_periods=1).max().values
    
    kCrossOver = np.zeros(n, dtype=bool)
    kCrossUnder = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if stochK[i] > stochD[i] and stochK[i-1] <= stochD[i-1]:
            kCrossOver[i] = True
        if stochK[i] < stochD[i] and stochK[i-1] >= stochD[i-1]:
            kCrossUnder[i] = True

    pb_buy = np.zeros(n, dtype=bool)
    pb_sell = np.zeros(n, dtype=bool)
    lastPbBar = -9999
    pbTakenInWave = False
    
    for i in range(1, n):
        if trend[i] != trend[i-1]:
            pbTakenInWave = False
        inZoneBuy = (lowK[i] <= pb_zone[0] or lowD[i] <= pb_zone[0])
        inZoneSell = (highK[i] >= pb_zone[1] or highD[i] >= pb_zone[1])
        pbCooldown = (i - lastPbBar) >= 3
        
        rawBuy = (trend[i] == 1 and trend[i-1] == 1) and kCrossOver[i] and inZoneBuy and pbCooldown
        rawSell = (trend[i] == -1 and trend[i-1] == -1) and kCrossUnder[i] and inZoneSell and pbCooldown
        
        allowWave = (not pbTakenInWave) if pb_mode == 'FIRST' else True
        if rawBuy and allowWave:
            pb_buy[i] = True
            lastPbBar = i
            pbTakenInWave = True
        if rawSell and allowWave:
            pb_sell[i] = True
            lastPbBar = i
            pbTakenInWave = True

    start_idx = 85
    if filter_start_time is not None:
        valid_indices = np.where(times >= filter_start_time)[0]
        if len(valid_indices) > 0:
            start_idx = max(start_idx, valid_indices[0])

    trades = []
    pos = 0
    entry_bar = 0
    entry_time = 0
    raw_entry_price = 0.0
    entry_price = 0.0
    contracts = 1
    equity = initial_capital
    peak_equity = initial_capital
    max_dd = 0.0
    
    for i in range(start_idx, n - 1):
        flip_to_bull = (trend[i] == 1 and trend[i-1] == -1)
        flip_to_bear = (trend[i] == -1 and trend[i-1] == 1)
        tp_long = (trend[i] == 1 and y_dots[i])
        tp_short = (trend[i] == -1 and g_dots[i])
        
        next_open = opens[i+1]
        
        # Check exits
        exit_trade = False
        exit_price = 0.0
        exit_reason = ""
        
        if pos == 1:
            if flip_to_bear:
                exit_trade = True
                exit_price = next_open - rem.TICK_SIZE
                exit_reason = "ST_FLIP"
            elif use_tp_dots and tp_long:
                exit_trade = True
                exit_price = next_open - rem.TICK_SIZE
                exit_reason = "TP_DOT"
        elif pos == -1:
            if flip_to_bull:
                exit_trade = True
                exit_price = next_open + rem.TICK_SIZE
                exit_reason = "ST_FLIP"
            elif use_tp_dots and tp_short:
                exit_trade = True
                exit_price = next_open + rem.TICK_SIZE
                exit_reason = "TP_DOT"
                
        if exit_trade:
            if pos == 1:
                pnl_pts = exit_price - entry_price
            else:
                pnl_pts = entry_price - exit_price
                
            gross_usd = pnl_pts * POINT_VALUE * contracts
            friction_usd = FRICTION_PER_CONTRACT * contracts
            net_usd = gross_usd - friction_usd
            equity += net_usd
            
            if equity > peak_equity:
                peak_equity = equity
            dd = peak_equity - equity
            if dd > max_dd:
                max_dd = dd
                
            trades.append({
                'entry_bar': entry_bar,
                'exit_bar': i + 1,
                'contracts': contracts,
                'net_pts': pnl_pts,
                'net_usd': net_usd,
                'equity_after': equity,
                'friction_usd': friction_usd
            })
            pos = 0

        # Check entries
        if pos == 0:
            trigger_long = False
            trigger_short = False
            
            if strategy_type == "PURE_FLIP":
                trigger_long = flip_to_bull
                trigger_short = flip_to_bear
            elif strategy_type == "PULLBACK":
                trigger_long = (trend[i] == 1 and pb_buy[i])
                trigger_short = (trend[i] == -1 and pb_sell[i])
                
            if trigger_long or trigger_short:
                # Calculate dynamic sizing
                # Stop based on 1.5 * ATR (or distance to trailing band)
                stop_dist_pts = max(10.0, 1.5 * atr[i])
                risk_budget_usd = equity * risk_pct
                calc_contracts = int(risk_budget_usd / (stop_dist_pts * POINT_VALUE))
                contracts = max(1, min(max_contracts, calc_contracts))
                
                pos = 1 if trigger_long else -1
                entry_bar = i + 1
                entry_time = times[i+1]
                raw_entry_price = next_open
                entry_price = next_open + rem.TICK_SIZE if trigger_long else next_open - rem.TICK_SIZE

    net_profit = equity - initial_capital
    return {
        'initial_capital': initial_capital,
        'final_equity': equity,
        'net_profit_usd': net_profit,
        'max_dd_usd': max_dd,
        'max_dd_pct': (max_dd / initial_capital) * 100.0,
        'total_trades': len(trades),
        'avg_contracts': np.mean([t['contracts'] for t in trades]) if trades else 1.0,
        'max_contracts_used': max([t['contracts'] for t in trades]) if trades else 1
    }

def main():
    t5, o5, h5, l5, c5, v5 = rem.load_data('mnq_5m_data.csv')
    t2, o2, h2, l2, c2, v2 = rem.load_data('mnq_2m_data.csv')
    oct25_start_time = t2[0]

    # Run simulations and collect trade logs for recovery and monte carlo
    selected_strats = [
        ('1. 5m Pure Flip (80/1.4 SMA)', t5, o5, h5, l5, c5, 'PURE_FLIP', 80, 1.4, 'SMA', 'ALL', False, None),
        ('2. 5m Pullback All (80/1.4 SMA + ST Exit)', t5, o5, h5, l5, c5, 'PULLBACK', 80, 1.4, 'SMA', 'ALL', False, None),
        ('3. 5m Pullback + TP Dot (80/1.4 SMA)', t5, o5, h5, l5, c5, 'PULLBACK', 80, 1.4, 'SMA', 'ALL', True, None),
        ('4. 5m Overlap Pullback + TP Dot (80/1.4 SMA)', t5, o5, h5, l5, c5, 'PULLBACK', 80, 1.4, 'SMA', 'ALL', True, oct25_start_time),
        ('5. 2m Pure Flip (80/1.4 SMA)', t2, o2, h2, l2, c2, 'PURE_FLIP', 80, 1.4, 'SMA', 'ALL', False, None),
        ('6. 2m Pullback All (80/1.4 SMA + ST Exit)', t2, o2, h2, l2, c2, 'PULLBACK', 80, 1.4, 'SMA', 'ALL', False, None),
        ('7. 5m Baseline Pure Flip (10/3.0 RMA)', t5, o5, h5, l5, c5, 'PURE_FLIP', 10, 3.0, 'RMA', 'ALL', False, None)
    ]

    recovery_results = []
    monte_carlo_results = []
    dynamic_sizing_results = []

    print("=== DRAWDOWN RECOVERY & UNDERWATER DURATION ANALYSIS ===")
    for name, t, o, h, l, c, st_type, st_len, st_mult, st_meth, pb_mode, use_tp, filt in selected_strats:
        trades = rra.run_strategy_simulation(t, o, h, l, c, st_type, st_len, st_mult, st_meth, pb_mode=pb_mode, use_tp_dots=use_tp, filter_start_time=filt)
        rec = analyze_drawdown_recovery(trades, name)
        recovery_results.append(rec)
        print(f"{name:<45} | Avg Rec: {rec['avg_recovery_trades']:.1f} trades ({rec['avg_recovery_days']:.1f} days) | Max Rec: {rec['max_recovery_trades']} trades ({rec['max_recovery_days']:.1f} days)")

        mc = run_monte_carlo(trades, initial_capital=50000.0, max_trailing_dd=2000.0, max_daily_loss=1000.0, n_sims=10000)
        mc['name'] = name
        monte_carlo_results.append(mc)

    print("\n=== MONTE CARLO BREACH ANALYSIS ($50K ACCOUNT, $2,000 MAX TRAILING DD, $1,000 DAILY STOP) ===")
    for mc in monte_carlo_results:
        print(f"{mc['name']:<45} | Breach $2k DD: {mc['prob_breach_2000_pct']:>5.1f}% | Breach $1.5k DD: {mc['prob_breach_1500_pct']:>5.1f}% | Worst Day: ${mc['worst_daily_loss']:>7.2f} | 95% DD: ${mc['p95_max_dd']:>7.2f}")

    print("\n=== DYNAMIC VOLATILITY SIZING VS FIXED 1-CONTRACT ===")
    for risk in [0.005, 0.010, 0.015, 0.020]:
        res_fixed = rra.compute_comprehensive_metrics(rra.run_strategy_simulation(t5, o5, h5, l5, c5, 'PULLBACK', 80, 1.4, 'SMA', pb_mode='ALL', use_tp_dots=True), t5, 'Fixed')
        res_dyn = simulate_dynamic_sizing(t5, o5, h5, l5, c5, 'PULLBACK', 80, 1.4, 'SMA', pb_mode='ALL', use_tp_dots=True, risk_pct=risk, initial_capital=50000.0, max_contracts=5)
        print(f"Risk {risk*100:>4.1f}%: Net: ${res_dyn['net_profit_usd']:>8.2f} | Max DD: ${res_dyn['max_dd_usd']:>8.2f} ({res_dyn['max_dd_pct']:.1f}%) | Avg Contracts: {res_dyn['avg_contracts']:.2f} | Max Contracts: {res_dyn['max_contracts_used']}")

    # Save to JSON
    with open('tests/recovery_and_mc_results.json', 'w') as f:
        json.dump({'recovery': recovery_results, 'monte_carlo': monte_carlo_results}, f, indent=2)

if __name__ == '__main__':
    main()
