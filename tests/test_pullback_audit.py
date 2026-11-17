import json
import math
import numpy as np

with open('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests/mgc1_5m_all.json', 'r') as f:
    bars_raw = json.load(f)

n = len(bars_raw)
times  = [b[0] for b in bars_raw]
opens  = [b[1] for b in bars_raw]
highs  = [b[2] for b in bars_raw]
lows   = [b[3] for b in bars_raw]
closes = [b[4] for b in bars_raw]

OCT_1_TS = 1790812800

def calc_rma(src, length):
    out = [0.0] * n
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
    out = [0.0] * n
    s = 0.0
    for i in range(n):
        s += src[i]
        if i >= length:
            s -= src[i - length]
            out[i] = s / length
        else:
            out[i] = s / (i + 1)
    return out

tr = [highs[0] - lows[0]] + [
    max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    for i in range(1, n)
]
atr80 = calc_rma(tr, 80)
atr14 = calc_rma(tr, 14)

# SuperTrend V3 Core (MGC1! Preset: ATR 80, Mult 2.2, hl2, RMA)
up = [0.0] * n
dn = [0.0] * n
trend = [1] * n
for i in range(n):
    hl2 = (highs[i] + lows[i]) / 2.0
    b_up = hl2 - 2.2 * atr80[i]
    b_dn = hl2 + 2.2 * atr80[i]
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

# Stoch RSI (3, 3, 14, 14, close)
up_chg = [0.0] * n
dn_chg = [0.0] * n
for i in range(1, n):
    diff = closes[i] - closes[i-1]
    up_chg[i] = max(diff, 0.0)
    dn_chg[i] = max(-diff, 0.0)
avg_up = calc_rma(up_chg, 14)
avg_dn = calc_rma(dn_chg, 14)
rsi_val = [50.0] * n
for i in range(n):
    if avg_dn[i] == 0: rsi_val[i] = 100.0
    elif avg_up[i] == 0: rsi_val[i] = 0.0
    else: rsi_val[i] = 100.0 - (100.0 / (1.0 + avg_up[i] / avg_dn[i]))
raw_stoch = [50.0] * n
for i in range(n):
    w = rsi_val[max(0, i - 13) : i + 1]
    lo, hi = min(w), max(w)
    raw_stoch[i] = ((rsi_val[i] - lo) / (hi - lo) * 100.0) if (hi - lo) > 0 else 50.0
stochK = calc_sma(raw_stoch, 3)
stochD = calc_sma(stochK, 3)

def generate_pullback_signals(engine_mode="SRSI_CROSS", pb_retrace_atr=1.25, srsi_os=30.0, srsi_ob=70.0, req_candle=True):
    srsiBullArmed = False
    srsiBearArmed = False

    waveHigh    = highs[0]
    waveHighBar = 0
    lastRefLow  = lows[0]
    waveLow     = lows[0]
    waveLowBar  = 0
    lastRefHigh = highs[0]

    pbBuySig  = [False] * n
    pbSellSig = [False] * n

    for i in range(1, n):
        inBullWave = (trend[i] == 1 and trend[i-1] == 1)
        inBearWave = (trend[i] == -1 and trend[i-1] == -1)

        if trend[i] != trend[i-1]:
            srsiBullArmed = False
            srsiBearArmed = False
            waveHigh      = highs[i]
            waveHighBar   = i
            lastRefLow    = lows[i]
            waveLow       = lows[i]
            waveLowBar    = i
            lastRefHigh   = highs[i]
        else:
            if trend[i] == 1 and highs[i] > waveHigh:
                waveHigh    = highs[i]
                waveHighBar = i
            if trend[i] == -1 and lows[i] < waveLow:
                waveLow     = lows[i]
                waveLowBar  = i

        if inBullWave and stochK[i] <= srsi_os and stochK[i] <= stochD[i]:
            srsiBullArmed = True
        if inBearWave and stochK[i] >= srsi_ob and stochK[i] >= stochD[i]:
            srsiBearArmed = True

        if stochK[i] >= srsi_ob:
            srsiBullArmed = False
        if stochK[i] <= srsi_os:
            srsiBearArmed = False

        bullCandleOk = (not req_candle) or (closes[i] > opens[i])
        bearCandleOk = (not req_candle) or (closes[i] < opens[i])

        # Engine 1: SRSI_CROSS
        kTurnUp       = stochK[i] > stochD[i] and stochK[i] > stochK[i-1]
        kTurnDown     = stochK[i] < stochD[i] and stochK[i] < stochK[i-1]
        srsiCrossBuy  = inBullWave and srsiBullArmed and kTurnUp   and bullCandleOk
        srsiCrossSell = inBearWave and srsiBearArmed and kTurnDown and bearCandleOk

        # Engine 2: ATR_WAVE
        trough2      = min(lows[i], lows[i-1])
        bullPullback = waveHigh - trough2
        bullImpulse  = waveHigh - lastRefLow
        low2         = lows[i-2] if i >= 2 else lows[i]
        isLocalTrough= trough2 <= min(low2, lows[i-1])
        bullTurnUp   = closes[i] > opens[i] and (closes[i] > highs[i-1] or (lows[i] <= lows[i-1] and closes[i] > closes[i-1]))
        nearBullLine = ((lows[i] - up[i]) <= 0.45 * atr80[i]) or ((lows[i-1] - up[i-1]) <= 0.45 * atr80[i-1])
        atrWaveBuy   = inBullWave and bullImpulse >= 1.2 * atr14[i] and (i - waveHighBar) >= 2 and (bullPullback >= pb_retrace_atr * atr14[i] or nearBullLine) and isLocalTrough and bullTurnUp

        peak2        = max(highs[i], highs[i-1])
        bearPullback = peak2 - waveLow
        bearImpulse  = lastRefHigh - waveLow
        high2        = highs[i-2] if i >= 2 else highs[i]
        isLocalPeak  = peak2 >= max(high2, highs[i-1])
        bearTurnDown = closes[i] < opens[i] and (closes[i] < lows[i-1] or (highs[i] >= highs[i-1] and closes[i] < closes[i-1]))
        nearBearLine = ((dn[i] - highs[i]) <= 0.45 * atr80[i]) or ((dn[i-1] - highs[i-1]) <= 0.45 * atr80[i-1])
        atrWaveSell  = inBearWave and bearImpulse >= 1.2 * atr14[i] and (i - waveLowBar) >= 2 and (bearPullback >= pb_retrace_atr * atr14[i] or nearBearLine) and isLocalPeak and bearTurnDown

        rawBuy  = srsiCrossBuy if engine_mode == "SRSI_CROSS" else atrWaveBuy
        rawSell = srsiCrossSell if engine_mode == "SRSI_CROSS" else atrWaveSell

        if rawBuy:
            pbBuySig[i] = True
            srsiBullArmed = False
            lastRefLow = trough2
            waveHigh = highs[i]
            waveHighBar = i
        if rawSell:
            pbSellSig[i] = True
            srsiBearArmed = False
            lastRefHigh = peak2
            waveLow = lows[i]
            waveLowBar = i

    return pbBuySig, pbSellSig

buy_srsi, sell_srsi = generate_pullback_signals("SRSI_CROSS")
buy_atr, sell_atr = generate_pullback_signals("ATR_WAVE")

print("SRSI Buy signals:", sum(buy_srsi[2232:]), "Sell signals:", sum(sell_srsi[2232:]))
print("ATR Buy signals:", sum(buy_atr[2232:]), "Sell signals:", sum(sell_atr[2232:]))
