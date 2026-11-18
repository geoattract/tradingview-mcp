import json
from datetime import datetime, timezone, timedelta

# Load MGC data
with open('/Users/melvin/.gemini/antigravity/brain/71dab95d-dfed-40d5-b5f4-dcdc835396d8/.system_generated/steps/110/output.txt') as f:
    raw = json.load(f)

bars = raw['result']['bars']
sgt_tz = timezone(timedelta(hours=8))

for b in bars:
    dt_utc = datetime.fromtimestamp(b['time'], tz=timezone.utc)
    dt_sgt = dt_utc.astimezone(sgt_tz)
    b['time_sgt_str'] = dt_sgt.strftime('%Y-%m-%d %H:%M')
    b['time_only'] = dt_sgt.strftime('%H:%M')

bars_by_idx = {b['index']: b for b in bars}

def inspect_trade_path(start_idx, trade_type, max_bars=60):
    print(f"\n=======================================================")
    print(f"TRACKING {trade_type} FROM BAR {start_idx} ({bars_by_idx[start_idx]['time_only']} SGT)")
    print(f"Entry Close: {bars_by_idx[start_idx]['close']}")
    print(f"=======================================================")
    
    opp_arrow = '▼' if 'BUY' in trade_type else '▲'
    same_arrow = '▲' if 'BUY' in trade_type else '▼'
    opp_st = 'SELL' if 'BUY' in trade_type else 'BUY'
    
    curl_events = []
    
    in_opp_cluster = False
    
    for i in range(start_idx + 1, start_idx + max_bars):
        if i not in bars_by_idx: break
        b = bars_by_idx[i]
        
        has_opp_label = any(l['text'] == opp_arrow for l in b['crsiLabels'])
        has_same_label = any(l['text'] == same_arrow for l in b['crsiLabels'])
        
        st_event = None
        if b['buyBadge']: st_event = 'BUY'
        if b['sellBadge']: st_event = 'SELL'
        
        # Check if new reversal curl event (or cluster)
        if has_opp_label:
            curl_events.append({
                'idx': i,
                'time': b['time_only'],
                'close': b['close'],
                'type': f"Reversal Curl {opp_arrow}"
            })
            
        print(f"Bar {b['index']:3d} | {b['time_only']} | C={b['close']:7.1f} | ST={str(st_event):5s} | Labels={[l['text'] for l in b['crsiLabels']]} | Alerts: dn={b['crsiHookDown']}, up={b['crsiHookUp']}")
        
        if st_event == opp_st:
            print(f"--> OPPOSITE SUPERTREND LABEL HIT AT BAR {b['index']} ({b['time_only']}) @ {b['close']}")
            break

# Inspect Trade 1: BUY at bar 124 (09:35)
inspect_trade_path(124, "BUY", 35)

# Inspect Trade 2: SELL at bar 156 (12:15)
inspect_trade_path(156, "SELL", 30)

# Inspect Trade 3: BUY at bar 164 (12:55)
inspect_trade_path(164, "BUY", 30)

# Inspect Trade 4: SELL at bar 179 (14:10)
inspect_trade_path(179, "SELL", 70)
