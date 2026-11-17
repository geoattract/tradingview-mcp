import json
import math
import numpy as np

def load_data(filepath):
    with open(filepath, 'r') as f:
        bars_raw = json.load(f)
    if isinstance(bars_raw[0], dict):
        times = [b['time'] for b in bars_raw]
        opens = [b['open'] for b in bars_raw]
        highs = [b['high'] for b in bars_raw]
        lows = [b['low'] for b in bars_raw]
        closes = [b['close'] for b in bars_raw]
        volumes = [b.get('volume', 0) for b in bars_raw]
    else:
        times = [b[0] for b in bars_raw]
        opens = [b[1] for b in bars_raw]
        highs = [b[2] for b in bars_raw]
        lows = [b[3] for b in bars_raw]
        closes = [b[4] for b in bars_raw]
        volumes = [b[5] for b in bars_raw]
    return np.array(times), np.array(opens, dtype=float), np.array(highs, dtype=float), np.array(lows, dtype=float), np.array(closes, dtype=float), np.array(volumes, dtype=float)

def calc_rma(src, length):
    n = len(src)
    out = np.zeros(n)
    alpha = 1.0 / length
    s = 0.0
    for i in range(n):
        if i < length:
            s += src[i]
            out[i] = s / (i + 1)
        else:
            out[i] = alpha * src[i] + (1.0 - alpha) * out[i-1]
    return out

def calc_sma(src, length):
    n = len(src)
    out = np.zeros(n)
    s = 0.0
    for i in range(n):
        s += src[i]
        if i >= length:
            s -= src[i - length]
            out[i] = s / length
        else:
            out[i] = s / (i + 1)
    return out

def calc_ema(src, length):
    n = len(src)
    out = np.zeros(n)
    alpha = 2.0 / (length + 1)
    s = 0.0
    for i in range(n):
        if i == 0:
            out[i] = src[i]
        else:
            out[i] = alpha * src[i] + (1.0 - alpha) * out[i-1]
    return out

def calc_rsi(src, length=14):
    n = len(src)
    up_chg = np.zeros(n)
    dn_chg = np.zeros(n)
    for i in range(1, n):
        d = src[i] - src[i-1]
        if d > 0:
            up_chg[i] = d
        else:
            dn_chg[i] = -d
    avg_up = calc_rma(up_chg, length)
    avg_dn = calc_rma(dn_chg, length)
    rsi = np.full(n, 50.0)
    for i in range(n):
        if avg_dn[i] == 0:
            rsi[i] = 100.0
        elif avg_up[i] == 0:
            rsi[i] = 0.0
        else:
            rsi[i] = 100.0 - (100.0 / (1.0 + avg_up[i] / avg_dn[i]))
    return rsi

def calc_supertrend(highs, lows, closes, length=80, mult=2.2):
    n = len(closes)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr = calc_rma(tr, length)
    
    up = np.zeros(n)
    dn = np.zeros(n)
    trend = np.ones(n, dtype=int)
    for i in range(n):
        hl2 = (highs[i] + lows[i]) / 2.0
        b_up = hl2 - mult * atr[i]
        b_dn = hl2 + mult * atr[i]
        if i == 0:
            up[i], dn[i], trend[i] = b_up, b_dn, 1
        else:
            up[i] = max(b_up, up[i-1]) if closes[i-1] > up[i-1] else b_up
            dn[i] = min(b_dn, dn[i-1]) if closes[i-1] < dn[i-1] else b_dn
            if trend[i-1] == -1 and closes[i] > dn[i-1]:
                trend[i] = 1
            elif trend[i-1] == 1 and closes[i] < up[i-1]:
                trend[i] = -1
            else:
                trend[i] = trend[i-1]
    return trend, up, dn, atr

def calc_stoch_rsi(closes, lengthRSI=14, lengthStoch=14, smoothK=3, smoothD=3):
    rsi = calc_rsi(closes, lengthRSI)
    n = len(closes)
    raw_stoch = np.full(n, 50.0)
    for i in range(n):
        w = rsi[max(0, i - lengthStoch + 1) : i + 1]
        lo, hi = min(w), max(w)
        raw_stoch[i] = ((rsi[i] - lo) / (hi - lo) * 100.0) if (hi - lo) > 0 else 50.0
    stochK = calc_sma(raw_stoch, smoothK)
    stochD = calc_sma(stochK, smoothD)
    return stochK, stochD, rsi

print("Module defined successfully.")
