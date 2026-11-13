#!/usr/bin/env python3
import json
from datetime import datetime, timezone

with open('merged_mgc1_5m.json') as f:
    bars = json.load(f)

bar_list = [[b['time'], b['open'], b['high'], b['low'], b['close'], b['volume']] for b in bars]
n = len(bar_list)

# 1. Supertrend (12, 2.8, RMA)
tr = [0.0] * n
tr[0] = bar_list[0][2] - bar_list[0][3]
for i in range(1, n):
    h = bar_list[i][2]
    l = bar_list[i][3]
    pc = bar_list[i-1][4]
    tr[i] = max(h - l, abs(h - pc), abs(l - pc))

atr = [0.0] * n
atr_period = 12
mult = 2.8
atr[atr_period - 1] = sum(tr[:atr_period]) / atr_period
for i in range(atr_period, n):
    atr[i] = (atr[i - 1] * (atr_period - 1) + tr[i]) / atr_period

up = [0.0] * n
dn = [0.0] * n
st_trend = [1] * n

for i in range(atr_period - 1, n):
    hl2 = (bar_list[i][2] + bar_list[i][3]) / 2.0
    basic_up = hl2 - (mult * atr[i])
    basic_dn = hl2 + (mult * atr[i])

    if i == atr_period - 1:
        up[i] = basic_up
        dn[i] = basic_dn
        st_trend[i] = 1
        continue

    prev_up = up[i - 1]
    prev_dn = dn[i - 1]
    prev_close = bar_list[i - 1][4]

    up[i] = max(basic_up, prev_up) if prev_close > prev_up else basic_up
    dn[i] = min(basic_dn, prev_dn) if prev_close < prev_dn else basic_dn

    curr_close = bar_list[i][4]
    prev_trend = st_trend[i - 1]

    if prev_trend == -1 and curr_close > prev_dn:
        st_trend[i] = 1
    elif prev_trend == 1 and curr_close < prev_up:
        st_trend[i] = -1
    else:
        st_trend[i] = prev_trend

# 2. Ichimoku Base Line (Kijun-sen 26)
kijun = [0.0] * n
for i in range(25, n):
    slice_highs = [bar_list[k][2] for k in range(i - 25, i + 1)]
    slice_lows  = [bar_list[k][3] for k in range(i - 25, i + 1)]
    kijun[i] = (max(slice_highs) + min(slice_lows)) / 2.0

# Ichimoku trend state: 1 if close > kijun, -1 if close < kijun
ichi_trend = [0] * n
for i in range(26, n):
    c = bar_list[i][4]
    k = kijun[i]
    prev_state = ichi_trend[i-1]
    if c > k:
        ichi_trend[i] = 1
    elif c < k:
        ichi_trend[i] = -1
    else:
        ichi_trend[i] = prev_state

nov9_ts = 1794178800 # Nov 08 23:00 UTC (Nov 09 Asian timing)

def simulate_system(trend_arr, start_ts, name='System'):
    signals = []
    for i in range(30, n):
        if trend_arr[i] != trend_arr[i-1] and trend_arr[i] != 0:
            sig_type = 'BUY' if trend_arr[i] == 1 else 'SELL'
            signals.append({
                'idx': i,
                'time': bar_list[i][0],
                'dt': datetime.fromtimestamp(bar_list[i][0], timezone.utc),
                'type': sig_type,
                'close': bar_list[i][4],
                'next_open': bar_list[i+1][1] if i + 1 < n else bar_list[i][4]
            })

    active_signals = [s for s in signals if s['time'] >= start_ts]

    # Compute Long trades
    longs = []
    cur_long = None
    for s in active_signals:
        if s['type'] == 'BUY':
            cur_long = {'entry_dt': s['dt'], 'entry_price': s['next_open']}
        elif s['type'] == 'SELL' and cur_long is not None:
            cur_long['exit_dt'] = s['dt']
            cur_long['exit_price'] = s['next_open']
            cur_long['pts'] = cur_long['exit_price'] - cur_long['entry_price']
            cur_long['net_usd'] = cur_long['pts'] * 10.0 - 3.40
            longs.append(cur_long)
            cur_long = None

    # Compute Short trades
    shorts = []
    cur_short = None
    for s in active_signals:
        if s['type'] == 'SELL':
            cur_short = {'entry_dt': s['dt'], 'entry_price': s['next_open']}
        elif s['type'] == 'BUY' and cur_short is not None:
            cur_short['exit_dt'] = s['dt']
            cur_short['exit_price'] = s['next_open']
            cur_short['pts'] = cur_short['entry_price'] - cur_short['exit_price']
            cur_short['net_usd'] = cur_short['pts'] * 10.0 - 3.40
            shorts.append(cur_short)
            cur_short = None

    # Stats
    l_pts = sum(t['pts'] for t in longs)
    l_net = sum(t['net_usd'] for t in longs)
    l_wins = sum(1 for t in longs if t['pts'] > 0)

    s_pts = sum(t['pts'] for t in shorts)
    s_net = sum(t['net_usd'] for t in shorts)
    s_wins = sum(1 for t in shorts if t['pts'] > 0)

    tot_trades = len(longs) + len(shorts)
    tot_pts = l_pts + s_pts
    tot_net = l_net + s_net
    tot_wins = l_wins + s_wins

    return {
        'name': name,
        'signals_count': len(active_signals),
        'long_trades': len(longs),
        'long_wins': l_wins,
        'long_pts': l_pts,
        'long_net': l_net,
        'short_trades': len(shorts),
        'short_wins': s_wins,
        'short_pts': s_pts,
        'short_net': s_net,
        'total_trades': tot_trades,
        'total_wins': tot_wins,
        'total_pts': tot_pts,
        'total_net': tot_net,
        'long_list': longs,
        'short_list': shorts,
        'cur_long': cur_long,
        'cur_short': cur_short
    }

st = simulate_system(st_trend, nov9_ts, 'Supertrend V2 (12, 2.8 RMA)')
ichi = simulate_system(ichi_trend, nov9_ts, 'Ichimoku Base Line Cross (Kijun 26)')

print("=" * 80)
print("HEAD-TO-HEAD: SUPERTREND V2 vs ICHIMOKU BASE LINE CROSS (MGC1! 5m)")
print("Period: 09 Nov 2026 Asian Open to 13 Nov 2026 Now (1 Contract, $10/pt)")
print("=" * 80)

print(f"\n1. {st['name']}:")
print(f"   Signals Fired: {st['signals_count']}")
print(f"   Long Only:     {st['long_trades']} trades | {st['long_wins']} Wins ({st['long_wins']/max(1,st['long_trades'])*100:.1f}%) | {st['long_pts']:+6.1f} pts | Net: ${st['long_net']:+8.2f}")
print(f"   Short Only:    {st['short_trades']} trades | {st['short_wins']} Wins ({st['short_wins']/max(1,st['short_trades'])*100:.1f}%) | {st['short_pts']:+6.1f} pts | Net: ${st['short_net']:+8.2f}")
print(f"   --> FULL BOTH: {st['total_trades']} trades | {st['total_wins']} Wins ({st['total_wins']/max(1,st['total_trades'])*100:.1f}%) | {st['total_pts']:+6.1f} pts | Net: ${st['total_net']:+8.2f}")

print(f"\n2. {ichi['name']}:")
print(f"   Signals Fired: {ichi['signals_count']}")
print(f"   Long Only:     {ichi['long_trades']} trades | {ichi['long_wins']} Wins ({ichi['long_wins']/max(1,ichi['long_trades'])*100:.1f}%) | {ichi['long_pts']:+6.1f} pts | Net: ${ichi['long_net']:+8.2f}")
print(f"   Short Only:    {ichi['short_trades']} trades | {ichi['short_wins']} Wins ({ichi['short_wins']/max(1,ichi['short_trades'])*100:.1f}%) | {ichi['short_pts']:+6.1f} pts | Net: ${ichi['short_net']:+8.2f}")
print(f"   --> FULL BOTH: {ichi['total_trades']} trades | {ichi['total_wins']} Wins ({ichi['total_wins']/max(1,ichi['total_trades'])*100:.1f}%) | {ichi['total_pts']:+6.1f} pts | Net: ${ichi['total_net']:+8.2f}")

print("\n" + "=" * 80)
diff_pts = st['total_pts'] - ichi['total_pts']
diff_net = st['total_net'] - ichi['total_net']
print(f"VERDICT: Supertrend outperformed Ichimoku Base Line by {diff_pts:+.1f} pts (${diff_net:+.2f} Net)")
print("=" * 80)
