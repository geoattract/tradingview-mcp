import json

with open('optimization_summary.json') as f:
    d = json.load(f)

print('=== TOP 10 BY NET P&L ===')
for i, r in enumerate(d['top_10_by_net_pts'][:10]):
    print(f"#{i+1:2d}: Net +{r['net_pts']:7.1f} pts (${r['net_usd']:8.2f}) | PF {r['pf']:.3f} | WR {r['win_rate']:.1f}% | DD {r['max_dd_pts']:6.1f} pts | Calmar {r['calmar_ratio']:4.2f} | Trades {int(r['trades'])} | ST: ({int(r['period'])}, {r['mult']}, {r['method']}, {r['source']}) | Zone: {r['zone_mode']} | RSI_L: {int(r['rsi_len'])} | Candle: {bool(r['req_candle'])} | CD: {int(r['cooldown'])} | Dots: ({r['dot_os']}/{r['dot_ob']})")

print('\n=== TOP 10 BY CALMAR RATIO (TRADES >= 100) ===')
for i, r in enumerate(d['top_10_by_calmar'][:10]):
    print(f"#{i+1:2d}: Calmar {r['calmar_ratio']:4.2f} | Net +{r['net_pts']:7.1f} pts (${r['net_usd']:8.2f}) | PF {r['pf']:.3f} | WR {r['win_rate']:.1f}% | DD {r['max_dd_pts']:6.1f} pts | Trades {int(r['trades'])} | ST: ({int(r['period'])}, {r['mult']}, {r['method']}, {r['source']}) | Zone: {r['zone_mode']} | RSI_L: {int(r['rsi_len'])} | Candle: {bool(r['req_candle'])} | CD: {int(r['cooldown'])} | Dots: ({r['dot_os']}/{r['dot_ob']})")
