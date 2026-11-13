import json
from optimize_mes1_5m_supertrend import run_supertrend_sim

with open('data_mes1_5m.json') as f:
    bars = json.load(f)

sources = ['hl2', 'close', 'hlc3', 'ohlc4']

candidates = [
    {"name": "Optimal SMA (12, 3.0)", "p": 12, "m": 3.0, "method": "SMA"},
    {"name": "Cluster SMA (13, 3.2)", "p": 13, "m": 3.2, "method": "SMA"},
    {"name": "Optimal RMA (8, 3.5)", "p": 8, "m": 3.5, "method": "RMA (Wilder)"},
    {"name": "Optimal RMA (7, 3.5)", "p": 7, "m": 3.5, "method": "RMA (Wilder)"},
    {"name": "Default RMA (10, 3.0)", "p": 10, "m": 3.0, "method": "RMA (Wilder)"},
]

print("================================================================================")
print("SOURCE PRICE SENSITIVITY TEST ON MES1! (5m)")
print("================================================================================")

for c in candidates:
    print(f"\n--- Candidate: {c['name']} ---")
    for src in sources:
        res = run_supertrend_sim(bars, c['p'], c['m'], c['method'], src)
        print(f"Source: {src:6s} | Net Profit: ${res['net_profit_usd']:8.2f} (+{res['net_profit_pts']:6.2f} pts) | PF: {res['profit_factor']:5.3f} | WR: {res['win_rate_pct']:5.2f}% | Trades: {res['total_trades']:2d} | MaxDD: ${res['max_drawdown_usd']:6.2f} | Avg: +${res['avg_trade_usd']:5.2f}")
