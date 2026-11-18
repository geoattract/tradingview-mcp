import json
from datetime import datetime, timezone, timedelta

with open('/Users/melvin/.gemini/antigravity/brain/71dab95d-dfed-40d5-b5f4-dcdc835396d8/.system_generated/steps/161/output.txt') as f:
    raw = json.load(f)

bars = raw['result']['bars']
sgt_tz = timezone(timedelta(hours=8))

for b in bars:
    dt_utc = datetime.fromtimestamp(b['time'], tz=timezone.utc)
    dt_sgt = dt_utc.astimezone(sgt_tz)
    b['time_sgt_str'] = dt_sgt.strftime('%Y-%m-%d %H:%M')
    b['time_only'] = dt_sgt.strftime('%H:%M')

bars_by_idx = {b['index']: b for b in bars}

# 1. Check the 07:50 SGT BUY trade
print("=== CHECKING 07:50 SGT BUY SIGNAL (Bar 100) ===")
for idx in range(100, 115):
    b = bars_by_idx[idx]
    labels = [l['text'] for l in b['crsiLabels']]
    alerts = []
    if b['crsiHookDown']: alerts.append("ALERT_DN")
    if b['crsiHookUp']: alerts.append("ALERT_UP")
    print(f"{b['index']} | {b['time_only']} | C={b['close']:.2f} | Labels={labels} | Alerts={alerts}")

# 2. Check Trade 1: SELL at 11:55 SGT (Bar 149)
print("\n=== CHECKING 11:55 SGT SELL SIGNAL (Bar 149) ===")
for idx in range(149, 160):
    b = bars_by_idx[idx]
    labels = [l['text'] for l in b['crsiLabels']]
    alerts = []
    if b['crsiHookDown']: alerts.append("ALERT_DN")
    if b['crsiHookUp']: alerts.append("ALERT_UP")
    print(f"{b['index']} | {b['time_only']} | C={b['close']:.2f} | Labels={labels} | Alerts={alerts}")

# 3. Check Trade 2: BUY at 15:05 SGT (Bar 187)
print("\n=== CHECKING 15:05 SGT BUY SIGNAL (Bar 187) ===")
for idx in range(187, 203):
    b = bars_by_idx[idx]
    labels = [l['text'] for l in b['crsiLabels']]
    alerts = []
    if b['crsiHookDown']: alerts.append("ALERT_DN")
    if b['crsiHookUp']: alerts.append("ALERT_UP")
    print(f"{b['index']} | {b['time_only']} | C={b['close']:.2f} | Labels={labels} | Alerts={alerts}")

# 4. Check Trade 3: SELL at 16:15 SGT (Bar 201)
print("\n=== CHECKING 16:15 SGT SELL SIGNAL (Bar 201) ===")
for idx in range(201, 225):
    b = bars_by_idx[idx]
    labels = [l['text'] for l in b['crsiLabels']]
    alerts = []
    if b['crsiHookDown']: alerts.append("ALERT_DN")
    if b['crsiHookUp']: alerts.append("ALERT_UP")
    print(f"{b['index']} | {b['time_only']} | C={b['close']:.2f} | Labels={labels} | Alerts={alerts}")
