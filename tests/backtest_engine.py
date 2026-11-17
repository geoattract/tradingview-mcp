#!/usr/bin/env python3
import json
import math
from datetime import datetime, timezone

def run_analysis():
    with open('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests/mgc1_5m_all.json', 'r') as f:
        bars_raw = json.load(f)
    
    # Each bar is [time, open, high, low, close, volume]
    n = len(bars_raw)
    times = [b[0] for b in bars_raw]
    opens = [b[1] for b in bars_raw]
    highs = [b[2] for b in bars_raw]
    lows = [b[3] for b in bars_raw]
    closes = [b[4] for b in bars_raw]
    volumes = [b[5] for b in bars_raw]

    # Timestamp for 2026-10-01 00:00:00 UTC (Asian session start)
    OCT_1_TS = 1790812800

    # 1. TR and ATR helpers (RMA / Wilder's smoothing)
    tr = [0.0] * n
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)

    def calc_rma(src, length):
        out = [0.0] * n
        alpha = 1.0 / length
        sum_val = 0.0
        for i in range(n):
            if i < length:
                sum_val += src[i]
                out[i] = sum_val / (i + 1)
            else:
                out[i] = alpha * src[i] + (1.0 - alpha) * out[i-1]
        return out

    # Precalculate ATRs
    atr14 = calc_rma(tr, 14)
    atr100 = calc_rma(tr, 100)
    atr80_rma = calc_rma(tr, 80)

    # -------------------------------------------------------------
    # 2. SUPERTREND V2 CALCULATOR
    # -------------------------------------------------------------
    def summarize_trades(trades, title):
        if not trades:
            return {'title': title, 'total_trades': 0, 'net_pnl_usd': 0.0}

        wins = [t for t in trades if t['pnl_pts'] > 0]
        losses = [t for t in trades if t['pnl_pts'] <= 0]

        total_pts = sum(t['pnl_pts'] for t in trades)
        gross_win_pts = sum(t['pnl_pts'] for t in wins)
        gross_loss_pts = sum(abs(t['pnl_pts']) for t in losses)

        pf = (gross_win_pts / gross_loss_pts) if gross_loss_pts > 0 else 999.0
        win_rate = (len(wins) / len(trades) * 100) if trades else 0.0

        cum = 0.0
        peak = 0.0
        max_dd_usd = 0.0
        for t in trades:
            cum += t['pnl_usd']
            if cum > peak:
                peak = cum
            dd = peak - cum
            if dd > max_dd_usd:
                max_dd_usd = dd

        avg_bars = sum(t['bars_held'] for t in trades) / len(trades)

        return {
            'title': title,
            'total_trades': len(trades),
            'win_rate': round(win_rate, 1),
            'total_pnl_pts': round(total_pts, 2),
            'total_pnl_usd': round(total_pts * 10.0, 2),
            'profit_factor': round(pf, 2),
            'max_drawdown_usd': round(max_dd_usd, 2),
            'avg_trade_bars': round(avg_bars, 1),
            'avg_trade_hours': round(avg_bars * 5 / 60.0, 1),
            'gross_win_usd': round(gross_win_pts * 10.0, 2),
            'gross_loss_usd': round(gross_loss_pts * 10.0, 2)
        }

    def backtest_supertrend(atr_len=80, mult=1.7, atr_series=atr80_rma):
        trend = [1] * n
        up = [0.0] * n
        dn = [0.0] * n
        
        for i in range(1, n):
            hl2 = (highs[i] + lows[i]) / 2.0
            basic_up = hl2 - mult * atr_series[i]
            basic_dn = hl2 + mult * atr_series[i]

            up1 = up[i-1]
            if closes[i-1] > up1:
                up[i] = max(basic_up, up1)
            else:
                up[i] = basic_up

            dn1 = dn[i-1]
            if closes[i-1] < dn1:
                dn[i] = min(basic_dn, dn1)
            else:
                dn[i] = basic_dn

            prev_trend = trend[i-1]
            if prev_trend == -1 and closes[i] > dn1:
                trend[i] = 1
            elif prev_trend == 1 and closes[i] < up1:
                trend[i] = -1
            else:
                trend[i] = prev_trend

        trades = []
        pos = 0 # 1 = long, -1 = short
        entry_price = 0.0
        entry_time = 0
        entry_bar = 0

        for i in range(1, n):
            if times[i] < OCT_1_TS:
                if trend[i] == 1 and trend[i-1] == -1:
                    pos = 1
                    entry_price = closes[i]
                    entry_time = times[i]
                    entry_bar = i
                elif trend[i] == -1 and trend[i-1] == 1:
                    pos = -1
                    entry_price = closes[i]
                    entry_time = times[i]
                    entry_bar = i
                continue

            if trend[i] == 1 and trend[i-1] == -1:
                if pos == -1:
                    pnl_pts = entry_price - closes[i]
                    trades.append({
                        'type': 'SHORT',
                        'entry_time': entry_time,
                        'exit_time': times[i],
                        'entry_price': entry_price,
                        'exit_price': closes[i],
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_pts * 10.0,
                        'bars_held': i - entry_bar
                    })
                pos = 1
                entry_price = closes[i]
                entry_time = times[i]
                entry_bar = i
            elif trend[i] == -1 and trend[i-1] == 1:
                if pos == 1:
                    pnl_pts = closes[i] - entry_price
                    trades.append({
                        'type': 'LONG',
                        'entry_time': entry_time,
                        'exit_time': times[i],
                        'entry_price': entry_price,
                        'exit_price': closes[i],
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_pts * 10.0,
                        'bars_held': i - entry_bar
                    })
                pos = -1
                entry_price = closes[i]
                entry_time = times[i]
                entry_bar = i

        if pos != 0:
            last_i = n - 1
            pnl_pts = (closes[last_i] - entry_price) if pos == 1 else (entry_price - closes[last_i])
            trades.append({
                'type': 'LONG' if pos == 1 else 'SHORT',
                'entry_time': entry_time,
                'exit_time': times[last_i],
                'entry_price': entry_price,
                'exit_price': closes[last_i],
                'pnl_pts': pnl_pts,
                'pnl_usd': pnl_pts * 10.0,
                'bars_held': last_i - entry_bar
            })

        return summarize_trades(trades, f"SuperTrend V2 (ATR {atr_len}, Mult {mult})")

    # -------------------------------------------------------------
    # 3. cRSI UNIVERSAL ENGINE
    # -------------------------------------------------------------
    crsi = [50.0] * n
    domcycle_arr = [24] * n
    cyclelen_arr = [12] * n

    up_arr = [0.0] * n
    down_arr = [0.0] * n
    rsi_arr = [50.0] * n

    for i in range(1, n):
        raw_ratio = (atr14[i] / atr100[i]) if (atr100[i] > 0 and atr14[i] > 0) else 1.0
        atr_ratio = max(0.25, min(4.0, raw_ratio))
        raw_dyn = 24.0 / atr_ratio
        domcycle = int(max(12, min(50, round(raw_dyn))))
        domcycle_arr[i] = domcycle
        cyclelen = max(1, domcycle // 2)
        cyclelen_arr[i] = cyclelen

        change = closes[i] - closes[i-1]
        up_change = max(change, 0.0)
        down_change = -min(change, 0.0)

        alpha = 1.0 / cyclelen
        up_arr[i] = alpha * up_change + (1.0 - alpha) * up_arr[i-1]
        down_arr[i] = alpha * down_change + (1.0 - alpha) * down_arr[i-1]

        if up_arr[i] == 0 and down_arr[i] == 0:
            rsi_val = 50.0
        elif down_arr[i] == 0:
            rsi_val = 100.0
        elif up_arr[i] == 0:
            rsi_val = 0.0
        else:
            rsi_val = 100.0 - 100.0 / (1.0 + up_arr[i] / down_arr[i])
        rsi_arr[i] = rsi_val

        torque = 2.0 / (10 + 1)
        lag_idx = max(0, i - 4)
        crsi[i] = torque * (2.0 * rsi_val - rsi_arr[lag_idx]) + (1.0 - torque) * crsi[i-1]

    def backtest_crsi(left=6, right=3, atr_mult=3.0, mode='EXTENSIONS', use_filter=True):
        run_high = None
        run_low = None
        last_peak_price = None
        last_trough_price = None
        last_pivot_dir = 0

        trades = []
        pos = 0
        entry_price = 0.0
        entry_time = 0
        entry_bar = 0

        confirmed_dots = []

        for i in range(left + right, n):
            piv_idx = i - right

            is_piv_h = True
            for l_bar in range(piv_idx - left, piv_idx):
                if highs[l_bar] >= highs[piv_idx]:
                    is_piv_h = False
                    break
            if is_piv_h:
                for r_bar in range(piv_idx + 1, piv_idx + right + 1):
                    if highs[r_bar] > highs[piv_idx]:
                        is_piv_h = False
                        break

            is_piv_l = True
            for l_bar in range(piv_idx - left, piv_idx):
                if lows[l_bar] <= lows[piv_idx]:
                    is_piv_l = False
                    break
            if is_piv_l:
                for r_bar in range(piv_idx + 1, piv_idx + right + 1):
                    if lows[r_bar] < lows[piv_idx]:
                        is_piv_l = False
                        break

            pivH = highs[piv_idx] if is_piv_h else None
            pivL = lows[piv_idx] if is_piv_l else None

            high_since = max(highs[piv_idx : i + 1])
            low_since = min(lows[piv_idx : i + 1])

            if run_high is not None:
                run_high = max(run_high, highs[i])
                run_low = min(run_low, lows[i])

            peak_crsi_ok = True
            trough_crsi_ok = True
            if use_filter:
                dyn_lb = int(max(16, min(50, round(domcycle_arr[i] * 1.5))))
                start_lb = max(0, i - dyn_lb)
                c_slice = crsi[start_lb : i + 1]
                crsi_hi = max(c_slice)
                crsi_lo = min(c_slice)
                span = crsi_hi - crsi_lo
                piv_crsi = crsi[piv_idx]
                rel_pos = (piv_crsi - crsi_lo) / span if span > 0 else 0.5
                peak_crsi_ok = (rel_pos >= 0.50)
                trough_crsi_ok = (rel_pos <= 0.50)

            min_move = atr_mult * atr14[i]
            peak_dist_ok = (run_low is None) or (atr_mult <= 0.0) or (pivH is not None and pivH - run_low >= min_move)
            trough_dist_ok = (run_high is None) or (atr_mult <= 0.0) or (pivL is not None and run_high - pivL >= min_move)

            raw_peak = (pivH is not None) and peak_crsi_ok and peak_dist_ok
            raw_trough = (pivL is not None) and trough_crsi_ok and trough_dist_ok

            peak_confirmed = False
            trough_confirmed = False

            if mode == 'STRICT_ALT':
                if last_pivot_dir == 1:
                    if raw_trough:
                        trough_confirmed = True
                        last_pivot_dir = -1
                        last_trough_price = pivL
                        run_low = pivL
                        run_high = high_since
                elif last_pivot_dir == -1:
                    if raw_peak:
                        peak_confirmed = True
                        last_pivot_dir = 1
                        last_peak_price = pivH
                        run_high = pivH
                        run_low = low_since
                else:
                    if raw_peak and raw_trough:
                        if closes[i] >= opens[i]:
                            peak_confirmed = True
                            last_pivot_dir = 1
                            last_peak_price = pivH
                            run_high = pivH
                            run_low = low_since
                        else:
                            trough_confirmed = True
                            last_pivot_dir = -1
                            last_trough_price = pivL
                            run_low = pivL
                            run_high = high_since
                    elif raw_peak:
                        peak_confirmed = True
                        last_pivot_dir = 1
                        last_peak_price = pivH
                        run_high = pivH
                        run_low = low_since
                    elif raw_trough:
                        trough_confirmed = True
                        last_pivot_dir = -1
                        last_trough_price = pivL
                        run_low = pivL
                        run_high = high_since

            elif mode == 'EXTENSIONS':
                can_ext_peak = (last_pivot_dir == 1) and (last_peak_price is not None and pivH is not None and pivH > last_peak_price)
                can_ext_trough = (last_pivot_dir == -1) and (last_trough_price is not None and pivL is not None and pivL < last_trough_price)

                peak_eligible = raw_peak and (last_pivot_dir != 1 or can_ext_peak)
                trough_eligible = raw_trough and (last_pivot_dir != -1 or can_ext_trough)

                if peak_eligible and trough_eligible:
                    if last_pivot_dir == 1:
                        peak_eligible = False
                    else:
                        trough_eligible = False

                if peak_eligible:
                    peak_confirmed = True
                    last_pivot_dir = 1
                    last_peak_price = pivH
                    run_high = pivH
                    run_low = low_since

                if trough_eligible:
                    trough_confirmed = True
                    last_pivot_dir = -1
                    last_trough_price = pivL
                    run_low = pivL
                    run_high = high_since

            if peak_confirmed:
                confirmed_dots.append({'bar': i, 'time': times[i], 'type': 'PEAK', 'price': pivH, 'piv_bar': piv_idx})
            if trough_confirmed:
                confirmed_dots.append({'bar': i, 'time': times[i], 'type': 'TROUGH', 'price': pivL, 'piv_bar': piv_idx})

            if times[i] < OCT_1_TS:
                if trough_confirmed:
                    pos = 1
                    entry_price = closes[i]
                    entry_time = times[i]
                    entry_bar = i
                elif peak_confirmed:
                    pos = -1
                    entry_price = closes[i]
                    entry_time = times[i]
                    entry_bar = i
                continue

            if trough_confirmed:
                if pos == -1:
                    pnl_pts = entry_price - closes[i]
                    trades.append({
                        'type': 'SHORT',
                        'entry_time': entry_time,
                        'exit_time': times[i],
                        'entry_price': entry_price,
                        'exit_price': closes[i],
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_pts * 10.0,
                        'bars_held': i - entry_bar
                    })
                pos = 1
                entry_price = closes[i]
                entry_time = times[i]
                entry_bar = i

            elif peak_confirmed:
                if pos == 1:
                    pnl_pts = closes[i] - entry_price
                    trades.append({
                        'type': 'LONG',
                        'entry_time': entry_time,
                        'exit_time': times[i],
                        'entry_price': entry_price,
                        'exit_price': closes[i],
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_pts * 10.0,
                        'bars_held': i - entry_bar
                    })
                pos = -1
                entry_price = closes[i]
                entry_time = times[i]
                entry_bar = i

        if pos != 0:
            last_i = n - 1
            pnl_pts = (closes[last_i] - entry_price) if pos == 1 else (entry_price - closes[last_i])
            trades.append({
                'type': 'LONG' if pos == 1 else 'SHORT',
                'entry_time': entry_time,
                'exit_time': times[last_i],
                'entry_price': entry_price,
                'exit_price': closes[last_i],
                'pnl_pts': pnl_pts,
                'pnl_usd': pnl_pts * 10.0,
                'bars_held': last_i - entry_bar
            })

        filter_tag = "crsiFilter=ON" if use_filter else "crsiFilter=OFF"
        title = f"cRSI Univ V5 [{mode}] (L={left}, R={right}, ATR={atr_mult}x, {filter_tag})"
        res = summarize_trades(trades, title)
        res['total_dots'] = len([d for d in confirmed_dots if d['time'] >= OCT_1_TS])
        return res

    # -------------------------------------------------------------
    # 4. EMPIRICAL PIVOT RIGHT CONFIRMATION STUDY
    # -------------------------------------------------------------
    def study_pivot_right_sensitivity():
        results = []
        for left in [6, 10]:
            for right in [1, 2, 3, 4, 5, 6, 7]:
                piv_low_count = 0
                piv_high_count = 0
                survived_10_bars_low = 0
                survived_20_bars_low = 0
                survived_10_bars_high = 0
                survived_20_bars_high = 0

                lag_drawdown_pts_low = []
                lag_drawdown_pts_high = []
                move_captured_pts_low = []
                move_captured_pts_high = []

                for i in range(left + right, n - 20):
                    if times[i] < OCT_1_TS:
                        continue
                    piv_idx = i - right

                    is_low = True
                    for l_bar in range(piv_idx - left, piv_idx):
                        if lows[l_bar] <= lows[piv_idx]:
                            is_low = False
                            break
                    if is_low:
                        for r_bar in range(piv_idx + 1, piv_idx + right + 1):
                            if lows[r_bar] < lows[piv_idx]:
                                is_low = False
                                break
                    if is_low:
                        piv_low_count += 1
                        min_next_10 = min(lows[i + 1 : i + 11])
                        min_next_20 = min(lows[i + 1 : i + 21])
                        if min_next_10 >= lows[piv_idx]:
                            survived_10_bars_low += 1
                        if min_next_20 >= lows[piv_idx]:
                            survived_20_bars_low += 1
                        lag_drawdown_pts_low.append(closes[i] - lows[piv_idx])
                        max_favorable = max(highs[i + 1 : i + 21]) - closes[i]
                        move_captured_pts_low.append(max_favorable)

                    is_high = True
                    for l_bar in range(piv_idx - left, piv_idx):
                        if highs[l_bar] >= highs[piv_idx]:
                            is_high = False
                            break
                    if is_high:
                        for r_bar in range(piv_idx + 1, piv_idx + right + 1):
                            if highs[r_bar] > highs[piv_idx]:
                                is_high = False
                                break
                    if is_high:
                        piv_high_count += 1
                        max_next_10 = max(highs[i + 1 : i + 11])
                        max_next_20 = max(highs[i + 1 : i + 21])
                        if max_next_10 <= highs[piv_idx]:
                            survived_10_bars_high += 1
                        if max_next_20 <= highs[piv_idx]:
                            survived_20_bars_high += 1
                        lag_drawdown_pts_high.append(highs[piv_idx] - closes[i])
                        max_favorable = closes[i] - min(lows[i + 1 : i + 21])
                        move_captured_pts_high.append(max_favorable)

                total_pivots = piv_low_count + piv_high_count
                total_surv_10 = survived_10_bars_low + survived_10_bars_high
                total_surv_20 = survived_20_bars_low + survived_20_bars_high

                pct_surv_10 = (total_surv_10 / total_pivots * 100) if total_pivots > 0 else 0
                pct_surv_20 = (total_surv_20 / total_pivots * 100) if total_pivots > 0 else 0

                avg_lag_cost = sum(lag_drawdown_pts_low + lag_drawdown_pts_high) / total_pivots if total_pivots > 0 else 0
                avg_mfe = sum(move_captured_pts_low + move_captured_pts_high) / total_pivots if total_pivots > 0 else 0

                results.append({
                    'left': left,
                    'right': right,
                    'delay_mins': right * 5,
                    'total_pivots': total_pivots,
                    'pct_survived_10_bars': round(pct_surv_10, 1),
                    'pct_survived_20_bars': round(pct_surv_20, 1),
                    'avg_lag_pts': round(avg_lag_cost, 2),
                    'avg_lag_usd': round(avg_lag_cost * 10.0, 2),
                    'avg_mfe_20b_pts': round(avg_mfe, 2)
                })
        return results

    print("Running SuperTrend Backtests...")
    st_tv = backtest_supertrend(80, 1.7)
    st_preset = backtest_supertrend(80, 2.2)

    print("Running cRSI Backtests...")
    crsi_live_tv = backtest_crsi(left=6, right=3, atr_mult=3.0, mode='EXTENSIONS', use_filter=True)
    crsi_live_nofilt = backtest_crsi(left=6, right=3, atr_mult=3.0, mode='EXTENSIONS', use_filter=False)
    crsi_strict_alt = backtest_crsi(left=6, right=3, atr_mult=3.0, mode='STRICT_ALT', use_filter=True)
    crsi_major_tv = backtest_crsi(left=10, right=5, atr_mult=3.0, mode='EXTENSIONS', use_filter=True)
    crsi_old_std = backtest_crsi(left=8, right=5, atr_mult=1.5, mode='STRICT_ALT', use_filter=False)

    print("Running Empirical Pivot Right Study...")
    empirical_study = study_pivot_right_sensitivity()

    output = {
        'evaluation_period': {
            'start_utc': '2026-10-01T00:00:00Z',
            'end_utc': '2026-11-13T21:55:00Z',
            'symbol': 'COMEX_MINI:MGC1!',
            'timeframe': '5m',
            'total_bars_evaluated': 8808
        },
        'supertrend_results': [st_tv, st_preset],
        'crsi_results': [crsi_live_tv, crsi_live_nofilt, crsi_strict_alt, crsi_major_tv, crsi_old_std],
        'empirical_pivot_right_study': empirical_study
    }

    with open('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests/backtest_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n=== RESULTS SUMMARY ===")
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    run_analysis()
