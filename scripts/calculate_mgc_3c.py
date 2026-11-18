import json

# Data points derived from exact bar indices
# Trade 1: Entry BUY at 09:35 (bar 124) @ 3860.7
# C1: 1st curl down @ bar 128 (09:55) = 3868.7 (+8.0 pts)
# C2: 2nd curl down @ bar 135 (10:30) = 3868.0 (+7.3 pts)
# C3: SuperTrend SELL @ bar 156 (12:15) = 3869.4 (+8.7 pts)

# Trade 2: Entry SELL at 12:15 (bar 156) @ 3869.4
# C1: 1st curl up @ bar 162 (12:45) = 3876.6 (-7.2 pts)
# C2 & C3: SuperTrend BUY @ bar 164 (12:55) = 3877.5 (-8.1 pts each) (hit before 2nd curl)

# Trade 3: Entry BUY at 12:55 (bar 164) @ 3877.5
# C1: 1st curl down @ bar 171 (13:30) = 3888.8 (+11.3 pts)
# C2: 2nd curl down @ bar 178 (14:05) = 3878.5 (+1.0 pt)
# C3: SuperTrend SELL @ bar 179 (14:10) = 3877.1 (-0.4 pts)

# Trade 4: Entry SELL at 14:10 (bar 179) @ 3877.1
# C1: 1st curl up @ bar 182 (14:25) = 3878.4 (-1.3 pts)
# C2: 2nd curl up @ bar 199 (15:50) = 3875.8 (+1.3 pts)
# C3: SuperTrend BUY @ bar 243 (19:30) = 3864.6 (+12.5 pts) (or if session closed around 17:00 at 3871.4 = +5.7 pts)

scenarios = {
    "Split Scaling (1st Curl, 2nd Curl, SuperTrend Flip)": {
        "T1": [8.0, 7.3, 8.7],
        "T2": [-7.2, -8.1, -8.1],
        "T3": [11.3, 1.0, -0.4],
        "T4": [-1.3, 1.3, 12.5], # holding to ST flip at 19:30
    },
    "Both Remaining Contracts Exit on 2nd Curl (or ST Flip if earlier)": {
        "T1": [8.0, 7.3, 7.3],
        "T2": [-7.2, -8.1, -8.1],
        "T3": [11.3, 1.0, 1.0],
        "T4": [-1.3, 1.3, 1.3],
    },
    "Both Remaining Contracts Hold to Next SuperTrend Flip": {
        "T1": [8.0, 8.7, 8.7],
        "T2": [-7.2, -8.1, -8.1],
        "T3": [11.3, -0.4, -0.4],
        "T4": [-1.3, 12.5, 12.5],
    }
}

for name, s in scenarios.items():
    print(f"\n=======================================================")
    print(f"SCENARIO: {name}")
    print(f"=======================================================")
    grand_pts = 0
    grand_pnl = 0
    for t_name, contracts in s.items():
        t_pts = sum(contracts)
        t_pnl = t_pts * 10.0
        grand_pts += t_pts
        grand_pnl += t_pnl
        print(f"{t_name}: C1={contracts[0]:+5.1f} | C2={contracts[1]:+5.1f} | C3={contracts[2]:+5.1f} | Total Pts: {t_pts:+6.1f} | P&L: ${t_pnl:+7.2f}")
    print("-" * 55)
    print(f"GRAND TOTAL: {grand_pts:+6.1f} points | ${grand_pnl:+7.2f}")
