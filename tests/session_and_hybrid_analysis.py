#!/usr/bin/env python3
import json
from datetime import datetime, timezone

def run_session_and_hybrid():
    with open('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests/mgc1_5m_all.json', 'r') as f:
        bars_raw = json.load(f)
    
    n = len(bars_raw)
    times = [b[0] for b in bars_raw]
    opens = [b[1] for b in bars_raw]
    highs = [b[2] for b in bars_raw]
    lows = [b[3] for b in bars_raw]
    closes = [b[4] for b in bars_raw]
    volumes = [b[5] for b in bars_raw]

    OCT_1_TS = 1790812800

    # ATRs
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

    atr14 = calc_rma(tr, 14)
    atr100 = calc_rma(tr, 100)
    atr80 = calc_rma(tr, 80)

    # SuperTrend series (80, 2.2 and 80, 1.7)
    def get_st_trend(mult):
        trend = [1] * n
        up = [0.0] * n
        dn = [0.0] * n
        for i in range(1, n):
            hl2 = (highs[i] + lows[i]) / 2.0
            basic_up = hl2 - mult * atr80[i]
            basic_dn = hl2 + mult * atr80[i]
            up1 = up[i-1]
            up[i] = max(basic_up, up1) if closes[i-1] > up1 else basic_up
            dn1 = dn[i-1]
            dn[i] = min(basic_dn, dn1) if closes[i-1] < dn1 else basic_dn

            prev_t = trend[i-1]
            if prev_t == -1 and closes[i] > dn1:
                trend[i] = 1
            elif prev_t == 1 and closes[i] < up1:
                trend[i] = -1
            else:
                trend[i] = prev_t
        return trend

    st_trend_22 = get_st_trend(2.2)
    st_trend_17 = get_st_trend(1.7)

    # cRSI series
    crsi = [50.0] * n
    domcycle_arr = [24] * n
    up_arr = [0.0] * n
    down_arr = [0.0] * n
    rsi_arr = [50.0] * n
    for i in range(1, n):
        raw_ratio = (atr14[i] / atr100[i]) if (atr100[i] > 0 and atr14[i] > 0) else 1.0
        atr_ratio = max(0.25, min(4.0, raw_ratio))
        domcycle = int(max(12, min(50, round(24.0 / atr_ratio))))
        domcycle_arr[i] = domcycle
        cyclelen = max(1, domcycle // 2)

        change = closes[i] - closes[i-1]
        alpha = 1.0 / cyclelen
        up_arr[i] = alpha * max(change, 0.0) + (1.0 - alpha) * up_arr[i-1]
        down_arr[i] = alpha * (-min(change, 0.0)) + (1.0 - alpha) * down_arr[i-1]
        rsi_val = 50.0 if (up_arr[i] == 0 and down_arr[i] == 0) else (100.0 if down_arr[i] == 0 else (0.0 if up_arr[i] == 0 else 100.0 - 100.0 / (1.0 + up_arr[i] / down_arr[i])))
        rsi_arr[i] = rsi_val
        crsi[i] = (2.0 / 11.0) * (2.0 * rsi_val - rsi_arr[max(0, i-4)]) + (9.0 / 11.0) * crsi[i-1]

    # Session classification: Asian (00:00 - 07:00 UTC), London (07:00 - 13:30 UTC), US (13:30 - 20:00 UTC), Settlement/Off (20:00 - 00:00 UTC)
    def get_session(ts):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        hour = dt.hour + dt.minute / 60.0
        if 0.0 <= hour < 7.0:
            return "Asian"
        elif 7.0 <= hour < 13.5:
            return "London"
        elif 13.5 <= hour < 20.0:
            return "US_NY"
        else:
            return "Evening_Off"

    # Evaluate cRSI trades by session
    # Left=6, Right=3, ATR=3.0, Extensions, Filter=True
    left = 6
    right = 3
    atr_mult = 3.0
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

        dyn_lb = int(max(16, min(50, round(domcycle_arr[i] * 1.5))))
        c_slice = crsi[max(0, i - dyn_lb) : i + 1]
        span = max(c_slice) - min(c_slice)
        rel_pos = (crsi[piv_idx] - min(c_slice)) / span if span > 0 else 0.5
        peak_crsi_ok = (rel_pos >= 0.50)
        trough_crsi_ok = (rel_pos <= 0.50)

        min_move = atr_mult * atr14[i]
        peak_dist_ok = (run_low is None) or (pivH is not None and pivH - run_low >= min_move)
        trough_dist_ok = (run_high is None) or (pivL is not None and run_high - pivL >= min_move)

        raw_peak = (pivH is not None) and peak_crsi_ok and peak_dist_ok
        raw_trough = (pivL is not None) and trough_crsi_ok and trough_dist_ok

        can_ext_peak = (last_pivot_dir == 1) and (last_peak_price is not None and pivH is not None and pivH > last_peak_price)
        can_ext_trough = (last_pivot_dir == -1) and (last_trough_price is not None and pivL is not None and pivL < last_trough_price)

        peak_eligible = raw_peak and (last_pivot_dir != 1 or can_ext_peak)
        trough_eligible = raw_trough and (last_pivot_dir != -1 or can_ext_trough)
        if peak_eligible and trough_eligible:
            if last_pivot_dir == 1:
                peak_eligible = False
            else:
                trough_eligible = False

        peak_confirmed = False
        trough_confirmed = False
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
                pnl = entry_price - closes[i]
                trades.append({
                    'type': 'SHORT',
                    'session': get_session(entry_time),
                    'pnl_pts': pnl,
                    'pnl_usd': pnl * 10.0
                })
            pos = 1
            entry_price = closes[i]
            entry_time = times[i]
            entry_bar = i
        elif peak_confirmed:
            if pos == 1:
                pnl = closes[i] - entry_price
                trades.append({
                    'type': 'LONG',
                    'session': get_session(entry_time),
                    'pnl_pts': pnl,
                    'pnl_usd': pnl * 10.0
                })
            pos = -1
            entry_price = closes[i]
            entry_time = times[i]
            entry_bar = i

    session_stats = {}
    for s in ["Asian", "London", "US_NY", "Evening_Off"]:
        s_trades = [t for t in trades if t['session'] == s]
        if s_trades:
            wins = [t for t in s_trades if t['pnl_pts'] > 0]
            pts = sum(t['pnl_pts'] for t in s_trades)
            win_rate = len(wins) / len(s_trades) * 100
            gross_win = sum(t['pnl_usd'] for t in wins)
            gross_loss = sum(abs(t['pnl_usd']) for t in s_trades if t['pnl_usd'] <= 0)
            pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
            session_stats[s] = {
                'trades': len(s_trades),
                'win_rate': round(win_rate, 1),
                'net_pnl_usd': round(pts * 10.0, 2),
                'profit_factor': round(pf, 2)
            }

    print("\n--- SESSION BREAKDOWN FOR cRSI V5 ---")
    print(json.dumps(session_stats, indent=2))

    with open('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests/session_results.json', 'w') as f:
        json.dump(session_stats, f, indent=2)

if __name__ == '__main__':
    run_session_and_hybrid()
