#!/usr/bin/env python3
"""
risk_expectancy_modeling.py
Comprehensive Risk, Capital Preservation, Expectancy and Friction Analysis Engine
for Supertrend V4 + RSI Permutations on MNQ Futures (5m and 2m).
"""

import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone

POINT_VALUE = 2.0       # $2.00 per point for MNQ
TICK_SIZE = 0.25        # 0.25 pt
TICK_VALUE = 0.50       # $0.50 per tick
SLIPPAGE_PER_FILL_PTS = 0.25   # 0.25 pt ($0.50) per fill
SLIPPAGE_PER_FILL_USD = 0.50   # $0.50 per fill
COMMISSION_ROUNDTRIP = 1.20    # $1.20 round-trip commission ($0.60 per fill)
TOTAL_FRICTION_ROUNDTRIP = 2.20 # $1.20 comm + $1.00 slippage (2 fills)

def load_data(filepath):
    df = pd.read_csv(filepath)
    times = df['time'].values.astype(np.int64)
    opens = df['open'].values.astype(np.float64)
    highs = df['high'].values.astype(np.float64)
    lows = df['low'].values.astype(np.float64)
    closes = df['close'].values.astype(np.float64)
    volumes = df['volume'].values.astype(np.float64)
    return times, opens, highs, lows, closes, volumes

# -----------------------------------------------------------------------------
# 1. PINE SCRIPT V6 EXACT INDICATOR IMPLEMENTATIONS
# -----------------------------------------------------------------------------
def calc_rma(src, length):
    n = len(src)
    out = np.zeros(n, dtype=np.float64)
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
    out = np.zeros(n, dtype=np.float64)
    s = 0.0
    for i in range(n):
        s += src[i]
        if i >= length:
            s -= src[i - length]
            out[i] = s / length
        else:
            out[i] = s / (i + 1)
    return out

def calc_wma(src, length):
    n = len(src)
    out = np.zeros(n, dtype=np.float64)
    weights = np.arange(1, length + 1, dtype=np.float64)
    w_sum = weights.sum()
    for i in range(n):
        if i < length - 1:
            w = np.arange(1, i + 2, dtype=np.float64)
            out[i] = np.dot(src[:i+1], w) / w.sum()
        else:
            out[i] = np.dot(src[i - length + 1 : i + 1], weights) / w_sum
    return out

def calc_ema(src, length):
    n = len(src)
    out = np.zeros(n, dtype=np.float64)
    alpha = 2.0 / (length + 1.0)
    for i in range(n):
        if i == 0:
            out[i] = src[i]
        else:
            out[i] = alpha * src[i] + (1.0 - alpha) * out[i-1]
    return out

def calc_rsi(src, length=14):
    n = len(src)
    up_chg = np.zeros(n, dtype=np.float64)
    dn_chg = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        d = src[i] - src[i-1]
        if d > 0:
            up_chg[i] = d
        else:
            dn_chg[i] = -d
    avg_up = calc_rma(up_chg, length)
    avg_dn = calc_rma(dn_chg, length)
    rsi = np.full(n, 50.0, dtype=np.float64)
    for i in range(n):
        if avg_dn[i] == 0:
            rsi[i] = 100.0
        elif avg_up[i] == 0:
            rsi[i] = 0.0
        else:
            rsi[i] = 100.0 - (100.0 / (1.0 + avg_up[i] / avg_dn[i]))
    return rsi

def calc_supertrend(highs, lows, closes, length=80, mult=1.4, method="SMA", source="hl2"):
    n = len(closes)
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    
    if method == "SMA":
        atr = calc_sma(tr, length)
    elif method == "EMA":
        atr = calc_ema(tr, length)
    else: # RMA
        atr = calc_rma(tr, length)
        
    src_price = (highs + lows) / 2.0 if source == "hl2" else closes
    
    up = np.zeros(n, dtype=np.float64)
    dn = np.zeros(n, dtype=np.float64)
    trend = np.ones(n, dtype=int)
    
    for i in range(n):
        b_up = src_price[i] - mult * atr[i]
        b_dn = src_price[i] + mult * atr[i]
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
    raw_stoch = np.full(n, 50.0, dtype=np.float64)
    for i in range(n):
        w = rsi[max(0, i - lengthStoch + 1) : i + 1]
        lo, hi = min(w), max(w)
        raw_stoch[i] = ((rsi[i] - lo) / (hi - lo) * 100.0) if (hi - lo) > 0 else 50.0
    stochK = calc_sma(raw_stoch, smoothK)
    stochD = calc_sma(stochK, smoothD)
    return stochK, stochD, rsi

def calc_early_wick_dots(highs, lows, closes, opens, dot_mode="STRICT", os_level=30.0, ob_level=65.0):
    """
    Exact Pine Script V4 Early Wick Reversal & Take-Profit Engine
    """
    n = len(closes)
    hl2 = (highs + lows) / 2.0
    rsiVal = calc_rsi(hl2, 14)
    rsiMa = calc_wma(rsiVal, 14)
    rsiCloseVal = calc_rsi(closes, 14)
    
    rsiMinSensor = np.minimum(rsiVal, rsiCloseVal)
    rsiMaxSensor = np.maximum(rsiVal, rsiCloseVal)
    
    green_dots = np.zeros(n, dtype=bool)
    yellow_dots = np.zeros(n, dtype=bool)
    
    armBullDot = False
    armBearDot = False
    lastBullTouchBar = -9999
    lastBearTouchBar = -9999
    wickLowBar = -9999
    wickLowPrice = 1e10
    wickHighBar = -9999
    wickHighPrice = -1e10
    
    dotTrend = 0 # 1 = Bull, -1 = Bear
    multiWaveArmed = True
    lastAnyDotBar = -9999
    bandMemoryBars = 8
    dotMinSpacing = 4
    
    for i in range(1, n):
        # 1. Arming
        canArmBull = (dotTrend != 1) if dot_mode == "STRICT" else (dotTrend != 1 or multiWaveArmed)
        canArmBear = (dotTrend != -1) if dot_mode == "STRICT" else (dotTrend != -1 or multiWaveArmed)
        
        if rsiMinSensor[i] <= os_level and canArmBull:
            if not armBullDot:
                wickLowBar = i
                wickLowPrice = lows[i]
            armBullDot = True
            lastBullTouchBar = i
            
        if rsiMaxSensor[i] >= ob_level and canArmBear:
            if not armBearDot:
                wickHighBar = i
                wickHighPrice = highs[i]
            armBearDot = True
            lastBearTouchBar = i
            
        # 2. Track extreme wicks
        if armBullDot and lows[i] < wickLowPrice:
            wickLowPrice = lows[i]
            wickLowBar = i
        if armBearDot and highs[i] > wickHighPrice:
            wickHighPrice = highs[i]
            wickHighBar = i
            
        # 3. Memory
        bullWithinMemory = armBullDot and ((i - lastBullTouchBar) <= bandMemoryBars)
        bearWithinMemory = armBearDot and ((i - lastBearTouchBar) <= bandMemoryBars)
        
        # 4. Momentum turn
        rsiCrossUp = (rsiVal[i] > rsiMa[i] and rsiVal[i-1] <= rsiMa[i-1])
        rsiCrossDn = (rsiVal[i] < rsiMa[i] and rsiVal[i-1] >= rsiMa[i-1])
        rsiHookUp = (rsiVal[i] > rsiVal[i-1])
        rsiHookDn = (rsiVal[i] < rsiVal[i-1])
        bullTurn = rsiHookUp or rsiCrossUp
        bearTurn = rsiHookDn or rsiCrossDn
        
        # 5. Structure
        candleRng = max(highs[i] - lows[i], 1e-5)
        isGreenCandle = closes[i] > opens[i]
        isRedCandle = closes[i] < opens[i]
        
        bullHighBreak = closes[i] > highs[i-1]
        bullEngulfing = (closes[i] > opens[i-1]) and (opens[i] <= closes[i-1])
        bullPinReject = (closes[i] - lows[i]) >= 0.65 * candleRng
        bullStructureOk = isGreenCandle and (bullHighBreak or bullEngulfing or bullPinReject)
        
        bearLowBreak = closes[i] < lows[i-1]
        bearEngulfing = (closes[i] < opens[i-1]) and (opens[i] >= closes[i-1])
        bearPinReject = (highs[i] - closes[i]) >= 0.65 * candleRng
        bearStructureOk = isRedCandle and (bearLowBreak or bearEngulfing or bearPinReject)
        
        rawBullDot = bullWithinMemory and bullTurn and bullStructureOk
        rawBearDot = bearWithinMemory and bearTurn and bearStructureOk
        
        spacingOk = (i - lastAnyDotBar) >= dotMinSpacing
        bullDotAllowed = (dotTrend != 1) and spacingOk if dot_mode == "STRICT" else (dotTrend != 1 or multiWaveArmed) and spacingOk
        bearDotAllowed = (dotTrend != -1) and spacingOk if dot_mode == "STRICT" else (dotTrend != -1 or multiWaveArmed) and spacingOk
        
        if rawBullDot and bullDotAllowed:
            green_dots[i] = True
            dotTrend = 1
            multiWaveArmed = False
            lastAnyDotBar = i
            armBullDot = False
            armBearDot = False
            
        if rawBearDot and bearDotAllowed:
            yellow_dots[i] = True
            dotTrend = -1
            multiWaveArmed = False
            lastAnyDotBar = i
            armBearDot = False
            armBullDot = False
            
        # Disarm safeguards
        if armBullDot and (((i - lastBullTouchBar) > bandMemoryBars) or (rsiVal[i] > 50.0)):
            armBullDot = False
        if armBearDot and (((i - lastBearTouchBar) > bandMemoryBars) or (rsiVal[i] < 50.0)):
            armBearDot = False
            
    return green_dots, yellow_dots

print("Indicators module loaded.")
