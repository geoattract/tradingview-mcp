import json
import numpy as np

def compute_rsi(prices, length=14):
    deltas = np.diff(prices)
    seed = deltas[:length]
    up = seed[seed >= 0].sum() / length
    down = -seed[seed < 0].sum() / length
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:length] = 100. - 100. / (1. + rs) if down != 0 else 100.

    alpha = 1.0 / length
    cur_up = up
    cur_down = down
    for i in range(length, len(prices)):
        d = deltas[i - 1]
        u = d if d > 0 else 0.0
        dn = -d if d < 0 else 0.0
        cur_up = alpha * u + (1.0 - alpha) * cur_up
        cur_down = alpha * dn + (1.0 - alpha) * cur_down
        if cur_down == 0:
            rsi[i] = 100.0
        else:
            rs = cur_up / cur_down
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def run_test(file_path, name):
    with open(file_path) as f:
        bars = json.load(f)
    print(f"\n==========================================")
    print(f"ANALYSIS FOR {name}: {len(bars)} BARS")
    print(f"==========================================")
    
    if isinstance(bars[0], dict):
        closes = np.array([b['close'] for b in bars], dtype=float)
        highs = np.array([b['high'] for b in bars], dtype=float)
        lows = np.array([b['low'] for b in bars], dtype=float)
    else:
        # [time, open, high, low, close, volume]
        highs = np.array([b[2] for b in bars], dtype=float)
        lows = np.array([b[3] for b in bars], dtype=float)
        closes = np.array([b[4] for b in bars], dtype=float)
        
    hl2 = (highs + lows) / 2.0
    
    rsi_close = compute_rsi(closes, 14)
    rsi_hl2 = compute_rsi(hl2, 14)
    
    # 1. Volatility / Noise (average absolute 1-bar change in RSI)
    d_close = np.abs(np.diff(rsi_close[14:]))
    d_hl2 = np.abs(np.diff(rsi_hl2[14:]))
    print(f"Average 1-bar RSI jitter/delta: Close = {d_close.mean():.3f} pts | hl2 = {d_hl2.mean():.3f} pts")
    print(f"Noise reduction with hl2: {((d_close.mean() - d_hl2.mean()) / d_close.mean()) * 100:.2f}% smoother")
    
    # 2. Number of directional turns (whipsaw count)
    diff_c = np.diff(rsi_close[14:])
    diff_h = np.diff(rsi_hl2[14:])
    turns_c = np.sum((diff_c[:-1] * diff_c[1:]) < 0)
    turns_h = np.sum((diff_h[:-1] * diff_h[1:]) < 0)
    print(f"Directional hook/whipsaw flips: Close = {turns_c} | hl2 = {turns_h}")
    print(f"Whipsaw reduction: {turns_c - turns_h} fewer false flips ({((turns_c - turns_h)/turns_c)*100:.1f}%)")
    
    # 3. Peak / Trough timing comparison vs Price high/low pivots
    exact_matches_c = 0
    exact_matches_h = 0
    total_pivots = 0
    
    for i in range(15, len(bars) - 2):
        is_pivot_h = highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]
        is_pivot_l = lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]
        
        if is_pivot_h:
            total_pivots += 1
            if rsi_close[i] >= rsi_close[i-1] and rsi_close[i] >= rsi_close[i+1]:
                exact_matches_c += 1
            if rsi_hl2[i] >= rsi_hl2[i-1] and rsi_hl2[i] >= rsi_hl2[i+1]:
                exact_matches_h += 1
                
        elif is_pivot_l:
            total_pivots += 1
            if rsi_close[i] <= rsi_close[i-1] and rsi_close[i] <= rsi_close[i+1]:
                exact_matches_c += 1
            if rsi_hl2[i] <= rsi_hl2[i-1] and rsi_hl2[i] <= rsi_hl2[i+1]:
                exact_matches_h += 1
                
    print(f"Total True 2-bar Price Swings Tested: {total_pivots}")
    print(f"Exact Same-Bar Pivot Synchronization:")
    print(f"  RSI(Close) matched exact turning candle: {exact_matches_c} / {total_pivots} ({exact_matches_c/total_pivots*100:.1f}%)")
    print(f"  RSI(hl2)   matched exact turning candle: {exact_matches_h} / {total_pivots} ({exact_matches_h/total_pivots*100:.1f}%)")

run_test('tests/mgc1_2m.json', 'MGC1! 2-Minute (Recent Session)')
run_test('tests/mgc1_5m_all.json', 'MGC1! 5-Minute (Full 11,040 Bars Dataset)')
