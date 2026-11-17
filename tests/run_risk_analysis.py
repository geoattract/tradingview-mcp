#!/usr/bin/env python3
"""
run_risk_analysis.py
Comprehensive Risk, Capital Preservation, Expectancy and Friction Analysis Engine.
Runs all candidate Supertrend V4 + RSI permutations across MNQ 5m and 2m datasets.
"""

import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone

POINT_VALUE = 2.0       # $2.00 per point for MNQ
TICK_SIZE = 0.25        # 0.25 pt
SLIPPAGE_PTS = 0.25     # 0.25 pt ($0.50) per fill
SLIPPAGE_USD = 0.50     # $0.50 per fill
COMMISSION_ROUNDTRIP = 1.20    # $1.20 round-trip commission ($0.60 per fill)
TOTAL_FRICTION_ROUNDTRIP = 2.20 # $1.20 comm + $1.00 slippage (2 fills * $0.50)

# Import base indicators
import risk_expectancy_modeling as rem

def run_strategy_simulation(
    times, opens, highs, lows, closes,
    strategy_type,
    st_len=80, st_mult=1.4, st_meth="SMA",
    pb_mode="ALL", pb_zone=(30.0, 70.0),
    use_tp_dots=False,
    bracket_sl_atr=None, bracket_tp_atr=None,
    filter_start_time=None
):
    n = len(closes)
    trend, up, dn, atr = rem.calc_supertrend(highs, lows, closes, length=st_len, mult=st_mult, method=st_meth)
    stochK, stochD, srsi = rem.calc_stoch_rsi(closes)
    g_dots, y_dots = rem.calc_early_wick_dots(highs, lows, closes, opens)
    
    # Precalculate rolling low/high for Stoch RSI
    lowK = pd.Series(stochK).rolling(3, min_periods=1).min().values
    lowD = pd.Series(stochD).rolling(3, min_periods=1).min().values
    highK = pd.Series(stochK).rolling(3, min_periods=1).max().values
    highD = pd.Series(stochD).rolling(3, min_periods=1).max().values
    
    # Stoch RSI crossovers
    kCrossOver = np.zeros(n, dtype=bool)
    kCrossUnder = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if stochK[i] > stochD[i] and stochK[i-1] <= stochD[i-1]:
            kCrossOver[i] = True
        if stochK[i] < stochD[i] and stochK[i-1] >= stochD[i-1]:
            kCrossUnder[i] = True

    # Dual sensor RSI for Purple Line dip
    hl2 = (highs + lows) / 2.0
    rsi_purple = rem.calc_rsi(hl2, 14)
    rsi_yellow = rem.calc_sma(rsi_purple, 14)

    # Signal generation
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

    # Purple line dip signals
    purple_buy = np.zeros(n, dtype=bool)
    purple_sell = np.zeros(n, dtype=bool)
    b_arm = False
    s_arm = False
    for i in range(1, n):
        if trend[i] != trend[i-1]:
            b_arm, s_arm = False, False
        if trend[i] == 1:
            if rsi_purple[i] < rsi_yellow[i] and rsi_purple[i] <= 48.0:
                b_arm = True
            if b_arm and rsi_purple[i] > rsi_yellow[i] and rsi_purple[i-1] <= rsi_yellow[i-1]:
                purple_buy[i] = True
                b_arm = False
        elif trend[i] == -1:
            if rsi_purple[i] > rsi_yellow[i] and rsi_purple[i] >= 52.0:
                s_arm = True
            if s_arm and rsi_purple[i] < rsi_yellow[i] and rsi_purple[i-1] >= rsi_yellow[i-1]:
                purple_sell[i] = True
                s_arm = False

    # -------------------------------------------------------------
    # SIMULATION LOOP
    # -------------------------------------------------------------
    start_idx = 85
    if filter_start_time is not None:
        valid_indices = np.where(times >= filter_start_time)[0]
        if len(valid_indices) > 0:
            start_idx = max(start_idx, valid_indices[0])

    trades = []
    pos = 0 # 1 = long, -1 = short, 0 = flat
    entry_bar = 0
    entry_time = 0
    raw_entry_price = 0.0
    entry_price = 0.0 # slipped
    tp_price = 0.0
    sl_price = 0.0
    
    # Helper to close position
    def close_pos(exit_bar, raw_exit_price, exit_reason, is_bracket=False):
        nonlocal pos, entry_bar, entry_time, raw_entry_price, entry_price, tp_price, sl_price
        if pos == 1:
            slipped_exit = raw_exit_price - SLIPPAGE_PTS if not is_bracket or exit_reason == "SL" else raw_exit_price
            gross_pts = raw_exit_price - raw_entry_price
            net_pts = slipped_exit - entry_price
        else: # pos == -1
            slipped_exit = raw_exit_price + SLIPPAGE_PTS if not is_bracket or exit_reason == "SL" else raw_exit_price
            gross_pts = raw_entry_price - raw_exit_price
            net_pts = entry_price - slipped_exit
            
        gross_usd = gross_pts * POINT_VALUE
        friction_usd = TOTAL_FRICTION_ROUNDTRIP
        net_usd = (net_pts * POINT_VALUE) - COMMISSION_ROUNDTRIP
        
        # Max Favorable / Adverse Excursion during trade
        trade_highs = highs[entry_bar : exit_bar + 1]
        trade_lows = lows[entry_bar : exit_bar + 1]
        if pos == 1:
            mfe_pts = max(trade_highs) - raw_entry_price
            mae_pts = raw_entry_price - min(trade_lows)
        else:
            mfe_pts = raw_entry_price - min(trade_lows)
            mae_pts = max(trade_highs) - raw_entry_price
            
        trades.append({
            'dir': pos,
            'entry_bar': entry_bar,
            'exit_bar': exit_bar,
            'entry_time': entry_time,
            'exit_time': times[exit_bar],
            'raw_entry': raw_entry_price,
            'entry_price': entry_price,
            'raw_exit': raw_exit_price,
            'exit_price': slipped_exit,
            'gross_pts': gross_pts,
            'gross_usd': gross_usd,
            'net_pts': net_pts,
            'net_usd': net_usd,
            'friction_usd': friction_usd,
            'friction_pts': friction_usd / POINT_VALUE,
            'bars_held': exit_bar - entry_bar,
            'mfe_pts': mfe_pts,
            'mae_pts': mae_pts,
            'exit_reason': exit_reason
        })
        pos = 0

    for i in range(start_idx, n - 1):
        # 1. Check bracket exits intrabar if active
        if pos != 0 and bracket_sl_atr is not None and bracket_tp_atr is not None:
            if pos == 1:
                if lows[i] <= sl_price:
                    close_pos(i, sl_price, "SL", is_bracket=True)
                elif highs[i] >= tp_price:
                    close_pos(i, tp_price, "TP", is_bracket=True)
            elif pos == -1:
                if highs[i] >= sl_price:
                    close_pos(i, sl_price, "SL", is_bracket=True)
                elif lows[i] <= tp_price:
                    close_pos(i, tp_price, "TP", is_bracket=True)

        # 2. Check bar-close confirmed signals
        flip_to_bull = (trend[i] == 1 and trend[i-1] == -1)
        flip_to_bear = (trend[i] == -1 and trend[i-1] == 1)
        
        # Take profit turning dot confirmed
        tp_long = (trend[i] == 1 and y_dots[i])
        tp_short = (trend[i] == -1 and g_dots[i])
        
        pb_b = pb_buy[i]
        pb_s = pb_sell[i]
        
        purp_b = purple_buy[i]
        purp_s = purple_sell[i]
        
        # Next-bar open for fills
        next_open = opens[i+1]
        
        # --- STRATEGY LOGIC ---
        if strategy_type == "PURE_FLIP":
            if pos == 1 and flip_to_bear:
                close_pos(i + 1, next_open, "FLIP")
                # Enter short
                pos = -1
                entry_bar = i + 1
                entry_time = times[i+1]
                raw_entry_price = next_open
                entry_price = next_open - SLIPPAGE_PTS
            elif pos == -1 and flip_to_bull:
                close_pos(i + 1, next_open, "FLIP")
                # Enter long
                pos = 1
                entry_bar = i + 1
                entry_time = times[i+1]
                raw_entry_price = next_open
                entry_price = next_open + SLIPPAGE_PTS
            elif pos == 0:
                if flip_to_bull:
                    pos = 1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open + SLIPPAGE_PTS
                elif flip_to_bear:
                    pos = -1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open - SLIPPAGE_PTS

        elif strategy_type == "FLIP_WITH_TP_DOT":
            # Enter on Flip, exit on TP dot or opposite Flip
            if pos == 1:
                if flip_to_bear:
                    close_pos(i + 1, next_open, "FLIP")
                    pos = -1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open - SLIPPAGE_PTS
                elif tp_long:
                    close_pos(i + 1, next_open, "TP_DOT")
            elif pos == -1:
                if flip_to_bull:
                    close_pos(i + 1, next_open, "FLIP")
                    pos = 1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open + SLIPPAGE_PTS
                elif tp_short:
                    close_pos(i + 1, next_open, "TP_DOT")
            elif pos == 0:
                if flip_to_bull:
                    pos = 1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open + SLIPPAGE_PTS
                elif flip_to_bear:
                    pos = -1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open - SLIPPAGE_PTS

        elif strategy_type == "PULLBACK":
            # Exit rules:
            if pos == 1:
                if flip_to_bear:
                    close_pos(i + 1, next_open, "ST_FLIP")
                elif use_tp_dots and tp_long:
                    close_pos(i + 1, next_open, "TP_DOT")
            elif pos == -1:
                if flip_to_bull:
                    close_pos(i + 1, next_open, "ST_FLIP")
                elif use_tp_dots and tp_short:
                    close_pos(i + 1, next_open, "TP_DOT")

            # Entry rules: Enter on pullback signal in trend direction
            if pos == 0:
                if trend[i] == 1 and pb_b:
                    pos = 1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open + SLIPPAGE_PTS
                    if bracket_sl_atr is not None and bracket_tp_atr is not None:
                        sl_price = raw_entry_price - bracket_sl_atr * atr[i]
                        tp_price = raw_entry_price + bracket_tp_atr * atr[i]
                elif trend[i] == -1 and pb_s:
                    pos = -1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open - SLIPPAGE_PTS
                    if bracket_sl_atr is not None and bracket_tp_atr is not None:
                        sl_price = raw_entry_price + bracket_sl_atr * atr[i]
                        tp_price = raw_entry_price - bracket_tp_atr * atr[i]

        elif strategy_type == "PURPLE_DIP":
            if pos == 1:
                if flip_to_bear:
                    close_pos(i + 1, next_open, "ST_FLIP")
                elif use_tp_dots and tp_long:
                    close_pos(i + 1, next_open, "TP_DOT")
            elif pos == -1:
                if flip_to_bull:
                    close_pos(i + 1, next_open, "ST_FLIP")
                elif use_tp_dots and tp_short:
                    close_pos(i + 1, next_open, "TP_DOT")

            if pos == 0:
                if trend[i] == 1 and purp_b:
                    pos = 1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open + SLIPPAGE_PTS
                elif trend[i] == -1 and purp_s:
                    pos = -1
                    entry_bar = i + 1
                    entry_time = times[i+1]
                    raw_entry_price = next_open
                    entry_price = next_open - SLIPPAGE_PTS

    # Close remaining open position at final bar close
    if pos != 0:
        close_pos(n - 1, closes[-1], "END_OF_DATA")

    return trades

print("Simulation engine ready.")

# -----------------------------------------------------------------------------
# METRICS & PERFORMANCE COMPUTATION ENGINE
# -----------------------------------------------------------------------------
def compute_comprehensive_metrics(trades, times, name, initial_capital=50000.0):
    if not trades:
        return {'name': name, 'total_trades': 0}

    n_trades = len(trades)
    gross_pnls_usd = np.array([t['gross_usd'] for t in trades])
    net_pnls_usd = np.array([t['net_usd'] for t in trades])
    gross_pnls_pts = np.array([t['gross_pts'] for t in trades])
    net_pnls_pts = np.array([t['net_pts'] for t in trades])
    frictions_usd = np.array([t['friction_usd'] for t in trades])
    bars_held = np.array([t['bars_held'] for t in trades])
    
    wins = [t for t in trades if t['net_usd'] > 0]
    losses = [t for t in trades if t['net_usd'] <= 0]
    
    n_wins = len(wins)
    n_losses = len(losses)
    win_rate = (n_wins / n_trades) * 100.0 if n_trades > 0 else 0.0
    
    total_gross_profit_usd = sum(t['gross_usd'] for t in trades if t['gross_usd'] > 0)
    total_gross_loss_usd = abs(sum(t['gross_usd'] for t in trades if t['gross_usd'] < 0))
    net_profit_usd = sum(net_pnls_usd)
    net_profit_pts = sum(net_pnls_pts)
    total_friction_usd = sum(frictions_usd)
    
    gross_profit_factor = (total_gross_profit_usd / total_gross_loss_usd) if total_gross_loss_usd > 0 else 999.0
    
    total_net_win_usd = sum(t['net_usd'] for t in wins)
    total_net_loss_usd = abs(sum(t['net_usd'] for t in losses))
    net_profit_factor = (total_net_win_usd / total_net_loss_usd) if total_net_loss_usd > 0 else 999.0
    
    avg_trade_usd = net_profit_usd / n_trades if n_trades > 0 else 0.0
    avg_trade_pts = net_profit_pts / n_trades if n_trades > 0 else 0.0
    
    avg_win_usd = total_net_win_usd / n_wins if n_wins > 0 else 0.0
    avg_win_pts = sum(t['net_pts'] for t in wins) / n_wins if n_wins > 0 else 0.0
    
    avg_loss_usd = total_net_loss_usd / n_losses if n_losses > 0 else 0.0
    avg_loss_pts = abs(sum(t['net_pts'] for t in losses)) / n_losses if n_losses > 0 else 0.0
    
    payoff_ratio = (avg_win_usd / avg_loss_usd) if avg_loss_usd > 0 else 0.0
    expectancy_usd = (win_rate / 100.0 * avg_win_usd) - ((100.0 - win_rate) / 100.0 * avg_loss_usd)
    expectancy_pts = expectancy_usd / POINT_VALUE
    
    # Friction erosion %
    friction_pct_gross_profit = (total_friction_usd / total_gross_profit_usd * 100.0) if total_gross_profit_usd > 0 else 0.0
    friction_drag_on_profit = (total_friction_usd / (total_gross_profit_usd - total_gross_loss_usd) * 100.0) if (total_gross_profit_usd - total_gross_loss_usd) > 0 else 999.0

    # Streaks
    max_win_streak = 0
    max_loss_streak = 0
    cur_win_streak = 0
    cur_loss_streak = 0
    for t in trades:
        if t['net_usd'] > 0:
            cur_win_streak += 1
            cur_loss_streak = 0
            if cur_win_streak > max_win_streak:
                max_win_streak = cur_win_streak
        else:
            cur_loss_streak += 1
            cur_win_streak = 0
            if cur_loss_streak > max_loss_streak:
                max_loss_streak = cur_loss_streak

    # Equity Curve & Drawdown Analysis (Closed-trade)
    cum_pnl = np.cumsum(net_pnls_usd)
    equity_curve = initial_capital + cum_pnl
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = running_max - equity_curve
    max_dd_usd = np.max(drawdowns)
    max_dd_pts = max_dd_usd / POINT_VALUE
    max_dd_pct = (max_dd_usd / initial_capital) * 100.0

    # Drawdown durations & recovery
    dd_durations_trades = []
    cur_dd_len = 0
    in_dd = False
    for dd in drawdowns:
        if dd > 0.001:
            cur_dd_len += 1
            in_dd = True
        else:
            if in_dd:
                dd_durations_trades.append(cur_dd_len)
                cur_dd_len = 0
                in_dd = False
    if in_dd:
        dd_durations_trades.append(cur_dd_len)
        
    avg_recovery_trades = np.mean(dd_durations_trades) if dd_durations_trades else 0.0
    max_dd_duration_trades = max(dd_durations_trades) if dd_durations_trades else 0.0

    # Time-based drawdown and recovery (using trade exit timestamps)
    start_time = trades[0]['entry_time']
    end_time = trades[-1]['exit_time']
    total_days = max(1.0, (end_time - start_time) / 86400.0)
    
    # Daily returns aggregation for Sharpe / Sortino
    df_trades = pd.DataFrame(trades)
    df_trades['dt'] = pd.to_datetime(df_trades['exit_time'], unit='s', utc=True).dt.date
    daily_pnl = df_trades.groupby('dt')['net_usd'].sum()
    
    # Reindex to all unique calendar days in range to include 0-trading days if wanted,
    # or evaluate on active trading days (typically 252 trading days/year)
    daily_returns_usd = daily_pnl.values
    mean_daily_pnl = np.mean(daily_returns_usd)
    std_daily_pnl = np.std(daily_returns_usd, ddof=1) if len(daily_returns_usd) > 1 else 1e-5
    
    # Annualized Sharpe (assuming 252 trading days, 0 risk-free rate)
    annualized_return_usd = mean_daily_pnl * 252.0
    annualized_vol_usd = std_daily_pnl * np.sqrt(252.0)
    sharpe_daily = (annualized_return_usd / annualized_vol_usd) if annualized_vol_usd > 0 else 0.0
    
    # Annualized Sortino (downside deviation of negative daily returns)
    downside_daily = daily_returns_usd[daily_returns_usd < 0]
    downside_std_usd = np.sqrt(np.mean(downside_daily ** 2)) * np.sqrt(252.0) if len(downside_daily) > 0 else 1e-5
    sortino_daily = (annualized_return_usd / downside_std_usd) if downside_std_usd > 0 else 0.0
    
    # Calmar / MAR Ratio (Annualized Return / Max Drawdown)
    calmar_ratio = (annualized_return_usd / max_dd_usd) if max_dd_usd > 0 else 999.0
    
    # Trade-based Sharpe and Sortino
    mean_trade_net = np.mean(net_pnls_usd)
    std_trade_net = np.std(net_pnls_usd, ddof=1) if len(net_pnls_usd) > 1 else 1e-5
    trades_per_year = (n_trades / total_days) * 252.0
    trade_sharpe = (mean_trade_net / std_trade_net) * np.sqrt(trades_per_year) if std_trade_net > 0 else 0.0
    
    downside_trades = net_pnls_usd[net_pnls_usd < 0]
    downside_trade_std = np.sqrt(np.mean(downside_trades ** 2)) if len(downside_trades) > 0 else 1e-5
    trade_sortino = (mean_trade_net / downside_trade_std) * np.sqrt(trades_per_year) if downside_trade_std > 0 else 0.0

    return {
        'name': name,
        'total_trades': n_trades,
        'wins': n_wins,
        'losses': n_losses,
        'win_rate': win_rate,
        'gross_profit_usd': total_gross_profit_usd,
        'gross_loss_usd': total_gross_loss_usd,
        'net_profit_usd': net_profit_usd,
        'net_profit_pts': net_profit_pts,
        'friction_usd': total_friction_usd,
        'friction_pct_gross_profit': friction_pct_gross_profit,
        'friction_drag_on_profit': friction_drag_on_profit,
        'gross_pf': gross_profit_factor,
        'net_pf': net_profit_factor,
        'avg_trade_usd': avg_trade_usd,
        'avg_trade_pts': avg_trade_pts,
        'avg_win_usd': avg_win_usd,
        'avg_win_pts': avg_win_pts,
        'avg_loss_usd': avg_loss_usd,
        'avg_loss_pts': avg_loss_pts,
        'payoff_ratio': payoff_ratio,
        'expectancy_usd': expectancy_usd,
        'expectancy_pts': expectancy_pts,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'max_dd_usd': max_dd_usd,
        'max_dd_pts': max_dd_pts,
        'max_dd_pct': max_dd_pct,
        'avg_recovery_trades': avg_recovery_trades,
        'max_dd_duration_trades': max_dd_duration_trades,
        'total_days': total_days,
        'annualized_return_usd': annualized_return_usd,
        'calmar_ratio': calmar_ratio,
        'sharpe_daily': sharpe_daily,
        'sortino_daily': sortino_daily,
        'trade_sharpe': trade_sharpe,
        'trade_sortino': trade_sortino,
        'trades_per_day': n_trades / total_days,
        'avg_bars_held': np.mean(bars_held) if len(bars_held) > 0 else 0.0
    }
