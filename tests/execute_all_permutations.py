#!/usr/bin/env python3
"""
execute_all_permutations.py
Executes all candidate Supertrend V4 + RSI permutations, computes full metrics,
and runs Position Sizing & Monte Carlo Ruin / Breach modeling.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

sys.path.append('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests')
import risk_expectancy_modeling as rem
import run_risk_analysis as rra

def main():
    print("================================================================================")
    print("  COMPREHENSIVE RISK, DRAWDOWN, EXPECTANCY & FRICTION AUDIT: SUPERTREND V4 + RSI")
    print("================================================================================")
    
    # Load 5m and 2m data
    t5, o5, h5, l5, c5, v5 = rem.load_data('mnq_5m_data.csv')
    t2, o2, h2, l2, c2, v2 = rem.load_data('mnq_2m_data.csv')
    
    oct25_start_time = t2[0] # Overlap start timestamp (2026-10-25 22:00:00 UTC)
    
    print(f"5m Data: {len(c5)} bars | Start: {datetime.fromtimestamp(t5[0], tz=timezone.utc)} | End: {datetime.fromtimestamp(t5[-1], tz=timezone.utc)}")
    print(f"2m Data: {len(c2)} bars | Start: {datetime.fromtimestamp(t2[0], tz=timezone.utc)} | End: {datetime.fromtimestamp(t2[-1], tz=timezone.utc)}")
    print(f"Common Overlap Start: {datetime.fromtimestamp(oct25_start_time, tz=timezone.utc)}")
    print("--------------------------------------------------------------------------------\n")
    
    # Define candidate permutations
    configs = [
        # --- 5M FULL DATASET PERMUTATIONS ---
        {
            'name': '1. 5m Pure Flip (Baseline 10/3.0 RMA)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PURE_FLIP',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'filter_time': None
        },
        {
            'name': '2. 5m Pure Flip (MNQ Preset 80/1.4 SMA)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PURE_FLIP',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'filter_time': None
        },
        {
            'name': '3. 5m Flip + Early TP Dot (10/3.0 RMA)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'FLIP_WITH_TP_DOT',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'filter_time': None
        },
        {
            'name': '4. 5m Flip + Early TP Dot (80/1.4 SMA)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'FLIP_WITH_TP_DOT',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'filter_time': None
        },
        {
            'name': '5. 5m Pullback All Waves (80/1.4 SMA + ST Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': False,
            'filter_time': None
        },
        {
            'name': '6. 5m Pullback 1st Wave Only (80/1.4 SMA + ST Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'FIRST', 'pb_zone': (30.0, 70.0), 'use_tp_dots': False,
            'filter_time': None
        },
        {
            'name': '7. 5m Pullback All Waves (80/1.4 SMA + TP Dot Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': True,
            'filter_time': None
        },
        {
            'name': '8. 5m Pullback All Waves (10/3.0 RMA + ST Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': False,
            'filter_time': None
        },
        {
            'name': '9. 5m Pullback 1st Wave Only (10/3.0 RMA + ST Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'pb_mode': 'FIRST', 'pb_zone': (30.0, 70.0), 'use_tp_dots': False,
            'filter_time': None
        },
        {
            'name': '10. 5m Pullback All Waves (10/3.0 RMA + TP Dot Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': True,
            'filter_time': None
        },
        {
            'name': '11. 5m RSI Purple Dip (80/1.4 SMA + ST Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PURPLE_DIP',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'use_tp_dots': False,
            'filter_time': None
        },
        {
            'name': '12. 5m RSI Purple Dip (80/1.4 SMA + TP Dot Exit)',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PURPLE_DIP',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'use_tp_dots': True,
            'filter_time': None
        },
        
        # --- 2M FULL DATASET PERMUTATIONS (Oct 25 to Nov 16) ---
        {
            'name': '13. 2m Pure Flip (Baseline 10/3.0 RMA)',
            'data': (t2, o2, h2, l2, c2),
            'strat': 'PURE_FLIP',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'filter_time': None
        },
        {
            'name': '14. 2m Pure Flip (MNQ Preset 80/1.4 SMA)',
            'data': (t2, o2, h2, l2, c2),
            'strat': 'PURE_FLIP',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'filter_time': None
        },
        {
            'name': '15. 2m Pullback All Waves (80/1.4 SMA + ST Exit)',
            'data': (t2, o2, h2, l2, c2),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': False,
            'filter_time': None
        },
        {
            'name': '16. 2m Pullback All Waves (80/1.4 SMA + TP Dot Exit)',
            'data': (t2, o2, h2, l2, c2),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': True,
            'filter_time': None
        },

        # --- 5M OVERLAPPING DATASET PERMUTATIONS (Oct 25 to Nov 16) ---
        {
            'name': '17. 5m Overlap Pure Flip (10/3.0 RMA) [Oct25-Nov16]',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PURE_FLIP',
            'st_len': 10, 'st_mult': 3.0, 'st_meth': 'RMA',
            'filter_time': oct25_start_time
        },
        {
            'name': '18. 5m Overlap Pure Flip (80/1.4 SMA) [Oct25-Nov16]',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PURE_FLIP',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'filter_time': oct25_start_time
        },
        {
            'name': '19. 5m Overlap Pullback All (80/1.4 SMA) [Oct25-Nov16]',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': False,
            'filter_time': oct25_start_time
        },
        {
            'name': '20. 5m Overlap Pullback + TP Dot (80/1.4 SMA) [Oct25-Nov16]',
            'data': (t5, o5, h5, l5, c5),
            'strat': 'PULLBACK',
            'st_len': 80, 'st_mult': 1.4, 'st_meth': 'SMA',
            'pb_mode': 'ALL', 'pb_zone': (30.0, 70.0), 'use_tp_dots': True,
            'filter_time': oct25_start_time
        }
    ]

    all_metrics = []
    all_trade_logs = {}

    for cfg in configs:
        times, opens, highs, lows, closes = cfg['data']
        trades = rra.run_strategy_simulation(
            times, opens, highs, lows, closes,
            strategy_type=cfg['strat'],
            st_len=cfg.get('st_len', 80),
            st_mult=cfg.get('st_mult', 1.4),
            st_meth=cfg.get('st_meth', 'SMA'),
            pb_mode=cfg.get('pb_mode', 'ALL'),
            pb_zone=cfg.get('pb_zone', (30.0, 70.0)),
            use_tp_dots=cfg.get('use_tp_dots', False),
            filter_start_time=cfg.get('filter_time', None)
        )
        
        metrics = rra.compute_comprehensive_metrics(trades, times, cfg['name'])
        all_metrics.append(metrics)
        all_trade_logs[cfg['name']] = trades
        
        print(f"Finished: {cfg['name']} -> {metrics['total_trades']} trades | Net: ${metrics['net_profit_usd']:,.2f} | PF: {metrics['net_pf']:.2f} | MaxDD: ${metrics['max_dd_usd']:,.2f} | WR: {metrics['win_rate']:.1f}%")

    # Save metrics to JSON for analysis
    with open('tests/candidate_permutations_metrics.json', 'w') as f:
        # Convert non-serializable objects
        clean_metrics = []
        for m in all_metrics:
            c = {}
            for k, v in m.items():
                if isinstance(v, (np.integer, int)):
                    c[k] = int(v)
                elif isinstance(v, (np.floating, float)):
                    c[k] = float(v)
                else:
                    c[k] = v
            clean_metrics.append(c)
        json.dump(clean_metrics, f, indent=2)

    print("\nAll simulations completed and saved to candidate_permutations_metrics.json.")

if __name__ == '__main__':
    main()
