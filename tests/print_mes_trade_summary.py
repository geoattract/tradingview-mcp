import json
from optimize_mes1_5m_supertrend import run_supertrend_sim

with open('data_mes1_5m.json') as f:
    bars = json.load(f)

# Run optimal
opt = run_supertrend_sim(bars, 12, 3.0, "SMA", "hl2")
base = run_supertrend_sim(bars, 10, 3.0, "RMA (Wilder)", "hl2")
rma_opt = run_supertrend_sim(bars, 8, 3.5, "RMA (Wilder)", "hl2")

print("=== MES1! 5-MINUTE BACKTEST PERFORMANCE COMPARISON ===")
print("Data Range: 02 Nov 2026 00:00 UTC to 12 Nov 2026 03:45 UTC (2,254 bars)")
print("Contract: CME Micro E-mini S&P 500 ($5/pt, 0.25 tick, $3.90 friction)")
print()
print(f"{'Metric':<25} | {'Default (10, 3.0 RMA)':<22} | {'Optimal RMA (8, 3.5 RMA)':<24} | {'Optimal SMA (12, 3.0 SMA)':<24}")
print("-" * 105)
print(f"{'Net Profit ($)':<25} | ${base['net_profit_usd']:<21.2f} | ${rma_opt['net_profit_usd']:<23.2f} | ${opt['net_profit_usd']:<23.2f}")
print(f"{'Net Profit (Points)':<25} | +{base['net_profit_pts']:<20.2f} pts | +{rma_opt['net_profit_pts']:<22.2f} pts | +{opt['net_profit_pts']:<22.2f} pts")
print(f"{'Profit Factor':<25} | {base['profit_factor']:<22.3f} | {rma_opt['profit_factor']:<24.3f} | {opt['profit_factor']:<24.3f}")
print(f"{'Win Rate (%)':<25} | {base['win_rate_pct']:<21.2f}% | {rma_opt['win_rate_pct']:<23.2f}% | {opt['win_rate_pct']:<23.2f}%")
print(f"{'Total Trades':<25} | {base['total_trades']:<22} | {rma_opt['total_trades']:<24} | {opt['total_trades']:<24}")
print(f"{'Winning Trades':<25} | {base['wins']:<22} | {rma_opt['wins']:<24} | {opt['wins']:<24}")
print(f"{'Losing Trades':<25} | {base['losses']:<22} | {rma_opt['losses']:<24} | {opt['losses']:<24}")
print(f"{'Max Drawdown ($)':<25} | ${base['max_drawdown_usd']:<21.2f} | ${rma_opt['max_drawdown_usd']:<23.2f} | ${opt['max_drawdown_usd']:<23.2f}")
print(f"{'Max Drawdown (Points)':<25} | {base['max_drawdown_pts']:<21.2f} pts | {rma_opt['max_drawdown_pts']:<23.2f} pts | {opt['max_drawdown_pts']:<23.2f} pts")
print(f"{'Average Trade ($)':<25} | +${base['avg_trade_usd']:<20.2f} | +${rma_opt['avg_trade_usd']:<22.2f} | +${opt['avg_trade_usd']:<22.2f}")
print(f"{'Average Trade (Points)':<25} | +{base['avg_trade_pts']:<20.2f} pts | +{rma_opt['avg_trade_pts']:<22.2f} pts | +{opt['avg_trade_pts']:<22.2f} pts")
print(f"{'Payoff Ratio (Win/Loss)':<25} | {base['payoff_ratio']:<22.2f} | {rma_opt['payoff_ratio']:<24.2f} | {opt['payoff_ratio']:<24.2f}")
