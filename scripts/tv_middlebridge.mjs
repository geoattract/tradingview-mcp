#!/usr/bin/env node

/**
 * tv_middlebridge.mjs
 * 
 * Local TradingView Middle-Bridge Webhook Listener
 * 
 * Flow:
 * 1. Listens for incoming HTTP POST webhooks from TradingView / n8n / Cloudflare Tunnel
 * 2. Authenticates payload via shared secret
 * 3. Connects to TradingView Desktop (CDP port 9222)
 * 4. Finds active broker (Tradovate) position for requested symbol (e.g. MGC1!, MNQ1!)
 * 5. Executes native position close & flattens orders
 * 6. Fires macOS audio chime and notification banner
 * 
 * Usage:
 *   node scripts/tv_middlebridge.mjs
 *   pm2 start scripts/tv_middlebridge.mjs --name tv-bridge
 */

import http from 'node:http';
import { exec } from 'node:child_process';
import CDP from 'chrome-remote-interface';

// -------------------------------------------------------------
// Configuration
// -------------------------------------------------------------
const PORT = Number(process.env.BRIDGE_PORT) || 3000;
const AUTH_SECRET = process.env.BRIDGE_SECRET || 'melvin_trading_secure';
const CDP_HOST = process.env.TV_CDP_HOST || '127.0.0.1';
const CDP_PORT = Number(process.env.TV_CDP_PORT) || 9222;

const startTime = Date.now();

// -------------------------------------------------------------
// Mac Notifications & Audio Alerts
// -------------------------------------------------------------
function sendMacNotification(title, subtitle, message) {
  const cleanTitle = title.replace(/"/g, '\\"');
  const cleanSub = subtitle.replace(/"/g, '\\"');
  const cleanMsg = message.replace(/"/g, '\\"');
  const script = `display notification "${cleanMsg}" with title "${cleanTitle}" subtitle "${cleanSub}" sound name "Glass"`;
  exec(`osascript -e '${script}'`, (err) => {
    if (err) console.error('Notification error:', err.message);
  });
}

function playSound(sound = 'Glass') {
  exec(`afplay /System/Library/Sounds/${sound}.aiff`, () => {});
}

// -------------------------------------------------------------
// TradingView CDP Interaction Helpers
// -------------------------------------------------------------
async function getTradingViewClient() {
  try {
    const listResp = await fetch(`http://${CDP_HOST}:${CDP_PORT}/json/list`);
    const targets = await listResp.json();
    const chartTarget = targets.find(t => t.type === 'page' && /tradingview\.com\/chart/i.test(t.url))
      || targets.find(t => t.type === 'page' && /tradingview/i.test(t.url));

    if (!chartTarget) {
      throw new Error('No TradingView chart window found on port 9222. Ensure TradingView is running with remote debugging.');
    }

    const client = await CDP({ host: CDP_HOST, port: CDP_PORT, target: chartTarget.id });
    await client.Runtime.enable();
    return { client, target: chartTarget };
  } catch (err) {
    throw new Error(`Failed to connect to TradingView CDP on port ${CDP_PORT}: ${err.message}`);
  }
}

/**
 * Execute close position inside TradingView page context
 */
async function executeClosePosition({ symbol = null, all = false }) {
  const { client } = await getTradingViewClient();

  try {
    const expr = `(async () => {
      const t = window.TradingViewApi && window.TradingViewApi._tradingService && window.TradingViewApi._tradingService.trading();
      if (!t) return { success: false, error: "Trading service not found on active tab" };

      const bc = typeof t.brokerCommandsUI === 'function' ? t.brokerCommandsUI() : t._brokerCommandsUI;
      if (!bc) return { success: false, error: "Broker commands UI not available" };

      const broker = bc._activeBroker;
      if (!broker) return { success: false, error: "No active broker connected" };

      const brokerTitle = broker.metainfo ? broker.metainfo().title : "Broker";
      const allPositions = await broker.positions();
      const activePositions = (allPositions || []).filter(p => Math.abs(p.qty || 0) > 0);

      if (activePositions.length === 0) {
        return {
          success: true,
          actionTaken: "none",
          broker: brokerTitle,
          message: "No open positions found (account is already flat)."
        };
      }

      // Filter target position
      const targetSymbol = ${JSON.stringify(symbol || '')}.toUpperCase();
      const closeAll = ${Boolean(all)};

      const toClose = activePositions.filter(p => {
        if (closeAll) return true;
        if (!targetSymbol) return true; // Close first active if unspecified
        const pSym = (p.symbol || '').toUpperCase();
        return pSym.includes(targetSymbol) || targetSymbol.includes(pSym);
      });

      if (toClose.length === 0) {
        return {
          success: true,
          actionTaken: "none",
          broker: brokerTitle,
          message: "No open positions matched symbol: " + targetSymbol,
          existingPositions: activePositions.map(p => ({ id: p.id, symbol: p.symbol, qty: p.qty, side: p.side }))
        };
      }

      // Enable instant execution / disable confirmation dialogs
      if (t.noConfirmEnabled && typeof t.noConfirmEnabled.setValue === 'function') {
        t.noConfirmEnabled.setValue(true);
      }
      if (bc && bc._noConfirmEnabled && typeof bc._noConfirmEnabled.setValue === 'function') {
        bc._noConfirmEnabled.setValue(true);
      }

      const closed = [];
      for (const pos of toClose) {
        try {
          // Direct broker-level market close
          if (typeof broker.closePosition === 'function') {
            await broker.closePosition(pos.id);
          } else {
            await bc.closePosition(pos.id);
          }
        } catch (err) {
          await bc.closePosition(pos.id);
        }
        closed.push({ id: pos.id, symbol: pos.symbol, qty: pos.qty, side: pos.side, avgPrice: pos.avgPrice });
      }

      // Safety Layer: Auto-click any confirmation dialog button if one appeared in the UI
      await new Promise(r => setTimeout(r, 150));
      const confirmBtns = Array.from(document.querySelectorAll('button')).filter(b => {
        const txt = (b.innerText || '').trim().toLowerCase();
        return txt === 'close position' || txt === 'confirm' || txt === 'yes';
      });
      for (const btn of confirmBtns) {
        if (btn.offsetParent !== null) {
          btn.click();
        }
      }

      // Also cancel open working bracket orders for these symbols
      try {
        if (typeof bc.cancelOrders === 'function') {
          await bc.cancelOrders();
        }
      } catch (err) {
        // Non-critical if cancelOrders fails
      }

      return {
        success: true,
        actionTaken: "closed",
        broker: brokerTitle,
        closedPositions: closed
      };
    })()`;

    const res = await client.Runtime.evaluate({
      expression: expr,
      returnByValue: true,
      awaitPromise: true
    });

    if (res.exceptionDetails) {
      throw new Error(res.exceptionDetails.text || 'Error evaluating TradingView close');
    }

    return res.result.value;
  } finally {
    try { await client.close(); } catch { /* ignore */ }
  }
}

/**
 * Draw a test horizontal line on chart
 */
async function executeDrawHorizontalLine({ price = null, text = 'ALERT TRIGGER' } = {}) {
  const { client } = await getTradingViewClient();
  try {
    const expr = `(async () => {
      const api = window.TradingViewApi && window.TradingViewApi._activeChartWidgetWV && window.TradingViewApi._activeChartWidgetWV.value();
      if (!api) return { success: false, error: "Active chart widget not found" };

      let targetPrice = ${Number(price) || 0};
      const nowSec = Math.floor(Date.now() / 1000);

      if (!targetPrice || isNaN(targetPrice)) {
        try {
          const bars = api._chartWidget.model().mainSeries().bars();
          const lastBar = bars.last();
          targetPrice = lastBar ? lastBar.value[4] : 0;
        } catch (e) {
          targetPrice = 0;
        }
      }

      if (!targetPrice) return { success: false, error: "Could not determine price for line" };

      const shapeId = api.createShape(
        { time: nowSec, price: targetPrice },
        {
          shape: "horizontal_line",
          overrides: {
            linecolor: "#00BCD4",
            linewidth: 2,
            linestyle: 0
          },
          text: ${JSON.stringify(text || 'WEBHOOK TEST')} + " @ " + targetPrice.toFixed(2)
        }
      );

      return {
        success: true,
        actionTaken: "line_drawn",
        price: targetPrice,
        shapeId: String(shapeId || 'drawn')
      };
    })()`;

    const res = await client.Runtime.evaluate({
      expression: expr,
      returnByValue: true,
      awaitPromise: true
    });

    if (res.exceptionDetails) {
      throw new Error(res.exceptionDetails.text || 'Error creating line shape');
    }

    return res.result.value;
  } finally {
    try { await client.close(); } catch { /* ignore */ }
  }
}

/**
 * Check current trading status without closing
 */
async function getTradingStatus() {
  try {
    const { client } = await getTradingViewClient();
    try {
      const expr = `(async () => {
        const t = window.TradingViewApi && window.TradingViewApi._tradingService && window.TradingViewApi._tradingService.trading();
        if (!t) return { tvConnected: true, brokerConnected: false };
        const bc = typeof t.brokerCommandsUI === 'function' ? t.brokerCommandsUI() : t._brokerCommandsUI;
        const broker = bc ? bc._activeBroker : null;
        if (!broker) return { tvConnected: true, brokerConnected: false };

        const positions = await broker.positions();
        const active = (positions || []).filter(p => Math.abs(p.qty || 0) > 0);
        return {
          tvConnected: true,
          brokerConnected: true,
          broker: broker.metainfo ? broker.metainfo().title : "Connected",
          openPositionsCount: active.length,
          positions: active.map(p => ({ id: p.id, symbol: p.symbol, qty: p.qty, side: p.side, avgPrice: p.avgPrice }))
        };
      })()`;

      const res = await client.Runtime.evaluate({
        expression: expr,
        returnByValue: true,
        awaitPromise: true
      });
      return res.result.value || {};
    } finally {
      try { await client.close(); } catch { /* ignore */ }
    }
  } catch (err) {
    return { tvConnected: false, error: err.message };
  }
}

// -------------------------------------------------------------
// HTTP Server
// -------------------------------------------------------------
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // GET / or /health
  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/health')) {
    const status = await getTradingStatus();
    const uptimeSec = Math.floor((Date.now() - startTime) / 1000);
    const hrs = Math.floor(uptimeSec / 3600);
    const mins = Math.floor((uptimeSec % 3600) / 60);
    const secs = uptimeSec % 60;

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ONLINE',
      uptime: `${hrs}h ${mins}m ${secs}s`,
      bridgePort: PORT,
      secretConfigured: Boolean(AUTH_SECRET),
      ...status
    }, null, 2));
    return;
  }

  // POST /webhook
  if (req.method === 'POST' && url.pathname === '/webhook') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      let payload = {};
      try {
        payload = body ? JSON.parse(body) : {};
      } catch {
        // Plain text fallback or form encoded
        payload = { raw: body };
      }

      const receivedSecret = payload.secret || req.headers['x-secret'] || url.searchParams.get('secret');

      // 1. Authenticate Secret
      if (AUTH_SECRET && receivedSecret !== AUTH_SECRET) {
        console.warn(`[${new Date().toISOString()}] ❌ 401 Unauthorized: Invalid secret rejected.`);
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'Unauthorized: Invalid secret' }));
        return;
      }

      console.log(`\n==================================================`);
      console.log(`📥 [${new Date().toLocaleTimeString()}] WEBHOOK RECEIVED:`, JSON.stringify(payload));

      const action = (payload.action || url.searchParams.get('action') || 'close').toLowerCase();
      const symbol = payload.symbol || payload.ticker || url.searchParams.get('symbol') || null;
      const all = payload.all === true || action === 'flatten_all' || url.searchParams.get('all') === 'true';

      if (action === 'close' || action === 'flatten' || action === 'flatten_all') {
        try {
          console.log(`⚡ Executing ${action} for symbol: ${symbol || 'ALL'}...`);
          const result = await executeClosePosition({ symbol, all });
          console.log('✅ Result:', JSON.stringify(result, null, 2));

          const closedCount = result.closedPositions ? result.closedPositions.length : 0;
          const msg = closedCount > 0 
            ? `Flattened ${closedCount} position(s) on ${result.broker}!` 
            : `No matching positions to close.`;

          sendMacNotification('Antigravity Trading Bridge', 'Webhook Triggered', msg);
          playSound(closedCount > 0 ? 'Glass' : 'Ping');

          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true, ...result }));
        } catch (err) {
          console.error('❌ Execution error:', err.message);
          sendMacNotification('Antigravity Trading Bridge', 'Execution Error', err.message);
          playSound('Basso');
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: false, error: err.message }));
        }
      } else if (action === 'draw_line' || action === 'test' || action === 'test_line') {
        try {
          const reqPrice = Number(payload.price || url.searchParams.get('price')) || null;
          const labelText = payload.text || url.searchParams.get('text') || 'ALERT TEST';
          console.log(`🎨 Executing draw_line at price: ${reqPrice || 'CURRENT'} with text: "${labelText}"...`);

          const result = await executeDrawHorizontalLine({ price: reqPrice, text: labelText });
          console.log('✅ Result:', JSON.stringify(result, null, 2));

          const msg = `Drew horizontal line @ ${result.price} on TradingView!`;
          sendMacNotification('Antigravity Trading Bridge', 'Test Webhook Fired', msg);
          playSound('Glass');

          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true, ...result }));
        } catch (err) {
          console.error('❌ Drawing error:', err.message);
          sendMacNotification('Antigravity Trading Bridge', 'Drawing Error', err.message);
          playSound('Basso');
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: false, error: err.message }));
        }
      } else {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: `Unknown action: ${action}` }));
      }
      console.log(`==================================================\n`);
    });
    return;
  }

  // 404
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not Found' }));
});

// -------------------------------------------------------------
// Start Server
// -------------------------------------------------------------
server.listen(PORT, '0.0.0.0', () => {
  console.log(`=======================================================`);
  console.log(`🚀 Antigravity TradingView Middle-Bridge Online`);
  console.log(`📡 Local Port:         http://localhost:${PORT}`);
  console.log(`🏥 Health Status:       http://localhost:${PORT}/health`);
  console.log(`🎯 Webhook Target:     http://localhost:${PORT}/webhook`);
  console.log(`🔐 Secret Protection:  ACTIVE`);
  console.log(`📊 TradingView Port:   ${CDP_PORT}`);
  console.log(`=======================================================`);

  // Pop initial startup banner
  sendMacNotification(
    'Antigravity Trading Bridge',
    'Bridge Online & Listening',
    `Listening on port ${PORT}. Ready to receive TradingView alerts.`
  );
});
