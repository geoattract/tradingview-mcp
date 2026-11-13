import json

with open('mgc1_5m_optimization_results.json') as f:
    data = json.load(f)

print('=== BASELINE 10, 3.0 RMA ===')
print(json.dumps(data['baseline_10_3_rma'], indent=2))

print('\n=== TOP 10 BY NET PROFIT ===')
for i, r in enumerate(data['top_10_by_net_profit'][:10]):
    print(f"#{i+1}: ATR {r['atr_period']}, Mult {r['multiplier']}, {r['atr_method']} | Net: ${r['net_profit_usd']} (+{r['net_profit_pts']} pts) | PF: {r['profit_factor']} | WR: {r['win_rate_pct']}% | Trades: {r['total_trades']} | MaxDD: ${r['max_drawdown_usd']}")

print('\n=== TOP 10 BY PROFIT FACTOR (>=20 trades) ===')
for i, r in enumerate(data['top_10_by_profit_factor'][:10]):
    print(f"#{i+1}: ATR {r['atr_period']}, Mult {r['multiplier']}, {r['atr_method']} | PF: {r['profit_factor']} | Net: ${r['net_profit_usd']} (+{r['net_profit_pts']} pts) | WR: {r['win_rate_pct']}% | Trades: {r['total_trades']} | MaxDD: ${r['max_drawdown_usd']}")
