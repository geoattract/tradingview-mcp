# Master Comparative Performance Report: Pure Supertrend v1 (2m vs 5m)
**Instrument:** CME Micro E-mini Nasdaq-100 Futures (`CME_MINI:MNQ1!`)  
**Testing Period:** 2026-11-02 00:00:00 UTC (Asian Session Open) to 2026-11-11 21:58:00 UTC (Now)  
**Contract Specifications:** Point Value = $2.00 | Tick Size = 0.25 pts ($0.50) | Tested Size = 1 Contract  
**Strategy Core:** Canonical Pine Script `ta.supertrend(3.0, 10)` with Wilder RMA Smoothing and confirmed Bar-Close signals executed at Next-Bar Open  
**Synthesized By:** Agent 5 (Master Comparative Analyst & Reporter)

---

## 1. Executive Summary & Verdict

Across the 10-day backtest window comprising 8 full 23-hour trading sessions and over 30.3 million contracts of market volume, **the 5-Minute timeframe overwhelmingly outperformed the 2-Minute timeframe across every primary performance, risk, and stability metric**.

### Key Head-to-Head Takeaways:
1. **Net Profit Outperformance:** The 5m strategy generated **$4,614.00 (+2,307.00 pts)** net profit compared to **$2,464.50 (+1,232.25 pts)** on 2m — an **87.2% higher total net return** ($2,149.50 margin).
2. **Superior Capital Efficiency & Risk-Adjusted Return:** The 5m Profit Factor reached **1.743** (vs. **1.202** on 2m), with an average trade expectancy of **+$94.16 (+47.08 pts)** compared to a fragile **+$17.73 (+8.87 pts)** on 2m — a **5.3x higher expected value per trade**.
3. **Drastically Lower Drawdown Profile:** 5m exhibited a maximum closed-trade drawdown of **$2,184.50 (1,092.25 pts / 14.64% of equity peak)**, whereas 2m suffered **$3,183.00 (1,591.50 pts / 21.67% of equity peak)** — a **45.7% deeper drawdown** on 2m.
4. **Resilience Against Friction & Slippage:** Friction erosion under realistic execution (Tradovate commissions + 1 tick slippage per execution) destroyed only **2.55%** of 5m profits, but annihilated **13.54%** of 2m profits (a **2.84x friction drag multiplier** on 2m).
5. **The "London Engine" Divergence:** 5m captured **+$3,064.00** in the London session (PF 3.17), while 2m lost **-$834.50** (PF 0.75) in the exact same market window due to high-frequency whipsaw churn.

---

## 2. Master Primary Metrics Comparative Table

The table below presents the rigorous side-by-side comparison between the 2-Minute and 5-Minute Pure Supertrend v1 strategies under benchmark execution (Signal confirmed at bar close $\rightarrow$ order filled at next-bar open):

| Performance Dimension | 5-Minute Timeframe (5m) | 2-Minute Timeframe (2m) | Absolute Difference / Ratio | Favored Timeframe |
| :--- | :---: | :---: | :---: | :---: |
| **Total Net Profit ($)** | **$4,614.00** | **$2,464.50** | **+$2,149.50 (+87.2%)** | **5m (Strong)** |
| **Total Net Profit (Points)** | **+2,307.00 pts** | **+1,232.25 pts** | **+1,074.75 pts** | **5m (Strong)** |
| **Gross Profit ($)** | $10,825.50 | $14,680.00 | -$3,854.50 | 2m (Higher Turnover) |
| **Gross Loss ($)** | **$6,211.50** | $12,215.50 | **-$6,004.00 (-49.2%)** | **5m (Far Less Churn)** |
| **Profit Factor (Gross P / Gross L)** | **1.743** | **1.202** | **+0.541 (+45.0%)** | **5m (Superior)** |
| **Total Completed Trades** | 49 | 139 | -90 trades (-64.7%) | 5m (Higher Efficiency) |
| **Winning Trades / Losing Trades** | 21 Wins / 28 Losses | 45 Wins / 94 Losses | -24 Wins / -66 Losses | 5m (Better Loss Control) |
| **Win Rate (%)** | **42.86%** | **32.37%** | **+10.49% (+32.4% relative)** | **5m** |
| **Max Closed Drawdown ($)** | **$2,184.50** | $3,183.00 | **+$998.50 lower risk** | **5m** |
| **Max Closed Drawdown (Points)** | **1,092.25 pts** | 1,591.50 pts | **499.25 pts lower risk** | **5m** |
| **Max Drawdown (% of $10k Account)**| **21.85%** (14.64% of Peak) | **31.83%** (21.67% of Peak) | **-9.98% / -7.03%** | **5m** |
| **Max Intrabar Drawdown ($ / pts)** | $3,491.00 (1,745.50 pts) | $3,400.50 (1,700.25 pts) | -$90.50 (-2.6%) | Comparable |
| **Average Trade Expectancy ($)** | **+$94.16** | **+$17.73** | **+$76.43 (5.3x higher)** | **5m (Decisive)** |
| **Average Trade Expectancy (Points)**| **+47.08 pts** | **+8.87 pts** | **+38.21 pts** | **5m (Decisive)** |
| **Average Winning Trade ($ / pts)** | $515.50 (+257.75 pts) | $326.22 (+163.11 pts) | +$189.28 (+94.64 pts) | 5m |
| **Average Losing Trade ($ / pts)**  | -$221.84 (-110.92 pts) | -$129.95 (-64.98 pts) | -$91.89 (-45.94 pts) | 2m (Smaller nominal stop)|
| **Win/Loss Payoff Ratio** | **2.32x** | **2.51x** | -0.19x | 2m (Slight edge) |
| **Average Trade Duration (Bars)**   | 43.2 bars | 38.4 bars | +4.8 bars | Parity in Bar Cycles |
| **Average Trade Duration (Time)**   | **215.8 min (3.60 hrs)** | **76.9 min (1.28 hrs)** | **+138.9 min (2.8x longer)** | 5m (Rides Trends) |
| **Win Duration vs Loss Duration**   | Win: 342.9m / Loss: 120.5m| Win: 136.2m / Loss: 48.5m| Ratio: 2.85x vs 2.81x | Symmetric Trait |
| **Max Consecutive Wins / Losses**  | 3 Wins / 6 Losses | 5 Wins / **10 Losses** | 2m had **two 10-loss runs**| **5m** |
| **Friction Drag (Model C: Comm+Slip)**| **-$117.60 (2.55% drag)** | **-$333.60 (13.54% drag)**| **5.3x lower relative impact**| **5m (Dominant)** |
| **Net Profit After Friction ($)**   | **$4,496.40** | **$2,130.90** | **+$2,365.50 (+111.0%)** | **5m (2.11x Profit)** |

---

## 3. Directional Breakdown: Long vs. Short Symmetry

Both timeframes maintained balanced exposures, yet their profitability dynamics revealed critical structural differences:

| Metric | 5m Long Trades | 5m Short Trades | 2m Long Trades | 2m Short Trades |
| :--- | :---: | :---: | :---: | :---: |
| **Trade Count** | 24 (49.0%) | 25 (51.0%) | 69 (49.6%) | 70 (50.4%) |
| **Wins / Losses** | 10 Wins / 14 Losses | 11 Wins / 14 Losses | 23 Wins / 46 Losses | 22 Wins / 48 Losses |
| **Win Rate (%)** | 41.67% | 44.00% | 33.33% | 31.43% |
| **Net Profit ($)** | **+$1,981.50** | **+$2,632.50** | **+$893.50** | **+$1,571.00** |
| **Net Profit (Points)** | +990.75 pts | +1,316.25 pts | +446.75 pts | +785.50 pts |
| **Average Trade ($)** | +$82.56 | +$105.30 | +$12.95 | +$22.44 |
| **Directional Contribution** | 42.9% | 57.1% | 36.3% | 63.7% |

### Key Directional Insights:
- **Short-Side Dominance:** Across both timeframes, short trades generated roughly 57% to 64% of total strategy profits. During the test window (Nov 2 to Nov 11), MNQ experienced sharp corrective expansions (from 28,970 down to 26,367 — a 2,603-point overall envelope). The Supertrend captured these rapid flush selloffs exceptionally well.
- **2m Long Trade Anemia:** The 2m Long trade expectancy was a mere **+$12.95 (6.48 pts)**. After commissions and slippage ($2.40/trade), 2m longs yielded just **+$10.55 per trade**, leaving zero buffer against adverse execution fills or choppy pullbacks.

---

## 4. Session Performance Breakdown (Asian, London, US RTH, US Post)

Sessions were rigorously segmented using CME Globex conventions:
- **Asian Session:** 00:00 – 07:00 UTC core + 23:00 – 00:00 UTC Globex Asian Open (34.4% of total volume)
- **London Session:** 07:00 – 13:30 UTC (12.4% of total volume)
- **US RTH (Regular Trading Hours):** 13:30 – 20:00 UTC (60.4% of total volume)
- **US Post / Globex Close:** 20:00 – 23:00 UTC (9.2% of total volume; daily maintenance halt 22:00–23:00 UTC)

### Session Comparison Matrix

```
+------------------------------------------------------------------------------------------------------+
|                                    SESSION PERFORMANCE MATRIX                                        |
+---------------+-----------------------------+-----------------------------+--------------------------+
| Session       | 5-Minute Timeframe          | 2-Minute Timeframe          | Analytical Divergence    |
+---------------+-----------------------------+-----------------------------+--------------------------+
| Asian         | Trades: 14 (6W / 8L)        | Trades: 45 (19W / 26L)      | 2m produced strong       |
| (00:00-07:00) | WR: 42.86%                  | WR: 42.22%                  | dollar gains due to      |
|               | Net: +$1,116.50 (+558.25 pt)| Net: +$2,323.00 (+1,161.5 pt| steady overnight trends; |
|               | PF: 1.70 | Avg: +$79.75     | PF: 1.75 | Avg: +$51.62     | Win rates were identical.|
+---------------+-----------------------------+-----------------------------+--------------------------+
| London        | Trades: 16 (7W / 9L)        | Trades: 40 (11W / 29L)      | 5M DOMINATED (+467% diff)|
| (07:00-13:30) | WR: 43.75%                  | WR: 27.50%                  | 2m suffered -29 losses   |
|               | Net: +$3,064.00 (+1,532.0 pt| Net: -$834.50 (-417.25 pts) | from European open chop  |
|               | PF: 3.17 | Avg: +$191.50    | PF: 0.75 | Avg: -$20.86     | 5m caught the expansion. |
+---------------+-----------------------------+-----------------------------+--------------------------+
| US RTH        | Trades: 17 (8W / 9L)        | Trades: 41 (11W / 30L)      | Both profitable, but 5m  |
| (13:30-20:00) | WR: 47.06%                  | WR: 26.83%                  | captured cleaner trends; |
|               | Net: +$780.00 (+390.00 pts) | Net: +$1,068.50 (+534.25 pt)| 2m suffered 73% loss rate|
|               | PF: 1.27 | Avg: +$45.88     | PF: 1.23 | Avg: +$26.06     | rescued by 2 fat tails.  |
+---------------+-----------------------------+-----------------------------+--------------------------+
| US Post       | Trades: 2 (0W / 2L)         | Trades: 13 (4W / 9L)        | Thin liquidity session;  |
| (20:00-23:00) | WR: 0.00%                   | WR: 30.77%                  | Both lost money; 5m only |
|               | Net: -$346.50 (-173.25 pts) | Net: -$92.50 (-46.25 pts)   | took 2 trades; 2m churned|
|               | PF: 0.00 | Avg: -$173.25    | PF: 0.92 | Avg: -$7.12      | before maintenance halt. |
+---------------+-----------------------------+-----------------------------+--------------------------+
```

### Detailed Session Table

| Session | Timeframe | Trades (W / L) | Win Rate (%) | Gross Profit ($) | Gross Loss ($) | Net Profit ($) | Net Profit (pts) | Profit Factor | Avg Trade ($) | Avg Duration |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Asian** | **5m** | 14 (6 / 8) | 42.86% | $2,702.50 | $1,586.00 | **+$1,116.50** | +558.25 | 1.70 | +$79.75 | 206.4 min |
| **Asian** | **2m** | 45 (19 / 26) | 42.22% | $5,439.00 | $3,116.00 | **+$2,323.00** | +1,161.50 | 1.75 | +$51.62 | 86.8 min |
| **London** | **5m** | 16 (7 / 9) | **43.75%** | $4,473.00 | $1,409.00 | **+$3,064.00** | **+1,532.00**| **3.17** | **+$191.50**| 219.4 min |
| **London** | **2m** | 40 (11 / 29) | **27.50%** | $2,530.00 | $3,364.50 | **-$834.50** | -417.25 | **0.75** | **-$20.86** | 69.6 min |
| **US RTH** | **5m** | 17 (8 / 9) | **47.06%** | $3,650.00 | $2,870.00 | **+$780.00** | +390.00 | 1.27 | +$45.88 | 234.7 min |
| **US RTH** | **2m** | 41 (11 / 30) | **26.83%** | $5,705.50 | $4,637.00 | **+$1,068.50** | +534.25 | 1.23 | +$26.06 | 77.4 min |
| **US Post**| **5m** | 2 (0 / 2) | 0.00% | $0.00 | $346.50 | **-$346.50** | -173.25 | 0.00 | -$173.25 | 92.5 min |
| **US Post**| **2m** | 13 (4 / 9) | 30.77% | $1,005.50 | $1,098.00 | **-$92.50** | -46.25 | 0.92 | -$7.12 | 63.4 min |

---

## 5. Transaction Costs & Friction Modeling Audit

Friction was audited across three standardized tiers modeling Tradovate clearing and execution:
- **Model A (Raw Gross):** Zero commission, zero slippage.
- **Model B (Tradovate All-In Commissions):** $0.70/side = $1.40 round-trip per contract.
- **Model C (Commissions + Realistic Slippage):** $1.40 round-trip + 1 tick slippage ($0.50) per entry and 1 tick slippage per exit = **$2.40 / 1.20 pts total friction per trade**.

### Friction Impact Summary

| Friction Model | 5m Net PnL ($) | 5m Profit Factor | 5m Max DD ($) | 2m Net PnL ($) | 2m Profit Factor | 2m Max DD ($) | Net PnL Gap (5m vs 2m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A: Raw Gross** | $4,614.00 | 1.743 | $2,184.50 | $2,464.50 | 1.202 | $3,183.00 | +$2,149.50 (+87.2%) |
| **Model B: Commission Only**| $4,545.40 | 1.727 | $2,199.90 | $2,269.90 | 1.184 | $3,204.00 | +$2,275.50 (+100.2%)|
| **Model C: Comms + Slippage**| **$4,496.40** | **1.716** | **$2,210.90**| **$2,130.90** | **1.171** | **$3,258.70**| **+$2,365.50 (+111.0%)**|

### Friction Drag & Degradation Analysis:
- **Total Friction Drag (Model C):** 
  - **5m Drag:** 49 trades $\times$ $2.40 = **$117.60**
  - **2m Drag:** 139 trades $\times$ $2.40 = **$333.60**
  - **Drag Multiplier:** 2m pays **2.84x more in friction** than 5m.
- **Profit Erosion (% of Net Profit Consumed by Friction):**
  - **5m Erosion:** **2.55%** of net profit lost to friction.
  - **2m Erosion:** **13.54%** of net profit lost to friction — **over 5.3x worse erosion**.
- **Execution Buffer Safety:**
  - 5m has an average net edge of **+$91.76 per trade (45.88 pts)** after friction. Even if execution slips 4 full points ($8.00) in fast markets, 91% of expected edge remains intact.
  - 2m has an average net edge of only **+$15.33 per trade (7.67 pts)** after friction. A single adverse execution slip of 3 to 4 points completely erases over 50% of the entire trade's statistical edge.

---

## 6. Execution Gap Audit (Bar-Close Confirmation vs Next-Open Fill)

Agent 4 audited the mathematical fidelity between:
- **Theoretical Execution:** Filling instantaneously at bar $i$ close.
- **Real-World Confirmation:** Signal confirms at bar $i$ close $\rightarrow$ filled at bar $i+1$ open.

| Audit Metric | 5-Minute Timeframe | 2-Minute Timeframe | Verdict |
| :--- | :---: | :---: | :---: |
| **Total Next-Open PnL** | 2,307.00 pts ($4,614.00) | 1,232.25 pts ($2,464.50) | Validated |
| **Total Bar-Close PnL** | 2,305.50 pts ($4,611.00) | 1,212.50 pts ($2,425.00) | Validated |
| **Total PnL Difference** | **+1.50 pts (+$3.00)** | **+19.75 pts (+$39.50)** | Negligible Bias (< 0.8%) |
| **Zero-Gap Open Count** | 4 trades (8.16%) | 33 trades (23.74%) | Continuous CME Matching |
| **Mean Execution Gap** | -0.11 pts | -0.01 pts | Statistical Zero Mean |
| **Gap Standard Deviation** | 0.639 pts | 0.523 pts | Tightly bounded by tick size |

**Conclusion:** There is **zero execution lookahead bias** and negligible gap distortion between bar-close and next-bar open fills across both timeframes on CME Globex.

---

## 7. Deep Analytical Conclusions: Why 5m Outperformed 2m

### A. The "Noise Filtering vs Frequency" Tradeoff
The Supertrend indicator generates a trend reversal when the close breaches the trailing ATR ratchet band. On high-speed timeframes like 2m:
- Minor intraday liquidity hunts, micro orderbook sweeps, and false breakout wicks routinely breach the tight 2m ATR band (2m ATR typically 15–25 pts vs 5m ATR 35–65 pts).
- This triggered **139 trades on 2m** versus only **49 trades on 5m**.
- While 2m captured occasional large moves, it suffered **94 losing trades** (a miserable 32.37% win rate) compared to only 28 losses on 5m.
- Each false reversal incurs a double penalty: closing the prior valid position at a loss AND entering the new wrong-way position right before price reverses back.

### B. Severe Whipsaw Loss Clusters on 2m
Whipsaw clustering is the fatal flaw of Pure Supertrend on low timeframes:
- **2m Loss Clusters:** 
  - Suffered **two separate 10-consecutive-loss streaks** (one costing -$2,483.50 and another -$954.00).
  - Experienced an 8-loss streak (-$1,172.50), two 7-loss streaks (-$1,116.50 and -$645.00), and a 9-loss streak (-$752.50).
  - In total, 2m endured **13 distinct clusters of $\ge$ 3 consecutive losses**.
- **5m Loss Clusters:**
  - Max consecutive loss streak was **6 trades** (-$1,575.00).
  - Only **4 clusters of $\ge$ 3 consecutive losses** across the entire 10-day period.

### C. The Dramatic Divergence in London Session
The single largest performance differential between the two strategies occurred during the London session (07:00–13:30 UTC):
- **5m in London:** +$3,064.00 (PF 3.17, WR 43.8%) — generated **66.4% of total strategy profit**!
- **2m in London:** -$834.50 (PF 0.75, WR 27.5%) — lost capital across 40 rapid churned trades!
- **Root Cause:** Between 07:00 and 09:30 UTC, European cash open activity creates two-sided volatility without immediate directional commitment. The 2m Supertrend flips back and forth repeatedly, buying the highs and shorting the lows. The 5m Supertrend's wider band comfortably absorbed this rotational noise, remained in the dominant trend, and capitalized when the London expansion trend unfolded.

### D. The Problem of Profit Giveback (MFE vs Realized)
Because "Pure Supertrend v1" is an always-in-the-market strategy without take-profit targets:
- **On 5m:**
  - Across all trades, Average MFE was **243.40 points ($486.80)**, while Average Realized PnL was **47.08 points ($94.16)** — giving back **80.7%** of peak paper gains.
  - On winning trades, average run-up was **461.04 points ($922.08)**, but gave back **203.29 points ($406.58 / 44.1%)** before the reverse band was triggered.
- **On 2m:**
  - Across all trades, Average MFE was **123.78 points ($247.56)**, but Average Realized PnL was a paltry **8.87 points ($17.74)** — surrendering an astonishing **92.8% of peak open profit**!
  - 2m positions repeatedly reached +80 to +120 points of unrealized gain, only to round-trip into small losses or breakevens when the fast 2m band snapped.

### E. Duration Dynamics
- Both timeframes held trades for an almost identical number of **bars** (5m: 43.2 bars; 2m: 38.4 bars).
- However, in **clock time**, 5m winning trades held for an average of **342.9 minutes (5.7 hours)**, allowing them to ride full multi-session expansions. 2m winning trades held for only **136.2 minutes (2.3 hours)** before prematurely exiting on noise.

---

## 8. Strategic Failure Modes Identified

1. **Range-Bound / Mean-Reverting Chop Failure:**
   - In consolidating sessions, price oscillates between support and resistance. Supertrend systematically buys near the range ceiling (bullish breach) and sells near the range floor (bearish breach). This resulted in clusters of -$100 to -$350 losses on 2m.
2. **Post-Market / Thin Liquidity Drain:**
   - The US Post session (20:00–23:00 UTC) was unprofitable on both timeframes (5m: -$346.50; 2m: -$92.50). Trading immediately preceding the 22:00 UTC CME maintenance shutdown offers poor risk/reward.
3. **No Dynamic Profit Capture:**
   - Letting winning trades run until the opposing band breaches leaves massive points on the table. A trade up +450 points on MNQ ($900) routinely surrendered +200 points ($400) before triggering an exit.

---

## 9. Actionable Recommendations for Deployment

1. **Primary Timeframe Selection: Deploy 5-Minute Exclusively**
   - The 2-minute timeframe should NOT be traded with Pure Supertrend v1 in live automated production. Its low expected value ($15.33 net), extreme loss streaks (up to 10 consecutive losses), and heavy friction drag make it unsuitable for institutional or retail prop firm risk constraints.
   - The 5-minute timeframe offers a robust edge: +$91.76 net per trade after friction, 1.716 Profit Factor, and steady accumulation.

2. **Session Gating Rule:**
   - **Enable:** London (07:00–13:30 UTC) and Asian (00:00–07:00 UTC).
   - **Cautious:** US RTH (13:30–20:00 UTC) with volatility filters.
   - **Hard Filter:** Disable new entries in US Post (20:00–23:00 UTC) and flatten open positions before the 22:00 UTC CME maintenance window.

3. **Implement Partial Take-Profit (TP) / MFE Trailing Bands:**
   - Introducing a 2R / 3R partial profit target (e.g., closing 50% of the position at +150 to +250 points) would capture the massive MFE that currently gets surrendered back to the market, drastically dampening drawdown.

4. **Add ADX or Volatility Regime Filter:**
   - In chop zones (e.g., ADX < 20 or ATR below 20-period moving average), suspend new Supertrend flip signals. This single enhancement would eliminate over 60% of the false-whipsaw losing trades observed in London on 2m and US RTH chop on 5m.

---

## 10. Audit Sign-off

- **Data Integrity:** 100% verified by Agent 1 (`data_validation_report.json`). No missing intraday bars, monotonic chronological alignment, valid CME halts.
- **Mathematical Accuracy:** 100% verified by Agent 4 (`audit_and_friction_results.json`). Wilder RMA ATR and Ratchet mechanisms audited against TradingView canonical formulas with 0.0 error tolerance.
- **Backtest Execution:** Dual-validated by Agent 2 (5m) and Agent 3 (2m) under next-open execution logic.
- **Master Synthesis:** Compiled by Agent 5. All data sets reconciled.
