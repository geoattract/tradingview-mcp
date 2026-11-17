import json
import numpy as np
from test_rsi_vs_supertrend_mgc import load_data, calc_rma, calc_sma, calc_rsi, calc_supertrend, calc_stoch_rsi

def backtest_pullbacks(highs, lows, closes, times, signals_buy, signals_sell, st_trend, st_up, st_dn, atr14, name, exit_mode='ST_FLIP', tp_atr=None, sl_atr=None, point_value=10.0, commission=4.0):
    n = len(closes)
    trades = []
    
    # We simulate pullback trades:
    # Each time a signal fires in the direction of the trend:
    # Can enter a trade. Let's support 1 active trade at a time, or separate trades per signal.
    # In standard TradingView / quant backtests, let's test both non-overlapping trades and all-signal trades.
    # Here let's run clean non-overlapping execution (standard single-position strategy).
    
    pos = 0 # 1 = long, -1 = short
    entry_bar = 0
    entry_price = 0.0
    entry_time = 0
    tp_price = 0.0
    sl_price = 0.0
    
    for i in range(1, n):
        # Check active position exit first
        if pos == 1:
            exit_trade = False
            exit_price = closes[i]
            reason = ""
            
            # 1. Exit on SL / TP if bracket mode
            if tp_atr is not None and sl_atr is not None:
                if lows[i] <= sl_price:
                    exit_trade = True
                    exit_price = sl_price
                    reason = "SL"
                elif highs[i] >= tp_price:
                    exit_trade = True
                    exit_price = tp_price
                    reason = "TP"
                    
            # 2. Exit on SuperTrend flip
            if not exit_trade and (st_trend[i] == -1 or closes[i] < st_up[i]):
                exit_trade = True
                exit_price = closes[i]
                reason = "ST_FLIP"
                
            # 3. Exit on momentum reversal
            if not exit_trade and exit_mode == 'OSC_REVERSAL' and signals_sell[i]:
                exit_trade = True
                exit_price = closes[i]
                reason = "OSC_REV"
                
            if exit_trade:
                pnl_pts = exit_price - entry_price
                pnl_gross = pnl_pts * point_value
                pnl_net = pnl_gross - commission
                trades.append({
                    'dir': 1,
                    'entry_bar': entry_bar,
                    'exit_bar': i,
                    'bars_held': i - entry_bar,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl_pts': pnl_pts,
                    'pnl_gross': pnl_gross,
                    'pnl_net': pnl_net,
                    'reason': reason
                })
                pos = 0
                
        elif pos == -1:
            exit_trade = False
            exit_price = closes[i]
            reason = ""
            
            if tp_atr is not None and sl_atr is not None:
                if highs[i] >= sl_price:
                    exit_trade = True
                    exit_price = sl_price
                    reason = "SL"
                elif lows[i] <= tp_price:
                    exit_trade = True
                    exit_price = tp_price
                    reason = "TP"
                    
            if not exit_trade and (st_trend[i] == 1 or closes[i] > st_dn[i]):
                exit_trade = True
                exit_price = closes[i]
                reason = "ST_FLIP"
                
            if not exit_trade and exit_mode == 'OSC_REVERSAL' and signals_buy[i]:
                exit_trade = True
                exit_price = closes[i]
                reason = "OSC_REV"
                
            if exit_trade:
                pnl_pts = entry_price - exit_price
                pnl_gross = pnl_pts * point_value
                pnl_net = pnl_gross - commission
                trades.append({
                    'dir': -1,
                    'entry_bar': entry_bar,
                    'exit_bar': i,
                    'bars_held': i - entry_bar,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl_pts': pnl_pts,
                    'pnl_gross': pnl_gross,
                    'pnl_net': pnl_net,
                    'reason': reason
                })
                pos = 0
                
        # Check Entry
        if pos == 0:
            if st_trend[i] == 1 and signals_buy[i]:
                pos = 1
                entry_bar = i
                entry_price = closes[i]
                entry_time = times[i]
                if tp_atr is not None and sl_atr is not None:
                    tp_price = entry_price + tp_atr * atr14[i]
                    sl_price = entry_price - sl_atr * atr14[i]
            elif st_trend[i] == -1 and signals_sell[i]:
                pos = -1
                entry_bar = i
                entry_price = closes[i]
                entry_time = times[i]
                if tp_atr is not None and sl_atr is not None:
                    tp_price = entry_price - tp_atr * atr14[i]
                    sl_price = entry_price + sl_atr * atr14[i]

    # Close open trade at end
    if pos != 0:
        last_i = n - 1
        pnl_pts = (closes[last_i] - entry_price) if pos == 1 else (entry_price - closes[last_i])
        trades.append({
            'dir': pos,
            'entry_bar': entry_bar,
            'exit_bar': last_i,
            'bars_held': last_i - entry_bar,
            'entry_price': entry_price,
            'exit_price': closes[last_i],
            'pnl_pts': pnl_pts,
            'pnl_gross': pnl_pts * point_value,
            'pnl_net': pnl_pts * point_value - commission,
            'reason': 'END'
        })
        
    cnt = len(trades)
    if cnt == 0:
        return {'name': name, 'trades': 0, 'win_rate': 0.0, 'pf': 0.0, 'gross_pnl': 0.0, 'net_pnl': 0.0, 'max_dd': 0.0, 'avg_trade': 0.0}
        
    wins = [t for t in trades if t['pnl_gross'] > 0]
    losses = [t for t in trades if t['pnl_gross'] <= 0]
    win_cnt = len(wins)
    win_rate = win_cnt / cnt * 100.0
    
    gross_win = sum(t['pnl_gross'] for t in wins)
    gross_loss = abs(sum(t['pnl_gross'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    
    gross_pnl = sum(t['pnl_gross'] for t in trades)
    net_pnl = sum(t['pnl_net'] for t in trades)
    
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cum += t['pnl_net']
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
            
    avg_bars = np.mean([t['bars_held'] for t in trades])
    
    return {
        'name': name,
        'trades': cnt,
        'win_cnt': win_cnt,
        'loss_cnt': len(losses),
        'win_rate': win_rate,
        'profit_factor': pf,
        'gross_pnl': gross_pnl,
        'net_pnl': net_pnl,
        'commissions': cnt * commission,
        'max_dd': max_dd,
        'avg_trade': net_pnl / cnt,
        'avg_bars': avg_bars
    }

def run_pullback_audit(filepath, dataset_name):
    times, opens, highs, lows, closes, volumes = load_data(filepath)
    n = len(closes)
    print(f"\n====================================================================================================")
    print(f"PART 2: PULLBACK ENGINE AUDIT (PURPLE X YELLOW RSI vs STOCH RSI): {dataset_name} ({n} bars)")
    print(f"====================================================================================================")
    
    # 1. SuperTrend 80/2.2 macro trend
    st_trend, st_up, st_dn, atr80 = calc_supertrend(highs, lows, closes, 80, 2.2)
    
    # ATR14 for targets/stops
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr14 = calc_rma(tr, 14)
    
    # 2. RSI (Purple) and RSI-MA (Yellow)
    rsi_purple = calc_rsi(closes, 14)
    rsi_yellow = calc_sma(rsi_purple, 14)
    
    # Variant A: Pure Purple x Yellow cross
    purple_x_yellow_buy = np.zeros(n, dtype=bool)
    purple_x_yellow_sell = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if rsi_purple[i] > rsi_yellow[i] and rsi_purple[i-1] <= rsi_yellow[i-1]:
            purple_x_yellow_buy[i] = True
        if rsi_purple[i] < rsi_yellow[i] and rsi_purple[i-1] >= rsi_yellow[i-1]:
            purple_x_yellow_sell[i] = True
            
    # Variant B: Purple x Yellow cross with candle confirmation (close > open / close < open)
    purple_candle_buy = purple_x_yellow_buy & (closes > opens)
    purple_candle_sell = purple_x_yellow_sell & (closes < opens)
    
    # Variant C: Purple x Yellow cross with Pullback Arming / Dip
    # In uptrend, RSI pulled back below Yellow while below 50 (or <= 45); then crosses back above
    purple_dip_buy = np.zeros(n, dtype=bool)
    purple_pop_sell = np.zeros(n, dtype=bool)
    bull_dip_armed = False
    bear_pop_armed = False
    for i in range(1, n):
        if st_trend[i] != st_trend[i-1]:
            bull_dip_armed = False
            bear_pop_armed = False
        if st_trend[i] == 1:
            if rsi_purple[i] < rsi_yellow[i] and rsi_purple[i] <= 48.0:
                bull_dip_armed = True
            if bull_dip_armed and rsi_purple[i] > rsi_yellow[i] and rsi_purple[i-1] <= rsi_yellow[i-1] and closes[i] > opens[i]:
                purple_dip_buy[i] = True
                bull_dip_armed = False
        elif st_trend[i] == -1:
            if rsi_purple[i] > rsi_yellow[i] and rsi_purple[i] >= 52.0:
                bear_pop_armed = True
            if bear_pop_armed and rsi_purple[i] < rsi_yellow[i] and rsi_purple[i-1] >= rsi_yellow[i-1] and closes[i] < opens[i]:
                purple_pop_sell[i] = True
                bear_pop_armed = False

    # 3. Stoch RSI (3, 3, 14, 14)
    stochK, stochD, _ = calc_stoch_rsi(closes, 14, 14, 3, 3)
    
    # Stoch RSI Variant A: Pure %K x %D cross
    srsi_pure_buy = np.zeros(n, dtype=bool)
    srsi_pure_sell = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if stochK[i] > stochD[i] and stochK[i-1] <= stochD[i-1]:
            srsi_pure_buy[i] = True
        if stochK[i] < stochD[i] and stochK[i-1] >= stochD[i-1]:
            srsi_pure_sell[i] = True
            
    # Stoch RSI Variant B: Pure cross with candle confirmation
    srsi_candle_buy = srsi_pure_buy & (closes > opens)
    srsi_candle_sell = srsi_pure_sell & (closes < opens)
    
    # Stoch RSI Variant C: Armed Deep Pullback (<=30 OS / >=70 OB as in existing repo)
    srsi_deep_buy = np.zeros(n, dtype=bool)
    srsi_deep_sell = np.zeros(n, dtype=bool)
    srsi_bull_armed = False
    srsi_bear_armed = False
    for i in range(1, n):
        if st_trend[i] != st_trend[i-1]:
            srsi_bull_armed = False
            srsi_bear_armed = False
        if st_trend[i] == 1:
            if stochK[i] <= 30.0 and stochK[i] <= stochD[i]:
                srsi_bull_armed = True
            if stochK[i] >= 70.0:
                srsi_bull_armed = False
            kTurnUp = stochK[i] > stochD[i] and stochK[i] > stochK[i-1]
            if srsi_bull_armed and kTurnUp and closes[i] > opens[i]:
                srsi_deep_buy[i] = True
                srsi_bull_armed = False
        elif st_trend[i] == -1:
            if stochK[i] >= 70.0 and stochK[i] >= stochD[i]:
                srsi_bear_armed = True
            if stochK[i] <= 30.0:
                srsi_bear_armed = False
            kTurnDown = stochK[i] < stochD[i] and stochK[i] < stochK[i-1]
            if srsi_bear_armed and kTurnDown and closes[i] < opens[i]:
                srsi_deep_sell[i] = True
                srsi_bear_armed = False

    engines = [
        ("Purple x Yellow (Pure Crossover)", purple_x_yellow_buy, purple_x_yellow_sell),
        ("Purple x Yellow (+ Candle Confirm)", purple_candle_buy, purple_candle_sell),
        ("Purple x Yellow (Armed Dip/Pop + Candle)", purple_dip_buy, purple_pop_sell),
        ("Stoch RSI (%K x %D Pure)", srsi_pure_buy, srsi_pure_sell),
        ("Stoch RSI (+ Candle Confirm)", srsi_candle_buy, srsi_candle_sell),
        ("Stoch RSI (Armed OS/OB 30/70)", srsi_deep_buy, srsi_deep_sell),
    ]

    print(f"\n--- EXIT MODEL 1: Trend-Following Macro Exit (SuperTrend Flip / Price Stop) ---")
    print(f"{'Engine Name':<38} | {'Trades':<8} | {'Win Rate':<10} | {'PF':<6} | {'Gross PnL':<12} | {'Net PnL':<12} | {'Max DD':<10} | {'Avg Trade':<10}")
    print("-" * 120)
    for name, b_sig, s_sig in engines:
        res = backtest_pullbacks(highs, lows, closes, times, b_sig, s_sig, st_trend, st_up, st_dn, atr14, name, exit_mode='ST_FLIP')
        print(f"{name:<38} | {res['trades']:<8} | {res['win_rate']:<9.1f}% | {res['profit_factor']:<6.2f} | ${res['gross_pnl']:<11.2f} | ${res['net_pnl']:<11.2f} | ${res['max_dd']:<9.2f} | ${res['avg_trade']:<9.2f}")

    print(f"\n--- EXIT MODEL 2: Fixed Bracket (1.5x ATR TP / 1.0x ATR SL) ---")
    print(f"{'Engine Name':<38} | {'Trades':<8} | {'Win Rate':<10} | {'PF':<6} | {'Gross PnL':<12} | {'Net PnL':<12} | {'Max DD':<10} | {'Avg Trade':<10}")
    print("-" * 120)
    for name, b_sig, s_sig in engines:
        res = backtest_pullbacks(highs, lows, closes, times, b_sig, s_sig, st_trend, st_up, st_dn, atr14, name, exit_mode='BRACKET', tp_atr=1.5, sl_atr=1.0)
        print(f"{name:<38} | {res['trades']:<8} | {res['win_rate']:<9.1f}% | {res['profit_factor']:<6.2f} | ${res['gross_pnl']:<11.2f} | ${res['net_pnl']:<11.2f} | ${res['max_dd']:<9.2f} | ${res['avg_trade']:<9.2f}")

    print(f"\n--- EXIT MODEL 3: Momentum Oscillator Reversal Exit ---")
    print(f"{'Engine Name':<38} | {'Trades':<8} | {'Win Rate':<10} | {'PF':<6} | {'Gross PnL':<12} | {'Net PnL':<12} | {'Max DD':<10} | {'Avg Trade':<10}")
    print("-" * 120)
    for name, b_sig, s_sig in engines:
        res = backtest_pullbacks(highs, lows, closes, times, b_sig, s_sig, st_trend, st_up, st_dn, atr14, name, exit_mode='OSC_REVERSAL')
        print(f"{name:<38} | {res['trades']:<8} | {res['win_rate']:<9.1f}% | {res['profit_factor']:<6.2f} | ${res['gross_pnl']:<11.2f} | ${res['net_pnl']:<11.2f} | ${res['max_dd']:<9.2f} | ${res['avg_trade']:<9.2f}")

run_pullback_audit('tests/mgc1_5m_all.json', 'MGC1! 5-Minute (Full 11,040 Bars)')
run_pullback_audit('tests/mgc1_2m.json', 'MGC1! 2-Minute (Recent 465 Bars)')
