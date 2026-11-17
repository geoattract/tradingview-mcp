import numpy as np
import pandas as pd
import math

def calculate_crsi_v4(df, tf_sec=300):
    """
    Exact Pine Script v6 implementation of cRSI Universal [V4].
    """
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    # 0. Auto-Timeframe detection
    is_intraday = tf_sec < 1800
    is_swing = (tf_sec >= 1800) and (tf_sec <= 14400)

    eff_base_cycle = 24 if is_intraday else (28 if is_swing else 30)
    eff_min_cycle = 12 if is_intraday else (14 if is_swing else 15)
    eff_max_cycle = 50 if is_intraday else (60 if is_swing else 70)
    eff_atr_short = 14 if is_intraday else (18 if is_swing else 21)
    eff_atr_long = 100 if is_intraday else (125 if is_swing else 150)
    eff_leveling = 10.0 if is_intraday else (9.0 if is_swing else 8.5)

    # 1. TR and ATRs (ta.atr in Pine is ta.rma(ta.tr(true), length))
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))

    def calc_rma(src, length):
        out = np.zeros(n)
        alpha = 1.0 / length
        s = 0.0
        for i in range(n):
            if i < length:
                s += src[i]
                out[i] = s / (i + 1)
            else:
                out[i] = alpha * src[i] + (1.0 - alpha) * out[i-1]
        return out

    atr_short = calc_rma(tr, eff_atr_short)
    atr_long = calc_rma(tr, eff_atr_long)

    # Dynamic Cycle calculation
    domcycle = np.zeros(n, dtype=int)
    cyclelen = np.zeros(n, dtype=int)
    cyclicmemory = np.zeros(n, dtype=int)
    atr_ratio = np.zeros(n)

    for i in range(n):
        if atr_long[i] > 0 and atr_short[i] > 0:
            raw_ratio = atr_short[i] / atr_long[i]
        else:
            raw_ratio = 1.0
        r = max(0.25, min(4.0, raw_ratio))
        atr_ratio[i] = r
        raw_dyn = eff_base_cycle / r
        dc = int(max(eff_min_cycle, min(eff_max_cycle, round(raw_dyn))))
        domcycle[i] = dc
        cyclelen[i] = max(1, dc // 2)
        cyclicmemory[i] = dc * 2

    # 2. cRSI Core Calculation
    # f_dyn_rma:
    # alpha = length > 0 ? 1.0 / length : 1.0
    # sum := na(sum[1]) ? src_val : alpha * src_val + (1.0 - alpha) * sum[1]
    up_arr = np.zeros(n)
    down_arr = np.zeros(n)
    rsi_val = np.full(n, 50.0)

    for i in range(1, n):
        clen = cyclelen[i]
        alpha = 1.0 / clen
        src_change = closes[i] - closes[i-1]
        u = max(src_change, 0.0)
        d = -min(src_change, 0.0)

        if i == 1:
            up_arr[i] = u
            down_arr[i] = d
        else:
            up_arr[i] = alpha * u + (1.0 - alpha) * up_arr[i-1]
            down_arr[i] = alpha * d + (1.0 - alpha) * down_arr[i-1]

        if up_arr[i] == 0.0 and down_arr[i] == 0.0:
            rsi_val[i] = 50.0
        elif down_arr[i] == 0.0:
            rsi_val[i] = 100.0
        elif up_arr[i] == 0.0:
            rsi_val[i] = 0.0
        else:
            rsi_val[i] = 100.0 - 100.0 / (1.0 + up_arr[i] / down_arr[i])

    vibration = 10
    torque = 2.0 / (vibration + 1)  # 2.0 / 11.0
    phasing_lag = int(round((vibration - 1) / 2.0))  # 5
    crsi = np.full(n, 50.0)

    for i in range(1, n):
        lag_idx = max(0, i - phasing_lag)
        crsi[i] = torque * (2.0 * rsi_val[i] - rsi_val[lag_idx]) + (1.0 - torque) * crsi[i-1]

    # Dynamic Upper & Lower Reference Bands (Percentile Nearest Rank)
    # db = ta.percentile_nearest_rank(crsi, cyclicmemory, eff_leveling)
    # ub = ta.percentile_nearest_rank(crsi, cyclicmemory, 100.0 - eff_leveling)
    db = np.zeros(n)
    ub = np.zeros(n)

    for i in range(n):
        cm = cyclicmemory[i]
        start_idx = max(0, i - cm + 1)
        window = crsi[start_idx : i + 1]
        sorted_w = np.sort(window)
        k_len = len(sorted_w)

        # Nearest rank formula: rank = ceil(P / 100.0 * length)
        # index = rank - 1
        rank_db = int(math.ceil(eff_leveling / 100.0 * k_len))
        rank_db = max(1, min(k_len, rank_db))
        db[i] = sorted_w[rank_db - 1]

        rank_ub = int(math.ceil((100.0 - eff_leveling) / 100.0 * k_len))
        rank_ub = max(1, min(k_len, rank_ub))
        ub[i] = sorted_w[rank_ub - 1]

    return {
        'crsi': crsi,
        'rsi_val': rsi_val,
        'domcycle': domcycle,
        'cyclelen': cyclelen,
        'cyclicmemory': cyclicmemory,
        'atr_ratio': atr_ratio,
        'atr_short': atr_short,
        'atr_long': atr_long,
        'db': db,
        'ub': ub
    }

if __name__ == '__main__':
    df = pd.read_csv('mnq_5m_data.csv')
    res = calculate_crsi_v4(df, tf_sec=300)
    print("cRSI V4 computed successfully on 5m data!")
    print(f"Total bars: {len(df)}")
    print(f"cRSI min: {res['crsi'].min():.2f}, max: {res['crsi'].max():.2f}, mean: {res['crsi'].mean():.2f}")
    print(f"ub mean: {res['ub'].mean():.2f}, min: {res['ub'].min():.2f}, max: {res['ub'].max():.2f}")
    print(f"db mean: {res['db'].mean():.2f}, min: {res['db'].min():.2f}, max: {res['db'].max():.2f}")
    print(f"domcycle mean: {res['domcycle'].mean():.2f}, min: {res['domcycle'].min()}, max: {res['domcycle'].max()}")
