# MGC 5-Minute 3-Contract Scaling Strategy P&L Report

- **Instrument**: COMEX Micro Gold Futures (`COMEX_MINI:MGC1!`)
- **Point Value**: \$10.00 per full point (\$1.00 per 0.1 tick)
- **Timeframe**: 5-Minute Candles
- **Session Filter**: Entries after 09:00 SGT, open positions allowed to run to natural exit
- **Position Sizing**: **3 Contracts per Entry**
- **Scaling Rules**:
  - **Contract 1 (1x)**: Exits upon **1st Reversal Curl** (`▼` for Long, `▲` for Short)
  - **Contracts 2 & 3 (2x)**:
    - *Interpretation A (Split Runner)*: Contract 2 exits on **2nd Reversal Curl**; Contract 3 holds until **Next SuperTrend Flip**
    - *Interpretation B (Both on 2nd Curl)*: Both exit on **2nd Reversal Curl** (or SuperTrend Flip if hit earlier)
    - *Interpretation C (Both on SuperTrend Flip)*: Both hold until **Next SuperTrend Flip**

---

## Trade-by-Trade Scaling Audit

### Trade 1: BUY at 09:35 SGT (Bar 124) @ 3,860.7
* **Contract 1 Exit**: First reversal curl (`▼`) at 09:55 SGT (bar 128) @ **3,868.7** -> **+8.0 pts** (+\$80.00)
* **Contract 2 Exit**: Second reversal curl (`▼`) at 10:30 SGT (bar 135) @ **3,868.0** -> **+7.3 pts** (+\$73.00)
* **Contract 3 Exit**: SuperTrend SELL badge at 12:15 SGT (bar 156) @ **3,869.4** -> **+8.7 pts** (+\$87.00)
* **Trade 1 Total (Split Runner)**: **+24.0 pts (+\$240.00)**

### Trade 2: SELL at 12:15 SGT (Bar 156) @ 3,869.4
* **Contract 1 Exit**: First reversal curl (`▲`) at 12:45 SGT (bar 162) @ **3,876.6** -> **-7.2 pts** (-\$72.00)
* **Contracts 2 & 3 Exit**: SuperTrend flipped to BUY at 12:55 SGT (bar 164) @ **3,877.5** before a second curl cycle could form -> **-8.1 pts each** (-\$81.00 x 2 = -\$162.00)
* **Trade 2 Total**: **-23.4 pts (-\$234.00)**

### Trade 3: BUY at 12:55 SGT (Bar 164) @ 3,877.5
* **Contract 1 Exit**: First reversal curl (`▼`) at 13:30 SGT (bar 171) @ **3,888.8** -> **+11.3 pts** (+\$113.00)
* **Contract 2 Exit**: Second reversal curl (`▼`) at 14:05 SGT (bar 178) @ **3,878.5** -> **+1.0 pt** (+\$10.00)
* **Contract 3 Exit**: SuperTrend SELL badge at 14:10 SGT (bar 179) @ **3,877.1** -> **-0.4 pts** (-\$4.00)
* **Trade 3 Total (Split Runner)**: **+11.9 pts (+\$119.00)**

### Trade 4: SELL at 14:10 SGT (Bar 179) @ 3,877.1
* **Contract 1 Exit**: First reversal curl (`▲`) at 14:25 SGT (bar 182) @ **3,878.4** -> **-1.3 pts** (-\$13.00)
* **Contract 2 Exit**: Second reversal curl (`▲`) at 15:50 SGT (bar 199) @ **3,875.8** -> **+1.3 pts** (+\$13.00)
* **Contract 3 Exit**:
  * *Option A (Held to next SuperTrend BUY flip at 19:30 SGT @ 3,864.6)*: **+12.5 pts** (+\$125.00)
  * *Option B (Closed flat at 17:00 SGT session close @ 3,871.4)*: **+5.7 pts** (+\$57.00)
* **Trade 4 Total (Option A)**: **+12.5 pts (+\$125.00)**
* **Trade 4 Total (Option B)**: **+5.7 pts (+\$57.00)**

---

## Grand Totals by Scaling Model

| Model | C1 (1st Curl) | C2 (2nd Curl) | C3 (SuperTrend Flip) | Total Points | Total Dollar P&L |
|---|---|---|---|---|---|
| **Split Runner (1st Curl + 2nd Curl + SuperTrend Flip)** | +10.8 pts (+\$108) | +1.5 pts (+\$15) | +12.7 pts (+\$127) | **+25.0 pts** | **+\$250.00** |
| **Conservative (C2 & C3 both exit on 2nd Curl)** | +10.8 pts (+\$108) | +1.5 pts (+\$15) | +1.5 pts (+\$15) | **+13.8 pts** | **+\$138.00** |
| **Trend-Following (C2 & C3 both hold to SuperTrend Flip)** | +10.8 pts (+\$108) | +12.7 pts (+\$127) | +12.7 pts (+\$127) | **+36.2 pts** | **+\$362.00** |
