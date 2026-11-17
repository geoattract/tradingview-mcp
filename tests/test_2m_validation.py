import pandas as pd
import numpy as np

df = pd.read_csv('mnq_2m_data.csv')
times = df['time'].values
opens = df['open'].values
highs = df['high'].values
lows = df['low'].values
closes = df['close'].values
n = len(df)

# Warmup: first 1000 bars (Oct 26), eval from bar 1000 to n-1
EVAL_START_BAR = 1000

def run_2m_sim(period, mult, method, src_name, zone_mode, rsi_len, req_candle, cooldown, dot_os, dot_ob):
    src = (highs + lows) / 2.0 if src_name == 'hl2' else closes
    
    # TR
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        
    if method == 'SMA':
        atr = np.zeros(n)
        s = 0.0
        for i in range(n):
            s += tr[i]
            if i >= period: s -= tr[i - period]; atr[i] = s / period
            else: atr[i] = s / (i + 1)
    elif method == 'EMA':
        atr = np.zeros(n)
        alpha = 2.0 / (period + 1.0)
        s = 0.0
        for i in range(n):
            if i < period: s += tr[i]; atr[i] = s / (i + 1)
            else: atr[i] = alpha * tr[i] + (1.0 - alpha) * atr[i-1]
    else: # RMA
        atr = np.zeros(n)
        alpha = 1.0 / period
        s = 0.0
        for i in range(n):
            if i < period: s += tr[i]; atr[i] = s / (i + 1)
            else: atr[i] = alpha * tr[i] + (1.0 - alpha) * atr[i-1]
            
    up = np.zeros(n)
    dn = np.zeros(n)
    trend = np.ones(n, dtype=np.int32)
    for i in range(n):
        b_up = src[i] - mult * atr[i]
        b_dn = src[i] + mult * atr[i]
        if i == 0:
            up[i] = b_up; dn[i] = b_dn; trend[i] = 1
        else:
            up[i] = max(b_up, up[i-1]) if closes[i-1] > up[i-1] else b_up
            dn[i] = min(b_dn, dn[i-1]) if closes[i-1] < dn[i-1] else b_dn
            if trend[i-1] == -1 and closes[i] > dn[i-1]: trend[i] = 1
            elif trend[i-1] == 1 and closes[i] < up[i-1]: trend[i] = -1
            else: trend[i] = trend[i-1]
            
    # RSI & Dots
    def calc_rma(src_arr, length):
        out = np.zeros(n)
        alpha = 1.0 / length
        s = 0.0
        for i in range(n):
            if i < length: s += src_arr[i]; out[i] = s / (i + 1)
            else: out[i] = alpha * src_arr[i] + (1.0 - alpha) * out[i-1]
        return out
        
    def calc_wma(src_arr, length):
        out = np.zeros(n)
        weights = np.arange(1, length + 1)
        w_sum = weights.sum()
        for i in range(n):
            if i < length - 1:
                w = np.arange(1, i + 2)
                out[i] = np.dot(src_arr[:i+1], w) / w.sum()
            else:
                out[i] = np.dot(src_arr[i - length + 1 : i + 1], weights) / w_sum
        return out
        
    def calc_rsi(src_arr, length=14):
        up_chg = np.zeros(n)
        dn_chg = np.zeros(n)
        for i in range(1, n):
            d = src_arr[i] - src_arr[i-1]
            if d > 0: up_chg[i] = d
            else: dn_chg[i] = -d
        avg_up = calc_rma(up_chg, length)
        avg_dn = calc_rma(dn_chg, length)
        rsi = np.full(n, 50.0)
        for i in range(n):
            if avg_dn[i] == 0: rsi[i] = 100.0
            elif avg_up[i] == 0: rsi[i] = 0.0
            else: rsi[i] = 100.0 - (100.0 / (1.0 + avg_up[i] / avg_dn[i]))
        return rsi

    rsiVal = calc_rsi(src, 14)
    rsiMa = calc_wma(rsiVal, 14)
    rsiCloseVal = calc_rsi(closes, 14)
    
    rsiMinSensor = np.minimum(rsiVal, rsiCloseVal)
    rsiMaxSensor = np.maximum(rsiVal, rsiCloseVal)
    
    armBullDot = False; armBearDot = False
    lastBullTouchBar = -9999; lastBearTouchBar = -9999
    dotTrend = 0; lastAnyDotBar = -9999
    
    green_dots = np.zeros(n, dtype=bool)
    yellow_dots = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        canArmBull = (dotTrend != 1); canArmBear = (dotTrend != -1)
        if rsiMinSensor[i] <= dot_os and canArmBull:
            armBullDot = True; lastBullTouchBar = i
        if rsiMaxSensor[i] >= dot_ob and canArmBear:
            armBearDot = True; lastBearTouchBar = i
            
        bullWithinMemory = armBullDot and ((i - lastBullTouchBar) <= 8)
        bearWithinMemory = armBearDot and ((i - lastBearTouchBar) <= 8)
        
        rsiCrossUp = (rsiVal[i] > rsiMa[i] and rsiVal[i-1] <= rsiMa[i-1])
        rsiCrossDn = (rsiVal[i] < rsiMa[i] and rsiVal[i-1] >= rsiMa[i-1])
        bullTurn = (rsiVal[i] > rsiVal[i-1]) or rsiCrossUp
        bearTurn = (rsiVal[i] < rsiVal[i-1]) or rsiCrossDn
        
        candleRng = max(highs[i] - lows[i], 1e-5)
        bullStructureOk = (closes[i] > opens[i]) and (
            (closes[i] > highs[i-1]) or 
            ((closes[i] > opens[i-1]) and (opens[i] <= closes[i-1])) or 
            ((closes[i] - lows[i]) >= 0.65 * candleRng)
        )
        bearStructureOk = (closes[i] < opens[i]) and (
            (closes[i] < lows[i-1]) or 
            ((closes[i] < opens[i-1]) and (opens[i] >= closes[i-1])) or 
            ((highs[i] - closes[i]) >= 0.65 * candleRng)
        )
        
        spacingOk = (i - lastAnyDotBar) >= 4
        if bullWithinMemory and bullTurn and bullStructureOk and (dotTrend != 1) and spacingOk:
            dotTrend = 1; lastAnyDotBar = i; armBullDot = False; armBearDot = False; green_dots[i] = True
        elif bearWithinMemory and bearTurn and bearStructureOk and (dotTrend != -1) and spacingOk:
            dotTrend = -1; lastAnyDotBar = i; armBearDot = False; armBullDot = False; yellow_dots[i] = True
            
        if armBullDot and (((i - lastBullTouchBar) > 8) or (rsiVal[i] > 50.0)): armBullDot = False
        if armBearDot and (((i - lastBearTouchBar) > 8) or (rsiVal[i] < 50.0)): armBearDot = False

    # Pullbacks
    def calc_sma_arr(src_arr, length):
        out = np.zeros(n)
        s = 0.0
        for i in range(n):
            s += src_arr[i]
            if i >= length: s -= src_arr[i - length]; out[i] = s / length
            else: out[i] = s / (i + 1)
        return out
        
    srsiRsiVal = calc_rsi(closes, rsi_len)
    srsiStochVal = np.full(n, 50.0)
    for i in range(n):
        w = srsiRsiVal[max(0, i - 13) : i + 1]
        lo = np.min(w); hi = np.max(w)
        srsiStochVal[i] = (srsiRsiVal[i] - lo) / (hi - lo) * 100.0 if hi > lo else 50.0
    stochK = calc_sma_arr(srsiStochVal, 3)
    stochD = calc_sma_arr(stochK, 3)
    
    lowestK = np.zeros(n); lowestD = np.zeros(n); lowestS = np.zeros(n)
    highestK = np.zeros(n); highestD = np.zeros(n); highestS = np.zeros(n)
    for i in range(n):
        w_k = stochK[max(0, i-2) : i+1]; w_d = stochD[max(0, i-2) : i+1]; w_s = srsiStochVal[max(0, i-2) : i+1]
        lowestK[i] = np.min(w_k); lowestD[i] = np.min(w_d); lowestS[i] = np.min(w_s)
        highestK[i] = np.max(w_k); highestD[i] = np.max(w_d); highestS[i] = np.max(w_s)
        
    kCrossOver = np.concatenate(([False], (stochK[1:] > stochD[1:]) & (stochK[:-1] <= stochD[:-1])))
    kCrossUnder = np.concatenate(([False], (stochK[1:] < stochD[1:]) & (stochK[:-1] >= stochD[:-1])))
    
    os_thresh = 30.0 if '30' in zone_mode else (20.0 if '20' in zone_mode else 999.0)
    ob_thresh = 70.0 if '70' in zone_mode else (80.0 if '80' in zone_mode else -999.0)
    
    inZoneBuy = np.ones(n, dtype=bool) if ('Anywhere' in zone_mode) else ((lowestK <= os_thresh) | (lowestD <= os_thresh) | (lowestS <= os_thresh))
    inZoneSell = np.ones(n, dtype=bool) if ('Anywhere' in zone_mode) else ((highestK >= ob_thresh) | (highestD >= ob_thresh) | (highestS >= ob_thresh))
    pb_buy = np.zeros(n, dtype=bool); pb_sell = np.zeros(n, dtype=bool)
    lastPbBar = -9999
    for i in range(1, n):
        candleOkBuy = (not req_candle) or (closes[i] > opens[i])
        candleOkSell = (not req_candle) or (closes[i] < opens[i])
        if (i - lastPbBar) >= cooldown:
            if (trend[i] == 1 and trend[i-1] == 1) and kCrossOver[i] and inZoneBuy[i] and candleOkBuy:
                pb_buy[i] = True; lastPbBar = i
            elif (trend[i] == -1 and trend[i-1] == -1) and kCrossUnder[i] and inZoneSell[i] and candleOkSell:
                pb_sell[i] = True; lastPbBar = i

    # Trade simulation
    trades = []
    pos = 0; entry_price = 0.0
    for i in range(1, n - 1):
        if i < EVAL_START_BAR:
            if trend[i] != trend[i-1]:
                pos = trend[i]; entry_price = opens[i+1]
            continue
        exec_price = opens[i+1]
        if trend[i] != trend[i-1]:
            if pos != 0:
                pnl = (exec_price - entry_price) if pos == 1 else (entry_price - exec_price)
                trades.append(pnl - 1.20)
            pos = trend[i]; entry_price = exec_price
            continue
        if pos == 1 and yellow_dots[i] and trend[i] == 1:
            pnl = exec_price - entry_price
            trades.append(pnl - 1.20); pos = 0; continue
        elif pos == -1 and green_dots[i] and trend[i] == -1:
            pnl = entry_price - exec_price
            trades.append(pnl - 1.20); pos = 0; continue
        if pos == 0:
            if trend[i] == 1 and pb_buy[i]: pos = 1; entry_price = exec_price
            elif trend[i] == -1 and pb_sell[i]: pos = -1; entry_price = exec_price
            
    if pos != 0:
        exec_price = closes[-1]
        pnl = (exec_price - entry_price) if pos == 1 else (entry_price - exec_price)
        trades.append(pnl - 1.20)
        
    net_pts = sum(trades)
    wins = [t for t in trades if t > 0]
    wr = len(wins) / len(trades) * 100 if trades else 0
    gw = sum(wins); gl = abs(sum(t for t in trades if t <= 0))
    pf = gw / gl if gl > 0 else 999.0
    cum = 0.0; peak = 0.0; max_dd = 0.0
    for t in trades:
        cum += t
        if cum > peak: peak = cum
        if peak - cum > max_dd: max_dd = peak - cum
    calmar = net_pts / max_dd if max_dd > 0 else 0
    
    return {
        'net_pts': round(net_pts, 1),
        'net_usd': round(net_pts * 2.0, 2),
        'pf': round(pf, 3),
        'wr': round(wr, 1),
        'trades': len(trades),
        'max_dd_pts': round(max_dd, 1),
        'max_dd_usd': round(max_dd * 2.0, 2),
        'calmar': round(calmar, 2)
    }

print("=== 2-MINUTE TIMEFRAME OUT-OF-SAMPLE CROSS-VALIDATION ===")
configs = [
    ("Default 1 (80, 1.4 SMA hl2)", 80, 1.4, 'SMA', 'hl2', 'Cross in Zone (<=30 / >=70)', 14, False, 3, 30.0, 65.0),
    ("Default 2 (80, 2.0 SMA hl2)", 80, 2.0, 'SMA', 'hl2', 'Cross in Zone (<=30 / >=70)', 14, False, 3, 30.0, 65.0),
    ("Classic Baseline (10, 3.0 RMA hl2)", 10, 3.0, 'RMA', 'hl2', 'Cross in Zone (<=30 / >=70)', 14, False, 3, 30.0, 65.0),
    ("High Calmar Winner (10, 1.8 RMA hl2)", 10, 1.8, 'RMA', 'hl2', 'Cross in Zone (<=30 / >=70)', 14, False, 3, 35.0, 70.0),
    ("Robust Plateau Winner (100, 1.2 RMA hl2)", 100, 1.2, 'RMA', 'hl2', 'Cross in Zone (<=30 / >=70)', 14, False, 3, 35.0, 65.0),
    ("Global Optimum (80, 1.8 EMA close)", 80, 1.8, 'EMA', 'close', 'Cross in Zone (<=30 / >=70)', 14, False, 3, 35.0, 60.0),
]

for label, p, m, met, src, zm, rsi_l, rc, cd, os, ob in configs:
    res = run_2m_sim(p, m, met, src, zm, rsi_l, rc, cd, os, ob)
    print(f"{label:<42}: Net: {res['net_pts']:+7.1f} pts (${res['net_usd']:+8.2f}) | PF: {res['pf']:.3f} | WR: {res['wr']:.1f}% | DD: {res['max_dd_pts']:.1f} pts | Calmar: {res['calmar']:.2f} | Trades: {res['trades']}")
