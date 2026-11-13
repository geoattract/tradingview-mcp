import json

with open('mes1_5m_optimization_results.json') as f:
    results = json.load(f)

rma_results = [r for r in results if r['atr_method'] == 'RMA (Wilder)']
sma_results = [r for r in results if r['atr_method'] == 'SMA']

# Sorts
rma_by_profit = sorted(rma_results, key=lambda x: x['net_profit_usd'], reverse=True)
rma_by_pf = sorted([r for r in rma_results if r['total_trades'] >= 20], key=lambda x: x['profit_factor'], reverse=True)

sma_by_profit = sorted(sma_results, key=lambda x: x['net_profit_usd'], reverse=True)
sma_by_pf = sorted([r for r in sma_results if r['total_trades'] >= 20], key=lambda x: x['profit_factor'], reverse=True)

print("================================================================================")
print("TOP 10 RMA (WILDER) BY NET PROFIT")
print("================================================================================")
for i, r in enumerate(rma_by_profit[:10]):
    print(f"#{i+1:2d}: ATR {r['atr_period']:2d}, Mult {r['multiplier']:3.1f} | Net: ${r['net_profit_usd']:8.2f} (+{r['net_profit_pts']:6.2f} pts) | PF: {r['profit_factor']:5.3f} | WR: {r['win_rate_pct']:5.2f}% | Trades: {r['total_trades']:2d} | MaxDD: ${r['max_drawdown_usd']:6.2f} | Avg: +${r['avg_trade_usd']:5.2f}")

print("\n================================================================================")
print("TOP 10 RMA (WILDER) BY PROFIT FACTOR (Trades >= 20)")
print("================================================================================")
for i, r in enumerate(rma_by_pf[:10]):
    print(f"#{i+1:2d}: ATR {r['atr_period']:2d}, Mult {r['multiplier']:3.1f} | PF: {r['profit_factor']:5.3f} | Net: ${r['net_profit_usd']:8.2f} (+{r['net_profit_pts']:6.2f} pts) | WR: {r['win_rate_pct']:5.2f}% | Trades: {r['total_trades']:2d} | MaxDD: ${r['max_drawdown_usd']:6.2f} | Avg: +${r['avg_trade_usd']:5.2f}")

print("\n================================================================================")
print("TOP 10 SMA BY NET PROFIT")
print("================================================================================")
for i, r in enumerate(sma_by_profit[:10]):
    print(f"#{i+1:2d}: ATR {r['atr_period']:2d}, Mult {r['multiplier']:3.1f} | Net: ${r['net_profit_usd']:8.2f} (+{r['net_profit_pts']:6.2f} pts) | PF: {r['profit_factor']:5.3f} | WR: {r['win_rate_pct']:5.2f}% | Trades: {r['total_trades']:2d} | MaxDD: ${r['max_drawdown_usd']:6.2f} | Avg: +${r['avg_trade_usd']:5.2f}")

print("\n================================================================================")
print("TOP 10 SMA BY PROFIT FACTOR (Trades >= 20)")
print("================================================================================")
for i, r in enumerate(sma_by_pf[:10]):
    print(f"#{i+1:2d}: ATR {r['atr_period']:2d}, Mult {r['multiplier']:3.1f} | PF: {r['profit_factor']:5.3f} | Net: ${r['net_profit_usd']:8.2f} (+{r['net_profit_pts']:6.2f} pts) | WR: {r['win_rate_pct']:5.2f}% | Trades: {r['total_trades']:2d} | MaxDD: ${r['max_drawdown_usd']:6.2f} | Avg: +${r['avg_trade_usd']:5.2f}")
