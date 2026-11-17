#!/usr/bin/env python3
import json
import math
import numpy as np
from datetime import datetime, timezone

def run_comprehensive_analysis():
    with open('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests/mgc1_5m_all.json', 'r') as f:
        bars_raw = json.load(f)

    n = len(bars_raw)
    times  = [b[0] for b in bars_raw]
    opens  = [b[1] for b in bars_raw]
    highs  = [b[2] for b in bars_raw]
    lows   = [b[3] for b in bars_raw]
    closes = [b[4] for b in bars_raw]

    OCT_1_TS = 1790812800 # 2026-10-01 00:00:00 UTC
    oct1_idx = next(i for i, t in enumerate(times) if t >= OCT_1_TS)

    # 1. Exact Pine RMA & SMA
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

    # Signal generator
    def run_engine(engine_mode="SRSI_CROSS", pb_retrace_atr=1.25, srsi_os=30.0, srsi_ob=70.0, req_candle=True):
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
        events    = {} # bar_index -> dict

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
                # Retracement depth from the preceding impulse peak
                peak_p = waveHigh
                trough_p = min(lows[waveHighBar : i + 1]) if i >= waveHighBar else trough2
                depth_pts = peak_p - trough_p
                depth_atr = depth_pts / atr14[i] if atr14[i] > 0 else 0.0
                events[i] = {
                    'bar': i,
                    'time': times[i],
                    'type': 'BUY',
                    'close': closes[i],
                    'peak_or_trough_ref': peak_p,
                    'extreme_pb_price': trough_p,
                    'depth_pts': depth_pts,
                    'depth_usd': depth_pts * 10.0,
                    'depth_atr': depth_atr,
                    'atr14': atr14[i]
                }
                lastRefLow = trough2
                waveHigh = highs[i]
                waveHighBar = i

            if rawSell:
                pbSellSig[i] = True
                srsiBearArmed = False
                trough_p = waveLow
                peak_p = max(highs[waveLowBar : i + 1]) if i >= waveLowBar else peak2
                depth_pts = peak_p - trough_p
                depth_atr = depth_pts / atr14[i] if atr14[i] > 0 else 0.0
                events[i] = {
                    'bar': i,
                    'time': times[i],
                    'type': 'SELL',
                    'close': closes[i],
                    'peak_or_trough_ref': trough_p,
                    'extreme_pb_price': peak_p,
                    'depth_pts': depth_pts,
                    'depth_usd': depth_pts * 10.0,
                    'depth_atr': depth_atr,
                    'atr14': atr14[i]
                }
                lastRefHigh = peak2
                waveLow = lows[i]
                waveLowBar = i

        return pbBuySig, pbSellSig, events

    # Get signals for both engines
    srsi_buy, srsi_sell, srsi_events = run_engine("SRSI_CROSS")
    atr_buy, atr_sell, atr_events = run_engine("ATR_WAVE")

    # Segment Trend Waves
    # Let's segment both:
    # Segment 1: Starting at the first flip on/after OCT_1_TS (as in audit_pullback_frequency_and_rank.py)
    # Segment 2: Starting at OCT_1_TS bar directly (including the ongoing wave that started before Oct 1)
    
    def extract_waves(start_at_first_flip=True):
        waves = []
        curr_dir = None
        curr_start = None
        curr_srsi_pb = []
        curr_atr_pb = []
        wave_high = -1e9
        wave_low = 1e9

        start_bar = oct1_idx
        if start_at_first_flip:
            # find first flip >= oct1_idx
            for i in range(oct1_idx, n):
                if trend[i] != trend[i-1]:
                    start_bar = i
                    break

        for i in range(start_bar, n):
            # check flip
            is_flip = (trend[i] != trend[i-1]) if i > 0 else False
            if is_flip and i > start_bar:
                # Close previous wave
                waves.append({
                    'wave_id': len(waves) + 1,
                    'dir': curr_dir,
                    'type': 'BULL' if curr_dir == 1 else 'BEAR',
                    'start_i': curr_start,
                    'end_i': i,
                    'start_time': times[curr_start],
                    'end_time': times[i],
                    'start_price': closes[curr_start],
                    'end_price': closes[i],
                    'wave_high': wave_high,
                    'wave_low': wave_low,
                    'bars': i - curr_start,
                    'duration_hours': (i - curr_start) * 5.0 / 60.0,
                    'srsi_pullbacks': curr_srsi_pb,
                    'atr_pullbacks': curr_atr_pb
                })
                curr_dir = trend[i]
                curr_start = i
                curr_srsi_pb = []
                curr_atr_pb = []
                wave_high = highs[i]
                wave_low = lows[i]
            else:
                if curr_dir is None:
                    curr_dir = trend[i]
                    curr_start = i
                    wave_high = highs[i]
                    wave_low = lows[i]
                else:
                    wave_high = max(wave_high, highs[i])
                    wave_low = min(wave_low, lows[i])

                if curr_dir == 1:
                    if srsi_buy[i]:
                        curr_srsi_pb.append(srsi_events[i])
                    if atr_buy[i]:
                        curr_atr_pb.append(atr_events[i])
                elif curr_dir == -1:
                    if srsi_sell[i]:
                        curr_srsi_pb.append(srsi_events[i])
                    if atr_sell[i]:
                        curr_atr_pb.append(atr_events[i])

        # Final wave up to end of dataset
        if curr_dir is not None:
            waves.append({
                'wave_id': len(waves) + 1,
                'dir': curr_dir,
                'type': 'BULL' if curr_dir == 1 else 'BEAR',
                'start_i': curr_start,
                'end_i': n - 1,
                'start_time': times[curr_start],
                'end_time': times[n - 1],
                'start_price': closes[curr_start],
                'end_price': closes[n - 1],
                'wave_high': wave_high,
                'wave_low': wave_low,
                'bars': (n - 1) - curr_start,
                'duration_hours': ((n - 1) - curr_start) * 5.0 / 60.0,
                'srsi_pullbacks': curr_srsi_pb,
                'atr_pullbacks': curr_atr_pb
            })
        return waves

    waves_flip = extract_waves(start_at_first_flip=True)
    waves_all = extract_waves(start_at_first_flip=False)

    def print_analysis(title, waves):
        print("=" * 80)
        print(f"ANALYSIS: {title}")
        print("=" * 80)
        total_waves = len(waves)
        bull_waves = [w for w in waves if w['dir'] == 1]
        bear_waves = [w for w in waves if w['dir'] == -1]
        total_bars = sum(w['bars'] for w in waves)
        avg_wave_bars = total_bars / total_waves if total_waves else 0
        avg_wave_hours = avg_wave_bars * 5.0 / 60.0

        print(f"Total Trend Waves: {total_waves} (Bullish: {len(bull_waves)}, Bearish: {len(bear_waves)})")
        print(f"Total Bars in Waves: {total_bars} (Avg duration: {avg_wave_bars:.1f} bars / {avg_wave_hours:.2f} hours)")

        for engine_key, engine_name in [('srsi_pullbacks', 'Stoch RSI Pullback Engine (3, 3, 14, 14, OS<=30 / OB>=70)'),
                                        ('atr_pullbacks', 'ATR Wave Retracement Pullback Engine (1.25x ATR14)')]:
            print("\n" + "-" * 75)
            print(f"ENGINE: {engine_name}")
            print("-" * 75)

            counts = [len(w[engine_key]) for w in waves]
            bull_counts = [len(w[engine_key]) for w in bull_waves]
            bear_counts = [len(w[engine_key]) for w in bear_waves]

            total_pb = sum(counts)
            avg_pb = np.mean(counts)
            max_pb = max(counts) if counts else 0
            min_pb = min(counts) if counts else 0

            print(f"Total Pullbacks: {total_pb} (Bullish: {sum(bull_counts)}, Bearish: {sum(bear_counts)})")
            print(f"Average Pullbacks per Wave: {avg_pb:.2f} (Bullish: {np.mean(bull_counts):.2f}, Bearish: {np.mean(bear_counts):.2f})")
            print(f"Highest Number of Pullbacks (Max): {max_pb}")
            print(f"Lowest Number of Pullbacks (Min): {min_pb}")

            # Distribution Table
            print("\nDISTRIBUTION TABLE (Exact Breakdown):")
            print(f"{'Pullback Count':20s} | {'Waves Count':12s} | {'% of Waves':12s} | {'Bull Waves':12s} | {'Bear Waves':12s}")
            print("-" * 75)
            for k in range(max_pb + 1):
                cnt = sum(1 for c in counts if c == k)
                pct = cnt / total_waves * 100.0 if total_waves else 0.0
                b_cnt = sum(1 for c in bull_counts if c == k)
                r_cnt = sum(1 for c in bear_counts if c == k)
                print(f"Exactly {k:2d} pullbacks      | {cnt:12d} | {pct:11.2f}% | {b_cnt:12d} | {r_cnt:12d}")

            # Aggregated 0, 1, 2, 3, 4+
            c0 = sum(1 for c in counts if c == 0)
            c1 = sum(1 for c in counts if c == 1)
            c2 = sum(1 for c in counts if c == 2)
            c3 = sum(1 for c in counts if c == 3)
            c4p = sum(1 for c in counts if c >= 4)
            print("-" * 75)
            print("REQUIRED SUMMARY DISTRIBUTION TABLE (0, 1, 2, 3, 4+):")
            print(f"• 0 pullbacks:            {c0:3d} waves ({c0/total_waves*100.0:5.2f}%)")
            print(f"• Exactly 1 pullback:     {c1:3d} waves ({c1/total_waves*100.0:5.2f}%)")
            print(f"• Exactly 2 pullbacks:    {c2:3d} waves ({c2/total_waves*100.0:5.2f}%)")
            print(f"• Exactly 3 pullbacks:    {c3:3d} waves ({c3/total_waves*100.0:5.2f}%)")
            print(f"• 4 or more pullbacks:    {c4p:3d} waves ({c4p/total_waves*100.0:5.2f}%)")
            print(f"Total Waves:              {total_waves:3d} waves (100.00%)")

            # Pullback depth statistics
            all_pb_events = []
            for w in waves:
                all_pb_events.extend(w[engine_key])

            if all_pb_events:
                pts = [e['depth_pts'] for e in all_pb_events]
                usds = [e['depth_usd'] for e in all_pb_events]
                atrs = [e['depth_atr'] for e in all_pb_events]

                avg_pts = np.mean(pts)
                max_pts = np.max(pts)
                min_pts = np.min(pts)

                avg_usd = np.mean(usds)
                max_usd = np.max(usds)
                min_usd = np.min(usds)

                avg_atr = np.mean(atrs)
                max_atr = np.max(atrs)
                min_atr = np.min(atrs)

                print("\nPULLBACK DEPTH / MAGNITUDE STATISTICS (At Signal Confirmation):")
                print(f"• Average Pullback Magnitude: {avg_pts:.2f} points (${avg_usd:.2f}) | {avg_atr:.2f}x ATR14")
                print(f"• Highest Pullback Magnitude: {max_pts:.2f} points (${max_usd:.2f}) | {max_atr:.2f}x ATR14")
                print(f"• Lowest Pullback Magnitude:  {min_pts:.2f} points (${min_usd:.2f}) | {min_atr:.2f}x ATR14")

                # Breakdown by Bullish vs Bearish pullbacks
                bull_pbs = [e for e in all_pb_events if e['type'] == 'BUY']
                bear_pbs = [e for e in all_pb_events if e['type'] == 'SELL']
                if bull_pbs:
                    b_pts = [e['depth_pts'] for e in bull_pbs]
                    b_atrs = [e['depth_atr'] for e in bull_pbs]
                    print(f"  - Bullish Pullbacks ({len(bull_pbs)}): Avg {np.mean(b_pts):.2f} pts (${np.mean(b_pts)*10:.2f}) | {np.mean(b_atrs):.2f}x ATR | Max {np.max(b_pts):.2f} pts | Min {np.min(b_pts):.2f} pts")
                if bear_pbs:
                    r_pts = [e['depth_pts'] for e in bear_pbs]
                    r_atrs = [e['depth_atr'] for e in bear_pbs]
                    print(f"  - Bearish Pullbacks ({len(bear_pbs)}): Avg {np.mean(r_pts):.2f} pts (${np.mean(r_pts)*10:.2f}) | {np.mean(r_atrs):.2f}x ATR | Max {np.max(r_pts):.2f} pts | Min {np.min(r_pts):.2f} pts")

    print("\n" + "#" * 80)
    print("RUNNING WITH METHOD A: Waves starting at First SuperTrend Flip on/after Oct 1")
    print("#" * 80)
    print_analysis("Method A (First Flip on/after Oct 1)", waves_flip)

    print("\n" + "#" * 80)
    print("RUNNING WITH METHOD B: All Waves from Oct 1 (including initial active wave)")
    print("#" * 80)
    print_analysis("Method B (All Bars >= Oct 1)", waves_all)

if __name__ == '__main__':
    run_comprehensive_analysis()
