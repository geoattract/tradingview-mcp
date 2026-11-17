import pandas as pd
import numpy as np

df = pd.read_csv('grid_search_results.csv')

# 1. 2D Heatmap: ATR Period vs Multiplier for Net PnL (Averaged across all RSI/Dot configs)
print("=== 2D HEATMAP: ATR PERIOD vs MULTIPLIER (Mean Net Points P&L) ===")
pivot_net = df.pivot_table(index='period', columns='mult', values='net_pts', aggfunc='mean').round(1)
print(pivot_net)

print("\n=== 2D HEATMAP: ATR PERIOD vs MULTIPLIER (Mean Profit Factor) ===")
pivot_pf = df.pivot_table(index='period', columns='mult', values='pf', aggfunc='mean').round(3)
print(pivot_pf)

print("\n=== 2D HEATMAP: ATR PERIOD vs MULTIPLIER (Mean Max Drawdown in Pts) ===")
pivot_dd = df.pivot_table(index='period', columns='mult', values='max_dd_pts', aggfunc='mean').round(1)
print(pivot_dd)

print("\n=== 2D HEATMAP: ATR PERIOD vs MULTIPLIER (Mean Calmar Ratio = Net/MaxDD) ===")
pivot_calmar = df.pivot_table(index='period', columns='mult', values='net_pts', aggfunc=lambda x: np.mean(x) / np.mean(df.loc[x.index, 'max_dd_pts'])).round(2)
print(pivot_calmar)

# 2. Check the (80, 1.8) and (10, 1.8) slices
print("\n=== DETAILED SLICE: MULTIPLIER 1.8 ACROSS ATR PERIODS ===")
slice_18 = df[df['mult'] == 1.8].groupby('period').agg(
    Mean_Net_Pts=('net_pts', 'mean'),
    Max_Net_Pts=('net_pts', 'max'),
    Mean_PF=('pf', 'mean'),
    Max_PF=('pf', 'max'),
    Mean_DD=('max_dd_pts', 'mean'),
    Min_DD=('max_dd_pts', 'min'),
    Mean_Trades=('trades', 'mean')
).round(2)
print(slice_18)

# 3. Check Smoothing Method x Source Breakdown
print("\n=== METHOD x SOURCE BREAKDOWN ===")
met_src = df.groupby(['method', 'source']).agg(
    Mean_Net_Pts=('net_pts', 'mean'),
    Mean_PF=('pf', 'mean'),
    Mean_DD=('max_dd_pts', 'mean'),
    Calmar=('net_pts', lambda x: np.mean(x) / np.mean(df.loc[x.index, 'max_dd_pts']))
).round(2)
print(met_src)

# 4. Check Stoch RSI Zone Mode x Dot Levels Breakdown
print("\n=== ZONE MODE x EARLY DOT LEVELS BREAKDOWN ===")
df['dot_pair'] = df['dot_os'].astype(str) + " / " + df['dot_ob'].astype(str)
zone_dot = df.groupby(['zone_mode', 'dot_pair']).agg(
    Mean_Net_Pts=('net_pts', 'mean'),
    Mean_PF=('pf', 'mean'),
    Mean_DD=('max_dd_pts', 'mean'),
    Calmar=('net_pts', lambda x: np.mean(x) / np.mean(df.loc[x.index, 'max_dd_pts']))
).round(2)
print(zone_dot)
