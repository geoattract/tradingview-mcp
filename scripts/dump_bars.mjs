#!/usr/bin/env node
import fs from 'node:fs';
import CDP from 'chrome-remote-interface';

async function main() {
  const targets = await CDP.List({ host: '127.0.0.1', port: 9222 });
  const tvTarget = targets.find(t => t.url && t.url.includes('tradingview.com'));
  if (!tvTarget) {
    console.error('TradingView target not found in CDP list');
    process.exit(1);
  }

  const client = await CDP({ target: tvTarget });
  const { Runtime } = client;
  await Runtime.enable();

  console.log('Connected to TradingView target:', tvTarget.title);

  const evalResult = await Runtime.evaluate({
    expression: `(function() {
      var chart = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget;
      var ms = chart.model().mainSeries();
      var bars = ms.bars();
      var firstIdx = bars.firstIndex();
      var lastIdx = bars.lastIndex();
      var res = [];
      for (var i = firstIdx; i <= lastIdx; i++) {
        var v = bars.valueAt(i);
        if (v) {
          res.push([v[0], v[1], v[2], v[3], v[4], v[5] || 0]);
        }
      }
      return JSON.stringify({ count: res.length, bars: res });
    })()`,
    returnByValue: true
  });

  if (evalResult.exceptionDetails) {
    console.error('Evaluation error:', evalResult.exceptionDetails);
    await client.close();
    process.exit(1);
  }

  const parsed = JSON.parse(evalResult.result.value);
  console.log(`Extracted ${parsed.count} bars!`);
  
  // Format as list of objects
  const barObjects = parsed.bars.map(b => ({
    time: b[0],
    open: b[1],
    high: b[2],
    low: b[3],
    close: b[4],
    volume: b[5]
  }));

  fs.writeFileSync('tests/mgc1_5m_all.json', JSON.stringify(barObjects, null, 2));
  console.log('Saved to tests/mgc1_5m_all.json');

  const firstDate = new Date(parsed.bars[0][0] * 1000).toISOString();
  const lastDate = new Date(parsed.bars[parsed.bars.length - 1][0] * 1000).toISOString();
  console.log(`First bar: ${firstDate}`);
  console.log(`Last bar:  ${lastDate}`);

  await client.close();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
