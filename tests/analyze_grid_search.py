#!/usr/bin/env python3
"""
analyze_grid_search.py
=============================================================================
Comprehensive Parameter Surface & Plateau Robustness Analysis for
Supertrend V4 + RSI on CME Micro Nasdaq-100 Futures (MNQ1! 5m)
Period: 01 Oct 2026 00:00:00 UTC to 17 Nov 2026 00:05:00 UTC
=============================================================================
"""

import pandas as pd
import numpy as np
import json
import os

def run_analysis():
    print("Loading grid_search_results.csv...")
    df = pd.read_csv('grid_search_results.csv')
    print(f"Total parameter combinations analyzed: {len(df):,}")

    # Calculate additional metrics
    # Calmar / MAR Ratio (Net PnL / Max Drawdown)
    df['calmar_ratio'] = np.where(df['max_dd_pts'] > 0, df['net_pts'] / df['max_dd_pts'], 0.0)
    df['uplift_vs_pure_st_pts'] = df['net_pts'] - df['pure_st_net_pts']
    df['dd_reduction_vs_pure_st_pts'] = df['pure_st_max_dd_pts'] - df['max_dd_pts']
    df['dd_reduction_pct'] = np.where(df['pure_st_max_dd_pts'] > 0, (df['pure_st_max_dd_pts'] - df['max_dd_pts']) / df['pure_st_max_dd_pts'] * 100.0, 0.0)

    # -------------------------------------------------------------
    # 1. PARAMETER MARGINAL SENSITIVITIES (Main Effects)
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("1. MARGINAL PARAMETER IMPACTS (Averaged across all other dimensions)")
    print("=" * 80)

    # ATR Period
    print("\n--- A. Supertrend ATR Period ---")
    p_stat = df.groupby('period').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(p_stat)

    # Multiplier
    print("\n--- B. Supertrend Multiplier ---")
    m_stat = df.groupby('mult').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(m_stat)

    # ATR Smoothing Method
    print("\n--- C. ATR Smoothing Method ---")
    met_stat = df.groupby('method').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(met_stat)

    # Price Source
    print("\n--- D. Price Source (hl2 vs close) ---")
    src_stat = df.groupby('source').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(src_stat)

    # Stoch RSI Zone Mode
    print("\n--- E. Stoch RSI Zone Mode ---")
    zone_stat = df.groupby('zone_mode').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(zone_stat)

    # RSI Length
    print("\n--- F. Stoch RSI: RSI Length ---")
    rsi_stat = df.groupby('rsi_len').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(rsi_stat)

    # Pullback Confirmation Candle
    print("\n--- G. Pullback Confirmation Candle (req_candle) ---")
    candle_stat = df.groupby('req_candle').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(candle_stat)

    # Pullback Cooldown Spacing
    print("\n--- H. Pullback Cooldown Spacing (bars) ---")
    cd_stat = df.groupby('cooldown').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(cd_stat)

    # Early Turning Dot OS/OB levels
    print("\n--- I. Early Turning Dot OS / OB Levels ---")
    df['dot_pair'] = df['dot_os'].astype(str) + " / " + df['dot_ob'].astype(str)
    dot_stat = df.groupby('dot_pair').agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Median_Net_Pts=('net_pts', 'median'),
        Mean_PF=('pf', 'mean'),
        Mean_WR=('win_rate', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean')
    ).round(2)
    print(dot_stat)

    # -------------------------------------------------------------
    # 2. GLOBAL OPTIMA (Raw Performance)
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. TOP 10 GLOBAL OPTIMA BY NET POINTS P&L")
    print("=" * 80)
    top_pnl = df.sort_values(by='net_pts', ascending=False).head(10)
    for i, (_, r) in enumerate(top_pnl.iterrows()):
        print(f"#{i+1:2d} | Net: +{r['net_pts']:7.1f} pts (${r['net_usd']:9.2f}) | PF: {r['pf']:5.2f} | WR: {r['win_rate']:4.1f}% | "
              f"DD: {r['max_dd_pts']:6.1f} pts (${r['max_dd_usd']:8.2f}) | Calmar: {r['calmar_ratio']:4.2f} | Trades: {int(r['trades']):3d} | "
              f"ST: ({int(r['period'])}, {r['mult']:.1f}, {r['method']}, {r['source']}) | "
              f"Zone: {r['zone_mode']} | RSI_L: {int(r['rsi_len'])} | Candle: {bool(r['req_candle'])} | CD: {int(r['cooldown'])} | "
              f"Dots: ({r['dot_os']:.0f}/{r['dot_ob']:.0f})")

    print("\n" + "=" * 80)
    print("3. TOP 10 BY CALMAR RATIO (Net PnL / Max Drawdown, Trades >= 100)")
    print("=" * 80)
    top_calmar = df[df['trades'] >= 100].sort_values(by='calmar_ratio', ascending=False).head(10)
    for i, (_, r) in enumerate(top_calmar.iterrows()):
        print(f"#{i+1:2d} | Calmar: {r['calmar_ratio']:4.2f} | Net: +{r['net_pts']:7.1f} pts (${r['net_usd']:9.2f}) | PF: {r['pf']:5.2f} | WR: {r['win_rate']:4.1f}% | "
              f"DD: {r['max_dd_pts']:6.1f} pts (${r['max_dd_usd']:8.2f}) | Trades: {int(r['trades']):3d} | "
              f"ST: ({int(r['period'])}, {r['mult']:.1f}, {r['method']}, {r['source']}) | "
              f"Zone: {r['zone_mode']} | RSI_L: {int(r['rsi_len'])} | Candle: {bool(r['req_candle'])} | CD: {int(r['cooldown'])} | "
              f"Dots: ({r['dot_os']:.0f}/{r['dot_ob']:.0f})")

    # -------------------------------------------------------------
    # 3. 3D PARAMETER SURFACE PLATEAU & ROBUSTNESS ANALYSIS
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("4. PARAMETER SURFACE PLATEAU & NEIGHBORHOOD ROBUSTNESS ANALYSIS")
    print("=" * 80)

    # To assess robustness and eliminate fragile curve-fitting spikes,
    # we compute the mean performance across the 3x3 local neighborhood:
    # Period: [10, 14, 20, 50, 80, 100] -> idx 0..5
    # Mult:   [1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0] -> idx 0..6
    
    # We create a lookup dictionary for fast neighbor aggregation
    period_list = [10, 14, 20, 50, 80, 100]
    mult_list = [1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0]
    p_map = {p: i for i, p in enumerate(period_list)}
    m_map = {m: i for i, m in enumerate(mult_list)}

    # Group by Macro Supertrend Configuration (period, mult, method, source)
    st_group = df.groupby(['period', 'mult', 'method', 'source']).agg(
        Mean_Net_Pts=('net_pts', 'mean'),
        Max_Net_Pts=('net_pts', 'max'),
        Min_Net_Pts=('net_pts', 'min'),
        Std_Net_Pts=('net_pts', 'std'),
        Mean_PF=('pf', 'mean'),
        Mean_MaxDD=('max_dd_pts', 'mean'),
        Min_MaxDD=('max_dd_pts', 'min'),
        Mean_Calmar=('calmar_ratio', 'mean'),
        Mean_Trades=('trades', 'mean'),
        Pure_ST_Net=('pure_st_net_pts', 'first'),
        Pure_ST_PF=('pure_st_pf', 'first'),
        Pure_ST_DD=('pure_st_max_dd_pts', 'first')
    ).reset_index()

    # Now compute 2D neighborhood stats across (period, mult) for each (method, source)
    robustness_rows = []
    for (method, source), sub in st_group.groupby(['method', 'source']):
        # create grid indexed by (p_idx, m_idx)
        grid = {}
        for _, r in sub.iterrows():
            grid[(p_map[r['period']], m_map[r['mult']])] = r

        for (p_idx, m_idx), r in grid.items():
            # Neighbors: p_idx +/- 1, m_idx +/- 1
            neighbor_nets = []
            neighbor_pfs = []
            neighbor_dds = []
            for dp in [-1, 0, 1]:
                for dm in [-1, 0, 1]:
                    np_idx = p_idx + dp
                    nm_idx = m_idx + dm
                    if (np_idx, nm_idx) in grid:
                        neighbor_nets.append(grid[(np_idx, nm_idx)]['Mean_Net_Pts'])
                        neighbor_pfs.append(grid[(np_idx, nm_idx)]['Mean_PF'])
                        neighbor_dds.append(grid[(np_idx, nm_idx)]['Mean_MaxDD'])

            neighbor_mean_net = np.mean(neighbor_nets)
            neighbor_min_net = np.min(neighbor_nets)
            neighbor_std_net = np.std(neighbor_nets)
            neighbor_mean_pf = np.mean(neighbor_pfs)
            neighbor_mean_dd = np.mean(neighbor_dds)
            
            # Robustness Metric:
            # Rewards high neighbor mean PnL, high minimum neighbor PnL (no weak dropoffs),
            # low neighbor std, and lower drawdown:
            plateau_score = (neighbor_min_net / (neighbor_mean_dd + 1e-5)) * (neighbor_mean_pf) if neighbor_min_net > 0 else neighbor_min_net

            robustness_rows.append({
                'period': r['period'],
                'mult': r['mult'],
                'method': method,
                'source': source,
                'macro_mean_net': r['Mean_Net_Pts'],
                'macro_max_net': r['Max_Net_Pts'],
                'macro_min_net': r['Min_Net_Pts'],
                'macro_mean_pf': r['Mean_PF'],
                'macro_mean_dd': r['Mean_MaxDD'],
                'macro_mean_calmar': r['Mean_Calmar'],
                'neighbor_mean_net': neighbor_mean_net,
                'neighbor_min_net': neighbor_min_net,
                'neighbor_std_net': neighbor_std_net,
                'neighbor_mean_pf': neighbor_mean_pf,
                'neighbor_mean_dd': neighbor_mean_dd,
                'plateau_score': plateau_score,
                'pure_st_net': r['Pure_ST_Net'],
                'pure_st_pf': r['Pure_ST_PF'],
                'pure_st_dd': r['Pure_ST_DD']
            })

    rob_df = pd.DataFrame(robustness_rows)

    print("\nTOP 10 ROBUST SUPERTREND MACRO PLATEAUS (Ranked by Plateau Stability Score):")
    top_plateaus = rob_df.sort_values(by='plateau_score', ascending=False).head(10)
    for i, (_, r) in enumerate(top_plateaus.iterrows()):
        print(f"#{i+1:2d} | ST: ({int(r['period']):3d}, {r['mult']:.1f}, {r['method']:3s}, {r['source']:5s}) | "
              f"Plateau Score: {r['plateau_score']:5.2f} | Neighbor Mean Net: +{r['neighbor_mean_net']:6.1f} pts | "
              f"Neighbor Min Net: +{r['neighbor_min_net']:6.1f} pts | Neighbor Mean PF: {r['neighbor_mean_pf']:4.2f} | "
              f"Neighbor Mean DD: {r['neighbor_mean_dd']:5.1f} pts | Macro Avg Net: +{r['macro_mean_net']:6.1f} pts | "
              f"Pure ST Baseline: +{r['pure_st_net']:6.1f} pts (PF {r['pure_st_pf']:.2f}, DD {r['pure_st_dd']:.1f})")

    # -------------------------------------------------------------
    # 4. HEAD-TO-HEAD COMPARISON WITH CURRENT DEFAULTS
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("5. DIRECT HEAD-TO-HEAD BENCHMARK: DEFAULTS VS GLOBAL & PLATEAU OPTIMA")
    print("=" * 80)

    # Default 1: ATR 80, Mult 1.4 SMA hl2
    def1_pure = df[(df['period'] == 80) & (df['mult'] == 1.4) & (df['method'] == 'SMA') & (df['source'] == 'hl2')].iloc[0]
    def1_best_v4 = df[(df['period'] == 80) & (df['mult'] == 1.4) & (df['method'] == 'SMA') & (df['source'] == 'hl2')].sort_values(by='net_pts', ascending=False).iloc[0]
    def1_calmar_v4 = df[(df['period'] == 80) & (df['mult'] == 1.4) & (df['method'] == 'SMA') & (df['source'] == 'hl2')].sort_values(by='calmar_ratio', ascending=False).iloc[0]

    # Default 2: ATR 80, Mult 2.0 SMA hl2
    def2_pure = df[(df['period'] == 80) & (df['mult'] == 2.0) & (df['method'] == 'SMA') & (df['source'] == 'hl2')].iloc[0]
    def2_best_v4 = df[(df['period'] == 80) & (df['mult'] == 2.0) & (df['method'] == 'SMA') & (df['source'] == 'hl2')].sort_values(by='net_pts', ascending=False).iloc[0]

    # Classic Baseline: ATR 10, Mult 3.0 RMA hl2
    base_pure = df[(df['period'] == 10) & (df['mult'] == 3.0) & (df['method'] == 'RMA') & (df['source'] == 'hl2')].iloc[0]
    base_best_v4 = df[(df['period'] == 10) & (df['mult'] == 3.0) & (df['method'] == 'RMA') & (df['source'] == 'hl2')].sort_values(by='net_pts', ascending=False).iloc[0]

    # Global Optimum Overall
    global_opt = df.sort_values(by='net_pts', ascending=False).iloc[0]

    # Plateau Winner (Highest Plateau Score)
    plat_winner_macro = top_plateaus.iloc[0]
    plat_winner_full = df[(df['period'] == plat_winner_macro['period']) & 
                          (df['mult'] == plat_winner_macro['mult']) & 
                          (df['method'] == plat_winner_macro['method']) & 
                          (df['source'] == plat_winner_macro['source'])].sort_values(by='net_pts', ascending=False).iloc[0]

    # Print summary table
    comparison_data = [
        {
            'Configuration': 'Classic Baseline Pure (10, 3.0 RMA hl2)',
            'Net Points': f"{base_pure['pure_st_net_pts']:+.1f} pts",
            'Net USD': f"${base_pure['pure_st_net_pts']*2.0:+.2f}",
            'Profit Factor': f"{base_pure['pure_st_pf']:.3f}",
            'Trades': f"{int(base_pure['pure_st_trades'])}",
            'Win Rate': "N/A",
            'Max Drawdown': f"{base_pure['pure_st_max_dd_pts']:.1f} pts (${base_pure['pure_st_max_dd_pts']*2.0:.2f})",
            'Calmar Ratio': f"{base_pure['pure_st_net_pts']/base_pure['pure_st_max_dd_pts']:.2f}"
        },
        {
            'Configuration': 'Default 1 Pure ST (80, 1.4 SMA hl2)',
            'Net Points': f"{def1_pure['pure_st_net_pts']:+.1f} pts",
            'Net USD': f"${def1_pure['pure_st_net_pts']*2.0:+.2f}",
            'Profit Factor': f"{def1_pure['pure_st_pf']:.3f}",
            'Trades': f"{int(def1_pure['pure_st_trades'])}",
            'Win Rate': "N/A",
            'Max Drawdown': f"{def1_pure['pure_st_max_dd_pts']:.1f} pts (${def1_pure['pure_st_max_dd_pts']*2.0:.2f})",
            'Calmar Ratio': f"{def1_pure['pure_st_net_pts']/def1_pure['pure_st_max_dd_pts']:.2f}"
        },
        {
            'Configuration': 'Default 1 with V4 RSI (80, 1.4 SMA hl2 Best)',
            'Net Points': f"{def1_best_v4['net_pts']:+.1f} pts",
            'Net USD': f"${def1_best_v4['net_usd']:+.2f}",
            'Profit Factor': f"{def1_best_v4['pf']:.3f}",
            'Trades': f"{int(def1_best_v4['trades'])}",
            'Win Rate': f"{def1_best_v4['win_rate']:.1f}%",
            'Max Drawdown': f"{def1_best_v4['max_dd_pts']:.1f} pts (${def1_best_v4['max_dd_usd']:.2f})",
            'Calmar Ratio': f"{def1_best_v4['calmar_ratio']:.2f}"
        },
        {
            'Configuration': 'Default 2 Pure ST (80, 2.0 SMA hl2)',
            'Net Points': f"{def2_pure['pure_st_net_pts']:+.1f} pts",
            'Net USD': f"${def2_pure['pure_st_net_pts']*2.0:+.2f}",
            'Profit Factor': f"{def2_pure['pure_st_pf']:.3f}",
            'Trades': f"{int(def2_pure['pure_st_trades'])}",
            'Win Rate': "N/A",
            'Max Drawdown': f"{def2_pure['pure_st_max_dd_pts']:.1f} pts (${def2_pure['pure_st_max_dd_pts']*2.0:.2f})",
            'Calmar Ratio': f"{def2_pure['pure_st_net_pts']/def2_pure['pure_st_max_dd_pts']:.2f}"
        },
        {
            'Configuration': 'Default 2 with V4 RSI (80, 2.0 SMA hl2 Best)',
            'Net Points': f"{def2_best_v4['net_pts']:+.1f} pts",
            'Net USD': f"${def2_best_v4['net_usd']:+.2f}",
            'Profit Factor': f"{def2_best_v4['pf']:.3f}",
            'Trades': f"{int(def2_best_v4['trades'])}",
            'Win Rate': f"{def2_best_v4['win_rate']:.1f}%",
            'Max Drawdown': f"{def2_best_v4['max_dd_pts']:.1f} pts (${def2_best_v4['max_dd_usd']:.2f})",
            'Calmar Ratio': f"{def2_best_v4['calmar_ratio']:.2f}"
        },
        {
            'Configuration': f"Robust Sweet Spot Plateau Winner ({int(plat_winner_full['period'])}, {plat_winner_full['mult']:.1f} {plat_winner_full['method']} {plat_winner_full['source']})",
            'Net Points': f"{plat_winner_full['net_pts']:+.1f} pts",
            'Net USD': f"${plat_winner_full['net_usd']:+.2f}",
            'Profit Factor': f"{plat_winner_full['pf']:.3f}",
            'Trades': f"{int(plat_winner_full['trades'])}",
            'Win Rate': f"{plat_winner_full['win_rate']:.1f}%",
            'Max Drawdown': f"{plat_winner_full['max_dd_pts']:.1f} pts (${plat_winner_full['max_dd_usd']:.2f})",
            'Calmar Ratio': f"{plat_winner_full['calmar_ratio']:.2f}"
        },
        {
            'Configuration': f"Global Optimum Overall ({int(global_opt['period'])}, {global_opt['mult']:.1f} {global_opt['method']} {global_opt['source']})",
            'Net Points': f"{global_opt['net_pts']:+.1f} pts",
            'Net USD': f"${global_opt['net_usd']:+.2f}",
            'Profit Factor': f"{global_opt['pf']:.3f}",
            'Trades': f"{int(global_opt['trades'])}",
            'Win Rate': f"{global_opt['win_rate']:.1f}%",
            'Max Drawdown': f"{global_opt['max_dd_pts']:.1f} pts (${global_opt['max_dd_usd']:.2f})",
            'Calmar Ratio': f"{global_opt['calmar_ratio']:.2f}"
        }
    ]

    comp_df = pd.DataFrame(comparison_data)
    print(comp_df.to_string(index=False))

    # Save detailed JSON summary
    summary_out = {
        'total_combinations_tested': len(df),
        'global_optimum': global_opt.to_dict(),
        'plateau_winner': plat_winner_full.to_dict(),
        'default_1_pure': def1_pure.to_dict(),
        'default_1_best_v4': def1_best_v4.to_dict(),
        'default_2_pure': def2_pure.to_dict(),
        'default_2_best_v4': def2_best_v4.to_dict(),
        'top_10_by_net_pts': top_pnl.to_dict(orient='records'),
        'top_10_by_calmar': top_calmar.to_dict(orient='records'),
        'top_10_plateaus': top_plateaus.to_dict(orient='records')
    }

    with open('optimization_summary.json', 'w') as f:
        json.dump(summary_out, f, indent=2)
    print("\nSaved optimization_summary.json successfully.")

if __name__ == '__main__':
    run_analysis()
