#!/usr/bin/env python3
import json
import math
from datetime import datetime, timezone

def run_audit():
    with open('tests/mgc1_5m_all.json', 'r') as f:
        bars_raw = json.load(f)

    n = len(bars_raw)
    times  = [b[0] for b in bars_raw]
    opens  = [b[1] for b in bars_raw]
    highs  = [b[2] for b in bars_raw]
    lows   = [b[3] for b in bars_raw]
    closes = [b[4] for b in bars_raw]
    vols   = [b[5] for b in bars_raw]

    OCT_1_TS = 1790812800  # 2026-10-01 00:00:00 UTC

    # 1. Exact Pine RMA & SMA functions
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

    # 2. SuperTrend V3 Core (ATR 80, Mult 2.2, hl2, RMA)
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
            dn[i] = min(b_dn, dn[i-1]) if closes[i-1] < dn1 else b_dn
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

    return times, opens, highs, lows, closes, vols, trend, up, dn, atr80, atr14, stochK, stochD

if __name__ == '__main__':
    run_audit()
    print("Init passed")
