#!/usr/bin/env python3
import json
import math
from datetime import datetime, timezone

def test_st():
    with open('tests/mgc1_5m_all.json', 'r') as f:
        bars_raw = json.load(f)

    n = len(bars_raw)
    times  = [b[0] for b in bars_raw]
    opens  = [b[1] for b in bars_raw]
    highs  = [b[2] for b in bars_raw]
    lows   = [b[3] for b in bars_raw]
    closes = [b[4] for b in bars_raw]
    vols   = [b[5] for b in bars_raw]

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

    tr = [highs[0] - lows[0]] + [
        max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        for i in range(1, n)
    ]
    atr80 = calc_rma(tr, 80)

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
            up1 = up[i-1]
            dn1 = dn[i-1]
            up[i] = max(b_up, up1) if closes[i-1] > up1 else b_up
            dn[i] = min(b_dn, dn1) if closes[i-1] < dn1 else b_dn
            if trend[i-1] == -1 and closes[i] > dn1:
                trend[i] = 1
            elif trend[i-1] == 1 and closes[i] < up1:
                trend[i] = -1
            else:
                trend[i] = trend[i-1]

    # Count flips from Oct 1
    oct1_idx = None
    for i in range(n):
        if times[i] >= OCT_1_TS:
            oct1_idx = i
            break

    print(f"Oct 1 idx: {oct1_idx}, Total bars: {n}, Bars from Oct 1: {n - oct1_idx}")
    print(f"Trend at Oct 1: {trend[oct1_idx]}")

    flips = []
    for i in range(oct1_idx, n):
        if trend[i] != trend[i-1]:
            dt = datetime.fromtimestamp(times[i], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            flips.append((i, times[i], dt, trend[i], closes[i]))

    print(f"Total SuperTrend flips from Oct 1: {len(flips)}")
    for f in flips[:10]:
        print(f"  Flip at bar {f[0]} ({f[2]}): to {'BULL (+1)' if f[3]==1 else 'BEAR (-1)'} at {f[4]}")

if __name__ == '__main__':
    test_st()
