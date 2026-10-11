#!/usr/bin/env node

/**
 * monitor_trend_reversal.mjs
 * 
 * Standalone Antigravity Trend Reversal Monitor for ES1! / MES1!
 * 
 * Monitors every 10 minutes (or custom interval):
 * 1. Price crossing / touching Ichimoku Base Line (Kijun-sen 26)
 * 2. CM MACD Clean Flow Bullish Crossup (MACD >= Signal)
 * 3. CM MACD Clean Flow Trend Strip color flip (Bearish -> Neutral/Bullish)
 * 
 * When triggered:
 * - Pops native macOS notification banner
 * - Plays audio chime
 * - Logs formatted status and exit recommendations
 * 
 * Usage:
 *   node scripts/monitor_trend_reversal.mjs          # Runs every 10 minutes
 *   node scripts/monitor_trend_reversal.mjs --once   # Runs a single check and exits
 *   node scripts/monitor_trend_reversal.mjs --every 5 # Runs every 5 minutes
 */

import { exec } from 'node:child_process';
import { getOhlcv } from '../src/core/data.js';

// Configuration
const ARGS = process.argv.slice(2);
const RUN_ONCE = ARGS.includes('--once');
const INTERVAL_MINUTES = (() => {
  const idx = ARGS.indexOf('--every');
  if (idx !== -1 && ARGS[idx + 1]) return Number(ARGS[idx + 1]) || 10;
  return 10;
})();

function sendMacNotification(title, subtitle, message) {
  const cleanTitle = title.replace(/"/g, '\\"');
  const cleanSub = subtitle.replace(/"/g, '\\"');
  const cleanMsg = message.replace(/"/g, '\\"');
  const script = `display notification "${cleanMsg}" with title "${cleanTitle}" subtitle "${cleanSub}" sound name "Glass"`;
  exec(`osascript -e '${script}'`, (err) => {
    if (err) console.error('Notification error:', err.message);
  });
}

function playAlertSound() {
  exec('afplay /System/Library/Sounds/Ping.aiff', () => {});
}

function calcEma(values, length) {
  const result = new Float64Array(values.length);
  const alpha = 2.0 / (length + 1);
  result[0] = values[0];
  for (let i = 1; i < values.length; i++) {
    result[i] = alpha * values[i] + (1 - alpha) * result[i - 1];
  }
  return result;
}

function stdDev(slice) {
  if (slice.length === 0) return 0;
  const mean = slice.reduce((a, b) => a + b, 0) / slice.length;
  const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / slice.length;
  return Math.sqrt(variance);
}

export async function checkReversal() {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  console.log(`\n[${timestamp}] Fetching latest chart bars...`);

  let data;
  try {
    data = await getOhlcv({ count: 120 });
  } catch (err) {
    console.error(`[${timestamp}] Error fetching chart data: ${err.message}`);
    return null;
  }

  const bars = data.bars;
  const n = bars.length;
  if (n < 60) {
    console.warn(`Not enough bars (${n} < 60) for accurate indicator calculation.`);
    return null;
  }

  const highs = bars.map(b => b.high);
  const lows = bars.map(b => b.low);
  const closes = bars.map(b => b.close);
  const volumes = bars.map(b => b.volume);

  // 1. Ichimoku Kijun-sen (Base Line: 26 periods)
  const kijunSliceHigh = highs.slice(n - 26);
  const kijunSliceLow = lows.slice(n - 26);
  const highest26 = Math.max(...kijunSliceHigh);
  const lowest26 = Math.min(...kijunSliceLow);
  const kijun = (highest26 + lowest26) / 2.0;

  // Tenkan-sen (Conversion Line: 9 periods)
  const tenkanSliceHigh = highs.slice(n - 9);
  const tenkanSliceLow = lows.slice(n - 9);
  const tenkan = (Math.max(...tenkanSliceHigh) + Math.min(...tenkanSliceLow)) / 2.0;

  // 2. CM MACD Clean Flow (Fast 8, Slow 17, Signal 9, DeadZone 50)
  const macd = new Float64Array(n);
  const fastEma = calcEma(closes, 8);
  const slowEma = calcEma(closes, 17);
  for (let i = 0; i < n; i++) macd[i] = fastEma[i] - slowEma[i];
  const sig = calcEma(Array.from(macd), 9);

  // Dead zone stdev(50)
  const deadLen = 50;
  const deadZone = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const start = Math.max(0, i - deadLen + 1);
    deadZone[i] = 1.0 * stdDev(Array.from(macd.slice(start, i + 1)));
  }

  // Trend State (-1: Bearish/Red, 1: Bullish/Green, 0: Neutral)
  const trend = new Int8Array(n);
  let curTrend = 0;
  for (let i = 0; i < n; i++) {
    if (macd[i] > deadZone[i]) curTrend = 1;
    else if (macd[i] < -deadZone[i]) curTrend = -1;
    trend[i] = curTrend;
  }

  // Current and previous candle metrics
  const currBar = bars[n - 1];
  const prevBar = bars[n - 2];
  const currMacd = macd[n - 1];
  const prevMacd = macd[n - 2];
  const currSig = sig[n - 1];
  const prevSig = sig[n - 2];
  const currTrend = trend[n - 1];
  const prevTrend = trend[n - 2];

  // Conditions
  const priceHitKijun = currBar.high >= kijun;
  const priceClosedAboveKijun = currBar.close >= kijun;
  const macdCrossUp = currMacd >= currSig && prevMacd < prevSig;
  const trendFlippedBullish = currTrend > prevTrend; // e.g. -1 to 0, or -1 to 1

  const trendColorStr = currTrend === 1 ? 'GREEN (Bullish)' : currTrend === -1 ? 'RED/ORANGE (Bearish)' : 'GRAY (Neutral)';

  console.log(`--------------------------------------------------`);
  console.log(`Current Price:   ${currBar.close.toFixed(2)} (High: ${currBar.high.toFixed(2)}, Low: ${currBar.low.toFixed(2)})`);
  console.log(`Ichimoku Kijun:  ${kijun.toFixed(2)} | Tenkan: ${tenkan.toFixed(2)}`);
  console.log(`MACD Line:       ${currMacd.toFixed(2)} | Signal Line: ${currSig.toFixed(2)} | Diff: ${(currMacd - currSig).toFixed(2)}`);
  console.log(`Trend Strip:     ${trendColorStr}`);
  console.log(`--------------------------------------------------`);

  const triggers = [];
  if (priceHitKijun) {
    triggers.push(`Price hit/exceeded Kijun-sen (${currBar.high.toFixed(2)} >= ${kijun.toFixed(2)})`);
  }
  if (priceClosedAboveKijun) {
    triggers.push(`Candle closed above Kijun-sen (${currBar.close.toFixed(2)} >= ${kijun.toFixed(2)})`);
  }
  if (macdCrossUp) {
    triggers.push(`MACD Wave Speed Bullish Crossup (${currMacd.toFixed(2)} >= ${currSig.toFixed(2)})`);
  }
  if (trendFlippedBullish) {
    triggers.push(`MACD Clean Flow Trend Strip flipped to ${trendColorStr}`);
  }

  if (triggers.length > 0) {
    console.log(`🚨 [ALERT - DOWNTREND STOP / REVERSAL NUDGE DETECTED]`);
    triggers.forEach(t => console.log(`   👉 ${t}`));
    console.log(`Action: Check short position stop loss or take profit!\n`);

    const subtitle = `Downtrend Pause / Reversal Alert`;
    const message = triggers.join(' | ');
    sendMacNotification('Antigravity Trading Alert', subtitle, message);
    playAlertSound();
    return { triggered: true, triggers, currPrice: currBar.close, kijun, trend: trendColorStr };
  } else {
    console.log(`✅ Downtrend continuing intact. No reversal triggers active.`);
    return { triggered: false, currPrice: currBar.close, kijun, trend: trendColorStr };
  }
}

// Execution logic
if (RUN_ONCE) {
  checkReversal().then(() => process.exit(0)).catch(err => {
    console.error(err);
    process.exit(1);
  });
} else {
  console.log(`=======================================================`);
  console.log(`🤖 Antigravity Trend Reversal Monitor Started`);
  console.log(`Target: CME ES1! / MES1!`);
  console.log(`Checking every: ${INTERVAL_MINUTES} minutes`);
  console.log(`Triggers: Kijun-sen (Base Line) cross + MACD Clean Flow flip`);
  console.log(`Press Ctrl+C to stop.`);
  console.log(`=======================================================`);

  // Run immediate first check
  checkReversal();

  // Schedule interval
  setInterval(checkReversal, INTERVAL_MINUTES * 60 * 1000);
}
