# PM2 Log & Webhook Telemetry Audit Report — MGC1! Execution Window

**Date & Time of Audit:** November 18, 2026  
**Auditor:** Agent 1 (PM2 Log & Webhook Telemetry Auditor)  
**Target Process:** `tv-bridge` (PID running under PM2)  
**Target Log Files:**
- `/Users/melvin/.pm2/logs/tv-bridge-out.log`
- `/Users/melvin/.pm2/logs/tv-bridge-error.log`

---

## 1. Executive Summary

Between **3:36:26 PM and 3:38:30 PM SGT**, the `tv-bridge` service received a rapid sequence of 5 TradingView alert webhooks triggered by horizontal price alert lines on **MGC1!** (`COMEX_MINI:MGCZ2026`).

- **3:36:26 PM & 3:36:29 PM:** Two webhooks crossed alert thresholds (`3,770.1` and `3,768.8`). `tv-bridge` inspected the broker (`Interactive Brokers`) and found no open positions (`account is already flat`), returning `actionTaken: "none"`.
- **3:37:47 PM, 3:37:49 PM, and 3:38:30 PM:** Three subsequent webhooks crossed alert thresholds (`3,767.9`, `3,768.5`, and `3,769.2`). An open short position was detected (`id: 751494403`, `avgPrice: 3769.79536`). `tv-bridge` detected these as Price Alert Lines, dynamically computed 2-tick marketable limit cushions (`+0.20` points to cover short positions), successfully submitted limit close orders to Interactive Brokers via TradingView CDP, and recorded `actionTaken: "limit_close_submitted"`.

No runtime or CDP connection errors were logged in `tv-bridge-error.log` during this execution sequence.

---

## 2. Telemetry Timeline & Event Breakdown

```
+---------------+------------------------+-------------------+----------------------+--------------------+--------------------+
| Timestamp SGT | Webhook Raw Message    | Broker Status     | Detected Alert Price | Calc Limit Price   | Action Reported    |
+---------------+------------------------+-------------------+----------------------+--------------------+--------------------+
| 3:36:26 PM    | MGC1! Crossing 3,770.1 | Flat (0 pos)      | 3,770.1              | N/A (No position)  | none               |
| 3:36:29 PM    | MGC1! Crossing 3,768.8 | Flat (0 pos)      | 3,768.8              | N/A (No position)  | none               |
| 3:37:47 PM    | MGC1! Crossing 3,767.9 | Short 2 @ 3769.80 | 3,767.9              | 3,768.1 (+2 ticks) | limit_close_subm.. |
| 3:37:49 PM    | MGC1! Crossing 3,768.5 | Short 2 @ 3769.80 | 3,768.5              | 3,768.7 (+2 ticks) | limit_close_subm.. |
| 3:38:30 PM    | MGC1! Crossing 3,769.2 | Short 2 @ 3769.80 | 3,769.2              | 3,769.4 (+2 ticks) | limit_close_subm.. |
+---------------+------------------------+-------------------+----------------------+--------------------+--------------------+
```

---

## 3. Detailed Event Telemetry

### Event 1: 3:36:26 PM SGT
- **Webhook Received:** `{"raw":"MGC1! Crossing 3,770.1"}`
- **Parsed Mode:** `LIMIT (alertPrice=3770.1, cushion=2 ticks, src=price_alert_line)`
- **Symbol:** `MGC`
- **Requested Contracts:** `1`
- **Bridge Result:**
  ```json
  {
    "success": true,
    "actionTaken": "none",
    "broker": "Interactive Brokers",
    "message": "No open positions found (account is already flat)."
  }
  ```
- **Analysis:** Account had no active open position in IBKR at 3:36:26 PM.

---

### Event 2: 3:36:29 PM SGT
- **Webhook Received:** `{"raw":"MGC1! Crossing 3,768.8"}`
- **Parsed Mode:** `LIMIT (alertPrice=3768.8, cushion=2 ticks, src=price_alert_line)`
- **Symbol:** `MGC`
- **Requested Contracts:** `1`
- **Bridge Result:**
  ```json
  {
    "success": true,
    "actionTaken": "none",
    "broker": "Interactive Brokers",
    "message": "No open positions found (account is already flat)."
  }
  ```
- **Analysis:** Account remained flat.

---

### Event 3: 3:37:47 PM SGT
- **Webhook Received:** `{"raw":"MGC1! Crossing 3,767.9"}`
- **Parsed Mode:** `LIMIT (alertPrice=3767.9, cushion=2 ticks, src=price_alert_line)`
- **Symbol:** `MGC`
- **Requested Contracts:** `1`
- **Active Position Detected in IBKR:**
  - `id`: `"751494403"`
  - `symbol`: `"COMEX_MINI:MGCZ2026"`
  - `side`: `-1` (Short)
  - `avgPrice`: `3769.79536`
  - `totalQty`: `2` contracts
- **Limit Price Math:**
  - Base Alert Price = `3767.9`
  - Root = `MGC`, Tick Size = `0.10`
  - Covering Short (`oppSide = 1` Buy) -> Cushion Offset = `+(2 * 0.10) = +0.20`
  - `limitPrice = 3767.9 + 0.20 = 3768.1`
- **Bridge Result:**
  ```json
  {
    "success": true,
    "actionTaken": "limit_close_submitted",
    "broker": "Interactive Brokers",
    "closedPositions": [
      {
        "id": "751494403",
        "symbol": "COMEX_MINI:MGCZ2026",
        "closedQty": 1,
        "remainingQty": 1,
        "isPartial": true,
        "orderType": "limit",
        "limitPrice": 3768.1,
        "baseAlertPrice": 3767.9,
        "cushionTicks": 2,
        "tickSize": 0.1,
        "priceSource": "price_alert_line",
        "side": -1,
        "avgPrice": 3769.79536
      }
    ]
  }
  ```

---

### Event 4: 3:37:49 PM SGT
- **Webhook Received:** `{"raw":"MGC1! Crossing 3,768.5"}`
- **Parsed Mode:** `LIMIT (alertPrice=3768.5, cushion=2 ticks, src=price_alert_line)`
- **Symbol:** `MGC`
- **Requested Contracts:** `1`
- **Active Position Detected in IBKR:**
  - `id`: `"751494403"`, `symbol`: `"COMEX_MINI:MGCZ2026"`, `side`: `-1`, `avgPrice`: `3769.79536`
- **Limit Price Math:**
  - Base Alert Price = `3768.5`
  - Cushion Offset = `+(2 * 0.10) = +0.20`
  - `limitPrice = 3768.5 + 0.20 = 3768.7`
- **Bridge Result:**
  ```json
  {
    "success": true,
    "actionTaken": "limit_close_submitted",
    "broker": "Interactive Brokers",
    "closedPositions": [
      {
        "id": "751494403",
        "symbol": "COMEX_MINI:MGCZ2026",
        "closedQty": 1,
        "remainingQty": 1,
        "isPartial": true,
        "orderType": "limit",
        "limitPrice": 3768.7,
        "baseAlertPrice": 3768.5,
        "cushionTicks": 2,
        "tickSize": 0.1,
        "priceSource": "price_alert_line",
        "side": -1,
        "avgPrice": 3769.79536
      }
    ]
  }
  ```

---

### Event 5: 3:38:30 PM SGT
- **Webhook Received:** `{"raw":"MGC1! Crossing 3,769.2"}`
- **Parsed Mode:** `LIMIT (alertPrice=3769.2, cushion=2 ticks, src=price_alert_line)`
- **Symbol:** `MGC`
- **Requested Contracts:** `1`
- **Active Position Detected in IBKR:**
  - `id`: `"751494403"`, `symbol`: `"COMEX_MINI:MGCZ2026"`, `side`: `-1`, `avgPrice`: `3769.79536`
- **Limit Price Math:**
  - Base Alert Price = `3769.2`
  - Cushion Offset = `+(2 * 0.10) = +0.20`
  - `limitPrice = 3769.2 + 0.20 = 3769.4`
- **Bridge Result:**
  ```json
  {
    "success": true,
    "actionTaken": "limit_close_submitted",
    "broker": "Interactive Brokers",
    "closedPositions": [
      {
        "id": "751494403",
        "symbol": "COMEX_MINI:MGCZ2026",
        "closedQty": 1,
        "remainingQty": 1,
        "isPartial": true,
        "orderType": "limit",
        "limitPrice": 3769.4,
        "baseAlertPrice": 3769.2,
        "cushionTicks": 2,
        "tickSize": 0.1,
        "priceSource": "price_alert_line",
        "side": -1,
        "avgPrice": 3769.79536
      }
    ]
  }
  ```

---

## 4. Architectural & Telemetry Observations

1. **Auto-Detection Reliability:**  
   The regex parser in `parseAlertPriceAndMode()` correctly identified the TradingView price line format `MGC1! Crossing <PRICE>` for all 5 webhooks, extracted the exact alert price, and switched execution mode from Market to Limit with cushion.

2. **Cushion Calculation Correctness:**  
   Because the position was Short (`side: -1`), buying to close required placing a limit order above the alert price to act as a marketable limit order. With MGC tick size of `0.10` and cushion of 2 ticks, the calculation `alertPrice + 0.20` was mathematically exact across all 3 submission events (`3768.1`, `3768.7`, `3769.4`).

3. **Working Limit Orders & Broker State Sync:**  
   In all 3 limit close submissions, `remainingQty` was reported as `1` because `pos.qty` in IBKR remained `2` until working limit orders filled. If multiple alerts fire before previous limit orders fill, multiple limit close orders are submitted to the broker context.
