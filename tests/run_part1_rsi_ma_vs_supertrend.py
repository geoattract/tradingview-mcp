import json
import numpy as np
from datetime import datetime, timezone
from test_rsi_vs_supertrend_mgc import load_data, calc_rma, calc_sma, calc_ema, calc_rsi, calc_supertrend

def backtest_regimes(signals, closes, highs, lows, times, name, point_value=10.0, commission=4.0):
    # signals: array of +1 (Bullish/Long) and -1 (Bearish/Short)
    n = len(signals)
    flips = []
    curr_dir = signals[0]
    curr_start = 0
    
    for i in range(1, n):
        if signals[i] != signals[i-1]:
            flips.append({
                'dir': curr_dir,
                'start_bar': curr_start,
                'end_bar': i,
                'duration_bars': i - curr_start,
                'entry_price': closes[curr_start],
                'exit_price': closes[i],
                'entry_time': times[curr_start],
                'exit_time': times[i]
            })
            curr_dir = signals[i]
            curr_start = i
            
    # Add final open regime if any
    flips.append({
        'dir': curr_dir,
        'start_bar': curr_start,
        'end_bar': n - 1,
        'duration_bars': (n - 1) - curr_start,
        'entry_price': closes[curr_start],
        'exit_price': closes[n - 1],
        'entry_time': times[curr_start],
        'exit_time': times[n - 1]
    })
    
    # Calculate trade metrics
    trades = []
    durations = [f['duration_bars'] for f in flips]
    
    for f in flips:
        pnl_pts = (f['exit_price'] - f['entry_price']) if f['dir'] == 1 else (f['entry_price'] - f['exit_price'])
        pnl_gross = pnl_pts * point_value
        pnl_net = pnl_gross - commission
        
        # Max adverse excursion during trade
        sb = f['start_bar']
        eb = f['end_bar']
        trade_highs = highs[sb : eb + 1]
        trade_lows = lows[sb : eb + 1]
        if f['dir'] == 1:
            mae_pts = min(trade_lows) - f['entry_price']
            mfe_pts = max(trade_highs) - f['entry_price']
        else:
            mae_pts = f['entry_price'] - max(trade_highs)
            mfe_pts = f['entry_price'] - min(trade_lows)
            
        trades.append({
            'dir': f['dir'],
            'pnl_pts': pnl_pts,
            'pnl_gross': pnl_gross,
            'pnl_net': pnl_net,
            'bars': f['duration_bars'],
            'mae_usd': mae_pts * point_value,
            'mfe_usd': mfe_pts * point_value
        })
        
    cnt = len(trades)
    wins = [t for t in trades if t['pnl_gross'] > 0]
    losses = [t for t in trades if t['pnl_gross'] <= 0]
    win_cnt = len(wins)
    loss_cnt = len(losses)
    win_rate = (win_cnt / cnt * 100.0) if cnt > 0 else 0.0
    
    gross_win = sum(t['pnl_gross'] for t in wins)
    gross_loss = abs(sum(t['pnl_gross'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    
    net_pnl = sum(t['pnl_net'] for t in trades)
    gross_pnl = sum(t['pnl_gross'] for t in trades)
    
    # Drawdown
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
            
    # Whipsaw counts
    whipsaw_1 = sum(1 for d in durations if d <= 1)
    whipsaw_2 = sum(1 for d in durations if d <= 2)
    whipsaw_3 = sum(1 for d in durations if d <= 3)
    whipsaw_5 = sum(1 for d in durations if d <= 5)
    whipsaw_10 = sum(1 for d in durations if d <= 10)
    
    avg_mae = np.mean([t['mae_usd'] for t in trades])
    worst_mae = min([t['mae_usd'] for t in trades])
    
    return {
        'name': name,
        'flips_count': cnt,
        'avg_duration_bars': np.mean(durations),
        'median_duration_bars': np.median(durations),
        'whipsaw_le_2': whipsaw_2,
        'whipsaw_le_3': whipsaw_3,
        'whipsaw_le_5': whipsaw_5,
        'whipsaw_le_10': whipsaw_10,
        'whipsaw_pct_le_3': (whipsaw_3 / cnt * 100.0) if cnt > 0 else 0.0,
        'whipsaw_pct_le_5': (whipsaw_5 / cnt * 100.0) if cnt > 0 else 0.0,
        'win_rate': win_rate,
        'profit_factor': pf,
        'gross_pnl': gross_pnl,
        'net_pnl': net_pnl,
        'total_commissions': cnt * commission,
        'max_dd': max_dd,
        'avg_trade_usd': net_pnl / cnt if cnt > 0 else 0.0,
        'avg_mae_usd': avg_mae,
        'worst_mae_usd': worst_mae
    }

def run_dataset_part1(filepath, dataset_name):
    times, opens, highs, lows, closes, volumes = load_data(filepath)
    n = len(closes)
    print(f"\n==========================================================================================")
    print(f"PART 1: BUY/SELL LABELS & WHIPSAW AUDIT: {dataset_name} ({n} bars)")
    print(f"==========================================================================================")
    
    # 1. SuperTrend 80 / 2.2 (hl2)
    st_trend, st_up, st_dn, atr80 = calc_supertrend(highs, lows, closes, length=80, mult=2.2)
    
    # 2. RSI Yellow Line (RSI 14 Close, SMA 14 of RSI)
    rsi_close = calc_rsi(closes, length=14)
    rsi_ma_sma = calc_sma(rsi_close, length=14)
    sig_rsi_ma_sma = np.zeros(n, dtype=int)
    curr = 1 if rsi_ma_sma[14] >= 50 else -1
    for i in range(n):
        if rsi_ma_sma[i] > 50:
            curr = 1
        elif rsi_ma_sma[i] < 50:
            curr = -1
        sig_rsi_ma_sma[i] = curr
        
    # 3. RSI Yellow Line with hl2 source (RSI 14 hl2, SMA 14 of RSI)
    hl2 = (highs + lows) / 2.0
    rsi_hl2 = calc_rsi(hl2, length=14)
    rsi_ma_hl2 = calc_sma(rsi_hl2, length=14)
    sig_rsi_ma_hl2 = np.zeros(n, dtype=int)
    curr = 1 if rsi_ma_hl2[14] >= 50 else -1
    for i in range(n):
        if rsi_ma_hl2[i] > 50:
            curr = 1
        elif rsi_ma_hl2[i] < 50:
            curr = -1
        sig_rsi_ma_hl2[i] = curr

    # 4. RSI Yellow Line with EMA (RSI 14 Close, EMA 14 of RSI)
    rsi_ma_ema = calc_ema(rsi_close, length=14)
    sig_rsi_ma_ema = np.zeros(n, dtype=int)
    curr = 1 if rsi_ma_ema[14] >= 50 else -1
    for i in range(n):
        if rsi_ma_ema[i] > 50:
            curr = 1
        elif rsi_ma_ema[i] < 50:
            curr = -1
        sig_rsi_ma_ema[i] = curr

    # 5. Raw RSI 50-cross (Purple Line crossing 50)
    sig_rsi_raw = np.zeros(n, dtype=int)
    curr = 1 if rsi_close[14] >= 50 else -1
    for i in range(n):
        if rsi_close[i] > 50:
            curr = 1
        elif rsi_close[i] < 50:
            curr = -1
        sig_rsi_raw[i] = curr

    # We evaluate warmup from bar 80 to ensure Supertrend has warm ATR80
    warmup = 80
    res_st = backtest_regimes(st_trend[warmup:], closes[warmup:], highs[warmup:], lows[warmup:], times[warmup:], "SuperTrend 80/2.2 (hl2)")
    res_rsi_sma = backtest_regimes(sig_rsi_ma_sma[warmup:], closes[warmup:], highs[warmup:], lows[warmup:], times[warmup:], "RSI-MA 50-Cross (Close, SMA 14)")
    res_rsi_hl2 = backtest_regimes(sig_rsi_ma_hl2[warmup:], closes[warmup:], highs[warmup:], lows[warmup:], times[warmup:], "RSI-MA 50-Cross (hl2, SMA 14)")
    res_rsi_ema = backtest_regimes(sig_rsi_ma_ema[warmup:], closes[warmup:], highs[warmup:], lows[warmup:], times[warmup:], "RSI-MA 50-Cross (Close, EMA 14)")
    res_rsi_raw = backtest_regimes(sig_rsi_raw[warmup:], closes[warmup:], highs[warmup:], lows[warmup:], times[warmup:], "RSI 14 Raw 50-Cross (Purple Line)")
    
    results = [res_st, res_rsi_sma, res_rsi_hl2, res_rsi_ema, res_rsi_raw]
    
    print(f"\n{'Metric / Indicator':<34} | {'SuperTrend 80/2.2':<18} | {'RSI-MA (Close SMA)':<18} | {'RSI-MA (hl2 SMA)':<18} | {'RSI-MA (Close EMA)':<18}")
    print("-" * 115)
    print(f"{'Total Regimes / Flips':<34} | {res_st['flips_count']:<18} | {res_rsi_sma['flips_count']:<18} | {res_rsi_hl2['flips_count']:<18} | {res_rsi_ema['flips_count']:<18}")
    print(f"{'Avg Duration (Bars)':<34} | {res_st['avg_duration_bars']:<18.1f} | {res_rsi_sma['avg_duration_bars']:<18.1f} | {res_rsi_hl2['avg_duration_bars']:<18.1f} | {res_rsi_ema['avg_duration_bars']:<18.1f}")
    print(f"{'Median Duration (Bars)':<34} | {res_st['median_duration_bars']:<18.1f} | {res_rsi_sma['median_duration_bars']:<18.1f} | {res_rsi_hl2['median_duration_bars']:<18.1f} | {res_rsi_ema['median_duration_bars']:<18.1f}")
    print(f"{'Whipsaws <= 2 bars':<34} | {res_st['whipsaw_le_2']:<18} | {res_rsi_sma['whipsaw_le_2']:<18} | {res_rsi_hl2['whipsaw_le_2']:<18} | {res_rsi_ema['whipsaw_le_2']:<18}")
    print(f"{'Whipsaws <= 3 bars':<34} | {res_st['whipsaw_le_3']:<18} | {res_rsi_sma['whipsaw_le_3']:<18} | {res_rsi_hl2['whipsaw_le_3']:<18} | {res_rsi_ema['whipsaw_le_3']:<18}")
    print(f"{'Whipsaws <= 5 bars':<34} | {res_st['whipsaw_le_5']:<18} | {res_rsi_sma['whipsaw_le_5']:<18} | {res_rsi_hl2['whipsaw_le_5']:<18} | {res_rsi_ema['whipsaw_le_5']:<18}")
    print(f"{'Whipsaws <= 10 bars':<34} | {res_st['whipsaw_le_10']:<18} | {res_rsi_sma['whipsaw_le_10']:<18} | {res_rsi_hl2['whipsaw_le_10']:<18} | {res_rsi_ema['whipsaw_le_10']:<18}")
    print(f"{'Whipsaw % (<= 3 bars)':<34} | {res_st['whipsaw_pct_le_3']:<17.1f}% | {res_rsi_sma['whipsaw_pct_le_3']:<17.1f}% | {res_rsi_hl2['whipsaw_pct_le_3']:<17.1f}% | {res_rsi_ema['whipsaw_pct_le_3']:<17.1f}%")
    print(f"{'Whipsaw % (<= 5 bars)':<34} | {res_st['whipsaw_pct_le_5']:<17.1f}% | {res_rsi_sma['whipsaw_pct_le_5']:<17.1f}% | {res_rsi_hl2['whipsaw_pct_le_5']:<17.1f}% | {res_rsi_ema['whipsaw_pct_le_5']:<17.1f}%")
    print(f"{'Win Rate (%)':<34} | {res_st['win_rate']:<17.1f}% | {res_rsi_sma['win_rate']:<17.1f}% | {res_rsi_hl2['win_rate']:<17.1f}% | {res_rsi_ema['win_rate']:<17.1f}%")
    print(f"{'Profit Factor':<34} | {res_st['profit_factor']:<18.2f} | {res_rsi_sma['profit_factor']:<18.2f} | {res_rsi_hl2['profit_factor']:<18.2f} | {res_rsi_ema['profit_factor']:<18.2f}")
    print(f"{'Gross PnL ($)':<34} | ${res_st['gross_pnl']:<17.2f} | ${res_rsi_sma['gross_pnl']:<17.2f} | ${res_rsi_hl2['gross_pnl']:<17.2f} | ${res_rsi_ema['gross_pnl']:<17.2f}")
    print(f"{'Total Commission ($4/tr)':<34} | ${res_st['total_commissions']:<17.2f} | ${res_rsi_sma['total_commissions']:<17.2f} | ${res_rsi_hl2['total_commissions']:<17.2f} | ${res_rsi_ema['total_commissions']:<17.2f}")
    print(f"{'Net PnL ($)':<34} | ${res_st['net_pnl']:<17.2f} | ${res_rsi_sma['net_pnl']:<17.2f} | ${res_rsi_hl2['net_pnl']:<17.2f} | ${res_rsi_ema['net_pnl']:<17.2f}")
    print(f"{'Max Drawdown ($)':<34} | ${res_st['max_dd']:<17.2f} | ${res_rsi_sma['max_dd']:<17.2f} | ${res_rsi_hl2['max_dd']:<17.2f} | ${res_rsi_ema['max_dd']:<17.2f}")
    print(f"{'Avg Trade ($ net)':<34} | ${res_st['avg_trade_usd']:<17.2f} | ${res_rsi_sma['avg_trade_usd']:<17.2f} | ${res_rsi_hl2['avg_trade_usd']:<17.2f} | ${res_rsi_ema['avg_trade_usd']:<17.2f}")
    print(f"{'Avg MAE ($)':<34} | ${res_st['avg_mae_usd']:<17.2f} | ${res_rsi_sma['avg_mae_usd']:<17.2f} | ${res_rsi_hl2['avg_mae_usd']:<17.2f} | ${res_rsi_ema['avg_mae_usd']:<17.2f}")
    print(f"{'Worst MAE ($)':<34} | ${res_st['worst_mae_usd']:<17.2f} | ${res_rsi_sma['worst_mae_usd']:<17.2f} | ${res_rsi_hl2['worst_mae_usd']:<17.2f} | ${res_rsi_ema['worst_mae_usd']:<17.2f}")

    # Also show Oct 1 onwards if dataset is 5m
    OCT_1_TS = 1790812800
    if times[-1] >= OCT_1_TS and times[0] < OCT_1_TS:
        oct_mask = times >= OCT_1_TS
        res_st_oct = backtest_regimes(st_trend[oct_mask], closes[oct_mask], highs[oct_mask], lows[oct_mask], times[oct_mask], "SuperTrend (Oct 1+)")
        res_rsi_oct = backtest_regimes(sig_rsi_ma_sma[oct_mask], closes[oct_mask], highs[oct_mask], lows[oct_mask], times[oct_mask], "RSI-MA (Oct 1+)")
        print(f"\n--- Sub-Period Audit: Oct 1, 2026 to Present (Recent 4,400+ Bars) ---")
        print(f"SuperTrend Flips: {res_st_oct['flips_count']} | Whipsaws <=3b: {res_st_oct['whipsaw_le_3']} ({res_st_oct['whipsaw_pct_le_3']:.1f}%) | Net PnL: ${res_st_oct['net_pnl']:.2f} | PF: {res_st_oct['profit_factor']:.2f} | WR: {res_st_oct['win_rate']:.1f}%")
        print(f"RSI-MA Flips:     {res_rsi_oct['flips_count']} | Whipsaws <=3b: {res_rsi_oct['whipsaw_le_3']} ({res_rsi_oct['whipsaw_pct_le_3']:.1f}%) | Net PnL: ${res_rsi_oct['net_pnl']:.2f} | PF: {res_rsi_oct['profit_factor']:.2f} | WR: {res_rsi_oct['win_rate']:.1f}%")

run_dataset_part1('tests/mgc1_5m_all.json', 'MGC1! 5-Minute (Full 11,040 Bars)')
run_dataset_part1('tests/mgc1_2m.json', 'MGC1! 2-Minute (Recent 465 Bars)')
