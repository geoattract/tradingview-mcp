import json
import pandas as pd
import numpy as np
import sys
sys.path.append('/Users/melvin/Documents/IDE-VS Code/tradingview-mcp/tests')
import risk_expectancy_modeling as rem
import run_risk_analysis as rra

t5, o5, h5, l5, c5, v5 = rem.load_data('mnq_5m_data.csv')
t2, o2, h2, l2, c2, v2 = rem.load_data('mnq_2m_data.csv')
oct25 = t2[0]

# Run 5m Overlap Pullback + TP Dot
trades = rra.run_strategy_simulation(t5, o5, h5, l5, c5, 'PULLBACK', 80, 1.4, 'SMA', pb_mode='ALL', use_tp_dots=True, filter_start_time=oct25)
df = pd.DataFrame(trades)
df['dt'] = pd.to_datetime(df['entry_time'], unit='s', utc=True)
df['hour'] = df['dt'].dt.hour

def get_session(hour):
    if 0 <= hour < 7: return 'Asia (00-07 UTC)'
    elif 7 <= hour < 13: return 'London (07-13 UTC)'
    elif 13 <= hour < 21: return 'US RTH (13-21 UTC)'
    else: return 'Post-US (21-24 UTC)'

df['session'] = df['hour'].apply(get_session)

print('=== LONG VS SHORT BREAKDOWN (5m Pullback + TP Dot, Oct25-Nov16) ===')
for d, name in [(1, 'Long'), (-1, 'Short')]:
    sub = df[df['dir'] == d]
    wins = sub[sub['net_usd'] > 0]
    wr = len(wins) / len(sub) * 100 if len(sub) > 0 else 0
    net = sub['net_usd'].sum()
    gross_win = wins['net_usd'].sum()
    gross_loss = abs(sub[sub['net_usd'] < 0]['net_usd'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    print(f"{name:<6} | Trades: {len(sub):>2} | Win Rate: {wr:>5.1f}% | Net: ${net:>8.2f} | PF: {pf:>4.2f}")

print('\n=== SESSION BREAKDOWN (5m Pullback + TP Dot, Oct25-Nov16) ===')
for sess in ['Asia (00-07 UTC)', 'London (07-13 UTC)', 'US RTH (13-21 UTC)', 'Post-US (21-24 UTC)']:
    sub = df[df['session'] == sess]
    if len(sub) == 0: continue
    wins = sub[sub['net_usd'] > 0]
    wr = len(wins) / len(sub) * 100 if len(sub) > 0 else 0
    net = sub['net_usd'].sum()
    gross_win = wins['net_usd'].sum()
    gross_loss = abs(sub[sub['net_usd'] < 0]['net_usd'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    print(f"{sess:<20} | Trades: {len(sub):>2} | Win Rate: {wr:>5.1f}% | Net: ${net:>8.2f} | PF: {pf:>4.2f}")
