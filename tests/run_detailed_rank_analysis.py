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

def run_detailed_analysis(engine_name, pbBuySig, pbSellSig):
    waves = []
    curr_dir = None
    curr_start = None
    curr_pullbacks = []

    for i in range(1, n):
        if times[i] < OCT_1_TS:
            continue
        if trend[i] != trend[i-1]:
            if curr_dir is not None:
                waves.append({
                    'dir': curr_dir,
                    'start_i': curr_start,
                    'end_i': i,
                    'bars': i - curr_start,
                    'pullbacks': curr_pullbacks
                })
            curr_dir = trend[i]
            curr_start = i
            curr_pullbacks = []
        else:
            if curr_dir == 1 and pbBuySig[i]:
                curr_pullbacks.append({'bar': i, 'price': closes[i], 'time': times[i], 'dir': 1})
            elif curr_dir == -1 and pbSellSig[i]:
                curr_pullbacks.append({'bar': i, 'price': closes[i], 'time': times[i], 'dir': -1})

    if curr_dir is not None:
        waves.append({
            'dir': curr_dir,
            'start_i': curr_start,
            'end_i': n - 1,
            'bars': (n - 1) - curr_start,
            'pullbacks': curr_pullbacks
        })

    pb_counts = [len(w['pullbacks']) for w in waves]
    total_waves = len(waves)
    total_pb = sum(pb_counts)

    print(f"\n==========================================================================")
    print(f"DETAILED REPORT: {engine_name}")
    print(f"Total Trend Waves: {total_waves} | Total Pullbacks: {total_pb}")
    print(f"==========================================================================")

    # Progression funnel
    w_0 = sum(1 for c in pb_counts if c == 0)
    w_1p = sum(1 for c in pb_counts if c >= 1)
    w_2p = sum(1 for c in pb_counts if c >= 2)
    w_3p = sum(1 for c in pb_counts if c >= 3)
    w_4p = sum(1 for c in pb_counts if c >= 4)

    print("PROGRESSION FUNNEL:")
    print(f"  Waves with >= 1 Pullback: {w_1p} / {total_waves} ({w_1p/total_waves*100:.1f}%)")
    print(f"  Waves with >= 2 Pullbacks: {w_2p} / {total_waves} ({w_2p/total_waves*100:.1f}%) [Progression from #1: {w_2p/w_1p*100:.1f}%]")
    print(f"  Waves with >= 3 Pullbacks: {w_3p} / {total_waves} ({w_3p/total_waves*100:.1f}%) [Progression from #2: {w_3p/w_2p*100:.1f}%]")
    print(f"  Waves with >= 4 Pullbacks: {w_4p} / {total_waves} ({w_4p/total_waves*100:.1f}%) [Progression from #3: {w_4p/w_3p*100:.1f}%]")

    rank_groups = [
        ("1st Pullback Only", [1]),
        ("2nd Pullback Only", [2]),
        ("3rd Pullback Only", [3]),
        ("4th Pullback Only (Strict)", [4]),
        ("4th+ Pullbacks (All)", list(range(4, 50))),
        ("All Pullbacks Combined", list(range(1, 50)))
    ]

    results_table = []

    for label, rank_list in rank_groups:
        trades = []
        for w in waves:
            pbs = w['pullbacks']
            exit_price = closes[w['end_i']]
            for r in rank_list:
                if len(pbs) >= r:
                    pb = pbs[r - 1]
                    pnl_pts = (exit_price - pb['price']) if pb['dir'] == 1 else (pb['price'] - exit_price)
                    pnl_usd = pnl_pts * 10.0
                    bars_held = w['end_i'] - pb['bar']
                    
                    # Intrabar MFE and MAE
                    # For long: MAE is min(lows) - entry_price, MFE is max(highs) - entry_price
                    # For short: MAE is entry_price - max(highs), MFE is entry_price - min(lows)
                    trade_lows = lows[pb['bar'] : w['end_i'] + 1]
                    trade_highs = highs[pb['bar'] : w['end_i'] + 1]
                    if pb['dir'] == 1:
                        mae_pts = min(trade_lows) - pb['price']
                        mfe_pts = max(trade_highs) - pb['price']
                    else:
                        mae_pts = pb['price'] - max(trade_highs)
                        mfe_pts = pb['price'] - min(trade_lows)

                    trades.append({
                        'pnl_usd': pnl_usd,
                        'bars_held': bars_held,
                        'dir': pb['dir'],
                        'mae_usd': mae_pts * 10.0,
                        'mfe_usd': mfe_pts * 10.0,
                        'entry_time': pb['time'],
                        'entry_bar': pb['bar'],
                        'exit_bar': w['end_i']
                    })

        cnt = len(trades)
        if cnt == 0:
            continue

        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] < 0]
        evens = [t for t in trades if t['pnl_usd'] == 0]

        win_cnt = len(wins)
        loss_cnt = len(losses)
        even_cnt = len(evens)

        win_rate = win_cnt / cnt * 100.0
        gross_pnl = sum(t['pnl_usd'] for t in trades)
        fee_cost = cnt * 4.0
        net_pnl = gross_pnl - fee_cost

        gross_wins = sum(t['pnl_usd'] for t in wins)
        gross_losses = abs(sum(t['pnl_usd'] for t in losses))
        pf = (gross_wins / gross_losses) if gross_losses > 0 else 999.0

        avg_win = (gross_wins / win_cnt) if win_cnt > 0 else 0.0
        avg_loss = (gross_losses / loss_cnt) if loss_cnt > 0 else 0.0
        payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else 999.0

        ev_gross = gross_pnl / cnt
        ev_net = net_pnl / cnt

        avg_bars = sum(t['bars_held'] for t in trades) / cnt
        avg_hours = avg_bars * 5.0 / 60.0

        # Closed-trade Drawdown (Gross & Net)
        cum_gross = 0.0
        peak_gross = 0.0
        dd_gross = 0.0
        cum_net = 0.0
        peak_net = 0.0
        dd_net = 0.0
        for t in trades:
            cum_gross += t['pnl_usd']
            if cum_gross > peak_gross: peak_gross = cum_gross
            if peak_gross - cum_gross > dd_gross: dd_gross = peak_gross - cum_gross

            cum_net += (t['pnl_usd'] - 4.0)
            if cum_net > peak_net: peak_net = cum_net
            if peak_net - cum_net > dd_net: dd_net = peak_net - cum_net

        # Long vs Short breakdown
        long_trades = [t for t in trades if t['dir'] == 1]
        short_trades = [t for t in trades if t['dir'] == -1]

        long_cnt = len(long_trades)
        long_wins = len([t for t in long_trades if t['pnl_usd'] > 0])
        long_wr = (long_wins / long_cnt * 100) if long_cnt > 0 else 0.0
        long_net = sum(t['pnl_usd'] for t in long_trades) - long_cnt * 4.0

        short_cnt = len(short_trades)
        short_wins = len([t for t in short_trades if t['pnl_usd'] > 0])
        short_wr = (short_wins / short_cnt * 100) if short_cnt > 0 else 0.0
        short_net = sum(t['pnl_usd'] for t in short_trades) - short_cnt * 4.0

        res_dict = {
            'label': label,
            'trades': cnt,
            'win_cnt': win_cnt,
            'loss_cnt': loss_cnt,
            'even_cnt': even_cnt,
            'win_rate': win_rate,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'pf': pf,
            'max_dd_gross': dd_gross,
            'max_dd_net': dd_net,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'payoff_ratio': payoff_ratio,
            'ev_gross': ev_gross,
            'ev_net': ev_net,
            'avg_bars': avg_bars,
            'avg_hours': avg_hours,
            'long_cnt': long_cnt,
            'long_wr': long_wr,
            'long_net': long_net,
            'short_cnt': short_cnt,
            'short_wr': short_wr,
            'short_net': short_net
        }
        results_table.append(res_dict)

    return results_table

srsi_results = run_detailed_analysis("1. STOCH RSI (%K x %D in <=30 / >=70)", buy_srsi, sell_srsi)
atr_results = run_detailed_analysis("2. ATR WAVE RETRACEMENT (1.25x ATR)", buy_atr, sell_atr)

with open('tests/pullback_rank_detailed_results.json', 'w') as f:
    json.dump({'stoch_rsi': srsi_results, 'atr_wave': atr_results}, f, indent=2)

print("\nSaved detailed results to tests/pullback_rank_detailed_results.json")
