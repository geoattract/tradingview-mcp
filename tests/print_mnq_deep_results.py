import json

# Let's run a quick query on all 288 runs
from optimize_mnq1_5m_supertrend import run_supertrend_sim

with open('data_mnq1_5m_live.json') as f:
    bars = json.load(f)

periods = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20]
multipliers = [1.5, 1.8, 2.0, 2.2, 2.4, 2.5, 2.6, 2.8, 3.0, 3.2, 3.5, 4.0]
methods = ["RMA (Wilder)", "SMA"]

results = []
for m in methods:
    for p in periods:
        for mult in multipliers:
            res = run_supertrend_sim(bars, p, mult, m)
            if res:
                results.append(res)

rma_results = [r for r in results if r['atr_method'] == 'RMA (Wilder)']
sma_results = [r for r in results if r['atr_method'] == 'SMA']

rma_by_profit = sorted(rma_results, key=lambda x: x['net_profit_usd'], reverse=True)
rma_by_pf = sorted([r for r in rma_results if r['total_trades'] >= 20], key=lambda x: x['profit_factor'], reverse=True)

print("=== TOP 5 RMA (WILDER) BY PROFIT FACTOR ===")
for i, r in enumerate(rma_by_pf[:5]):
    print(f"#{i+1}: ATR {r['atr_period']}, Mult {r['multiplier']} | PF: {r['profit_factor']} | Net: ${r['net_profit_usd']} (+{r['net_profit_pts']} pts) | WR: {r['win_rate_pct']}% | Trades: {r['total_trades']} | MaxDD: ${r['max_drawdown_usd']} | Avg: +${r['avg_trade_usd']}")

print("\n=== TOP 5 RMA (WILDER) BY NET PROFIT ===")
for i, r in enumerate(rma_by_profit[:5]):
    print(f"#{i+1}: ATR {r['atr_period']}, Mult {r['multiplier']} | Net: ${r['net_profit_usd']} (+{r['net_profit_pts']} pts) | PF: {r['profit_factor']} | WR: {r['win_rate_pct']}% | Trades: {r['total_trades']} | MaxDD: ${r['max_drawdown_usd']} | Avg: +${r['avg_trade_usd']}")

sma_by_profit = sorted(sma_results, key=lambda x: x['net_profit_usd'], reverse=True)
sma_by_pf = sorted([r for r in sma_results if r['total_trades'] >= 20], key=lambda x: x['profit_factor'], reverse=True)

print("\n=== TOP 5 SMA BY PROFIT FACTOR ===")
for i, r in enumerate(sma_by_pf[:5]):
    print(f"#{i+1}: ATR {r['atr_period']}, Mult {r['multiplier']} | PF: {r['profit_factor']} | Net: ${r['net_profit_usd']} (+{r['net_profit_pts']} pts) | WR: {r['win_rate_pct']}% | Trades: {r['total_trades']} | MaxDD: ${r['max_drawdown_usd']} | Avg: +${r['avg_trade_usd']}")
