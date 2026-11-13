import json
from optimize_mes1_5m_supertrend import run_supertrend_sim

with open('data_mes1_5m.json') as f:
    bars = json.load(f)

def inspect_trades(atr_p, mult, method):
    # Modified run to return trades
    pass

# Let's inspect long vs short in a quick script
from datetime import datetime, timezone

def analyze_trade_detail(atr_period, multiplier, atr_method):
    n = len(bars)
    tr = [0.0] * n
    tr[0] = bars[0][2] - bars[0][3]
    for i in range(1, n):
        tr[i] = max(bars[i][2] - bars[i][3], abs(bars[i][2] - bars[i-1][4]), abs(bars[i][3] - bars[i-1][4]))

    atr = [0.0] * n
    if atr_method == "SMA":
        for i in range(n):
            atr[i] = sum(tr[max(0, i - atr_period + 1):i + 1]) / atr_period if i >= atr_period - 1 else 0.0
    else:
        atr[atr_period - 1] = sum(tr[:atr_period]) / atr_period
        for i in range(atr_period, n):
            atr[i] = (atr[i - 1] * (atr_period - 1) + tr[i]) / atr_period

    up = [0.0] * n
    dn = [0.0] * n
    trend = [1] * n
    start_idx = atr_period - 1
    for i in range(start_idx, n):
        hl2 = (bars[i][2] + bars[i][3]) / 2.0
        b_up = hl2 - (multiplier * atr[i])
        b_dn = hl2 + (multiplier * atr[i])
        if i == start_idx:
            up[i] = b_up
            dn[i] = b_dn
            trend[i] = 1
            continue
        up[i] = max(b_up, up[i - 1]) if bars[i - 1][4] > up[i - 1] else b_up
        dn[i] = min(b_dn, dn[i - 1]) if bars[i - 1][4] < dn[i - 1] else b_dn
        if trend[i - 1] == -1 and bars[i][4] > dn[i - 1]:
            trend[i] = 1
        elif trend[i - 1] == 1 and bars[i][4] < up[i - 1]:
            trend[i] = -1
        else:
            trend[i] = trend[i - 1]

    trades = []
    curr = None
    for i in range(start_idx + 1, n - 1):
        if (trend[i] == 1 and trend[i-1] == -1) or (trend[i] == -1 and trend[i-1] == 1):
            bar = i + 1
            if curr:
                curr['exit_price'] = bars[bar][1]
                pts = (curr['exit_price'] - curr['entry_price']) if curr['dir'] == 'LONG' else (curr['entry_price'] - curr['exit_price'])
                curr['pnl_pts'] = pts
                curr['pnl_net'] = pts * 5.0 - 3.90
                trades.append(curr)
            curr = {'dir': 'LONG' if trend[i] == 1 else 'SHORT', 'entry_price': bars[bar][1], 'entry_time': bars[bar][0]}
    if curr:
        curr['exit_price'] = bars[-1][4]
        pts = (curr['exit_price'] - curr['entry_price']) if curr['dir'] == 'LONG' else (curr['entry_price'] - curr['exit_price'])
        curr['pnl_pts'] = pts
        curr['pnl_net'] = pts * 5.0 - 3.90
        trades.append(curr)

    longs = [t for t in trades if t['dir'] == 'LONG']
    shorts = [t for t in trades if t['dir'] == 'SHORT']
    print(f"[{atr_method} {atr_period}, {multiplier}] Total Trades: {len(trades)}")
    print(f"  LONG:  {len(longs)} trades | Net: ${sum(t['pnl_net'] for t in longs):.2f} | Win%: {len([t for t in longs if t['pnl_net'] > 0])/len(longs)*100:.1f}%")
    print(f"  SHORT: {len(shorts)} trades | Net: ${sum(t['pnl_net'] for t in shorts):.2f} | Win%: {len([t for t in shorts if t['pnl_net'] > 0])/len(shorts)*100:.1f}%")

analyze_trade_detail(12, 3.0, "SMA")
analyze_trade_detail(8, 3.5, "RMA (Wilder)")
analyze_trade_detail(10, 3.0, "RMA (Wilder)")
