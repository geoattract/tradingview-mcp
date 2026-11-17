import json
from datetime import datetime, timezone, timedelta

with open('/Users/melvin/.gemini/antigravity/brain/71dab95d-dfed-40d5-b5f4-dcdc835396d8/.system_generated/steps/110/output.txt') as f:
    raw = json.load(f)

bars = raw['result']['bars']
sgt_tz = timezone(timedelta(hours=8))

for b in bars:
    dt_utc = datetime.fromtimestamp(b['time'], tz=timezone.utc)
    dt_sgt = dt_utc.astimezone(sgt_tz)
    b['time_sgt_str'] = dt_sgt.strftime('%Y-%m-%d %H:%M')
    b['time_only'] = dt_sgt.strftime('%H:%M')

# Let's inspect each bar from 09:00 SGT to end of data
bars_window = [b for b in bars if b['time_sgt_str'] >= '2026-11-17 09:00']

print("Index | Time SGT |   Open   |   High   |   Low    |  Close   | SuperTrend | cRSI Triangles / Alerts")
print("-" * 90)

for b in bars_window:
    st_sig = []
    if b['buyBadge']: st_sig.append("BUY")
    if b['sellBadge']: st_sig.append("SELL")
    
    crsi_sig = []
    if b['crsiHookDown']: crsi_sig.append("ALERT_HOOK_DN")
    if b['crsiHookUp']: crsi_sig.append("ALERT_HOOK_UP")
    for l in b['crsiLabels']:
        crsi_sig.append(f"LABEL_{l['text']}")
        
    if st_sig or crsi_sig:
        print(f"{b['index']:5d} | {b['time_sgt_str']} | {b['open']:8.1f} | {b['high']:8.1f} | {b['low']:8.1f} | {b['close']:8.1f} | {', '.join(st_sig):10s} | {', '.join(crsi_sig)}")
