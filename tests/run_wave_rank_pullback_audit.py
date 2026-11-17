import json
import numpy as np
from test_rsi_vs_supertrend_mgc import load_data, calc_rma, calc_sma, calc_rsi, calc_supertrend, calc_stoch_rsi

def audit_wave_ranks(filepath, dataset_name):
    times, opens, highs, lows, closes, volumes = load_data(filepath)
    n = len(closes)
    
    # 1. SuperTrend 80/2.2
    st_trend, st_up, st_dn, atr80 = calc_supertrend(highs, lows, closes, 80, 2.2)
    
    # 2. RSI Purple and Yellow
    rsi_purple = calc_rsi(closes, 14)
    rsi_yellow = calc_sma(rsi_purple, 14)
    
    # 3. Stoch RSI
    stochK, stochD, _ = calc_stoch_rsi(closes, 14, 14, 3, 3)
    
    # Signal sets:
    # A. Purple x Yellow Pure
    pxy_buy = np.zeros(n, dtype=bool)
    pxy_sell = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if rsi_purple[i] > rsi_yellow[i] and rsi_purple[i-1] <= rsi_yellow[i-1]:
            pxy_buy[i] = True
        if rsi_purple[i] < rsi_yellow[i] and rsi_purple[i-1] >= rsi_yellow[i-1]:
            pxy_sell[i] = True
            
    # B. Purple x Yellow Dip/Pop (RSI pulls back below yellow & <=48 in uptrend, crosses up; or >=52 in downtrend, crosses down)
    pxy_dip_buy = np.zeros(n, dtype=bool)
    pxy_dip_sell = np.zeros(n, dtype=bool)
    b_arm = False
    s_arm = False
    for i in range(1, n):
        if st_trend[i] != st_trend[i-1]:
            b_arm, s_arm = False, False
        if st_trend[i] == 1:
            if rsi_purple[i] < rsi_yellow[i] and rsi_purple[i] <= 48.0:
                b_arm = True
            if b_arm and rsi_purple[i] > rsi_yellow[i] and rsi_purple[i-1] <= rsi_yellow[i-1]:
                pxy_dip_buy[i] = True
                b_arm = False
        elif st_trend[i] == -1:
            if rsi_purple[i] > rsi_yellow[i] and rsi_purple[i] >= 52.0:
                s_arm = True
            if s_arm and rsi_purple[i] < rsi_yellow[i] and rsi_purple[i-1] >= rsi_yellow[i-1]:
                pxy_dip_sell[i] = True
                s_arm = False

    # C. Stoch RSI Armed (<=30 / >=70)
    srsi_deep_buy = np.zeros(n, dtype=bool)
    srsi_deep_sell = np.zeros(n, dtype=bool)
    sb_arm, ss_arm = False, False
    for i in range(1, n):
        if st_trend[i] != st_trend[i-1]:
            sb_arm, ss_arm = False, False
        if st_trend[i] == 1:
            if stochK[i] <= 30.0 and stochK[i] <= stochD[i]:
                sb_arm = True
            if stochK[i] >= 70.0:
                sb_arm = False
            kTurnUp = stochK[i] > stochD[i] and stochK[i] > stochK[i-1]
            if sb_arm and kTurnUp and closes[i] > opens[i]:
                srsi_deep_buy[i] = True
                sb_arm = False
        elif st_trend[i] == -1:
            if stochK[i] >= 70.0 and stochK[i] >= stochD[i]:
                ss_arm = True
            if stochK[i] <= 30.0:
                ss_arm = False
            kTurnDown = stochK[i] < stochD[i] and stochK[i] < stochK[i-1]
            if ss_arm and kTurnDown and closes[i] < opens[i]:
                srsi_deep_sell[i] = True
                ss_arm = False

    # D. Stoch RSI Pure Cross
    srsi_pure_buy = np.zeros(n, dtype=bool)
    srsi_pure_sell = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if stochK[i] > stochD[i] and stochK[i-1] <= stochD[i-1]:
            srsi_pure_buy[i] = True
        if stochK[i] < stochD[i] and stochK[i-1] >= stochD[i-1]:
            srsi_pure_sell[i] = True

    # Segment into SuperTrend Waves
    def evaluate_engine_ranks(buy_sigs, sell_sigs, engine_label):
        waves = []
        curr_dir = None
        curr_start = None
        curr_pbs = []
        
        warmup = 80
        for i in range(warmup, n):
            if st_trend[i] != st_trend[i-1]:
                if curr_dir is not None:
                    waves.append({
                        'dir': curr_dir,
                        'start_i': curr_start,
                        'end_i': i,
                        'pullbacks': curr_pbs
                    })
                curr_dir = st_trend[i]
                curr_start = i
                curr_pbs = []
            else:
                if curr_dir == 1 and buy_sigs[i]:
                    curr_pbs.append({'bar': i, 'price': closes[i], 'dir': 1})
                elif curr_dir == -1 and sell_sigs[i]:
                    curr_pbs.append({'bar': i, 'price': closes[i], 'dir': -1})
                    
        if curr_dir is not None:
            waves.append({
                'dir': curr_dir,
                'start_i': curr_start,
                'end_i': n - 1,
                'pullbacks': curr_pbs
            })
            
        # Group by ranks
        ranks_config = [
            ("1st Pullback Only", [1]),
            ("2nd Pullback Only", [2]),
            ("3rd Pullback Only", [3]),
            ("All Pullbacks Combined", list(range(1, 100)))
        ]
        
        print(f"\n--- Wave-Rank Breakdown: {engine_label} ---")
        print(f"{'Rank':<24} | {'Trades':<8} | {'Win Rate':<10} | {'PF':<6} | {'Gross PnL':<12} | {'Net PnL':<12} | {'Max DD':<10} | {'Avg Trade':<10}")
        print("-" * 105)
        
        for rank_title, r_list in ranks_config:
            trades = []
            for w in waves:
                pbs = w['pullbacks']
                exit_price = closes[w['end_i']]
                for r in r_list:
                    if len(pbs) >= r:
                        pb = pbs[r - 1]
                        pnl_pts = (exit_price - pb['price']) if pb['dir'] == 1 else (pb['price'] - exit_price)
                        trades.append({
                            'pnl_gross': pnl_pts * 10.0,
                            'pnl_net': pnl_pts * 10.0 - 4.0
                        })
            cnt = len(trades)
            if cnt == 0:
                print(f"{rank_title:<24} | {0:<8} | {'N/A':<10} | {'N/A':<6} | {'$0.00':<12} | {'$0.00':<12} | {'$0.00':<10} | {'$0.00':<10}")
                continue
            wins = [t for t in trades if t['pnl_gross'] > 0]
            losses = [t for t in trades if t['pnl_gross'] <= 0]
            wr = len(wins) / cnt * 100.0
            gross_win = sum(t['pnl_gross'] for t in wins)
            gross_loss = abs(sum(t['pnl_gross'] for t in losses))
            pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
            gross_pnl = sum(t['pnl_gross'] for t in trades)
            net_pnl = sum(t['pnl_net'] for t in trades)
            
            cum = 0.0
            peak = 0.0
            max_dd = 0.0
            for t in trades:
                cum += t['pnl_net']
                if cum > peak: peak = cum
                dd = peak - cum
                if dd > max_dd: max_dd = dd
                
            print(f"{rank_title:<24} | {cnt:<8} | {wr:<9.1f}% | {pf:<6.2f} | ${gross_pnl:<11.2f} | ${net_pnl:<11.2f} | ${max_dd:<9.2f} | ${net_pnl/cnt:<9.2f}")

    print(f"\n==========================================================================================")
    print(f"PULLBACK RANK-BY-RANK AUDIT: {dataset_name} ({n} bars)")
    print(f"==========================================================================================")
    evaluate_engine_ranks(pxy_buy, pxy_sell, "Purple x Yellow (Pure Crossover)")
    evaluate_engine_ranks(pxy_dip_buy, pxy_dip_sell, "Purple x Yellow (Armed Dip/Pop)")
    evaluate_engine_ranks(srsi_deep_buy, srsi_deep_sell, "Stoch RSI (Armed OS/OB 30/70)")
    evaluate_engine_ranks(srsi_pure_buy, srsi_pure_sell, "Stoch RSI (Pure %K x %D)")

audit_wave_ranks('tests/mgc1_5m_all.json', 'MGC1! 5-Minute (Full 11,040 Bars)')
audit_wave_ranks('tests/mgc1_2m.json', 'MGC1! 2-Minute (Recent 465 Bars)')
