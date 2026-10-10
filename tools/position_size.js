#!/usr/bin/env node
/**
 * Position sizing from a fixed account risk - the browser/node twin of
 * tools/position_size.py. Same inputs, same rounding rule, same output.
 *
 *   node position_size.js --symbol EUR/USD --account 10000 --risk 1 \
 *        --entry 1.1000 --stop 1.0980
 *
 * No dependencies.
 */

const fs = require('fs');
const path = require('path');

const DATA = path.join(__dirname, '..', 'data', 'contract-specifications.csv');

function loadSpecs(file = DATA) {
  const lines = fs.readFileSync(file, 'utf8').trim().split(/\r?\n/);
  const head = lines.shift().split(',');
  const specs = {};
  for (const line of lines) {
    if (!line.trim()) continue;
    const row = line.split(',');
    const o = {};
    head.forEach((k, i) => (o[k.trim()] = (row[i] || '').trim()));
    specs[o.symbol] = {
      asset_class: o.asset_class,
      quote_currency: o.quote_currency,
      pip_size: Number(o.pip_size),
      contract_size: Number(o.contract_size),
      unit_step: Number(o.unit_step),
    };
  }
  return specs;
}

/**
 * @param spec  {pip_size, contract_size, unit_step}
 * @param account        balance in quote currency
 * @param riskPct        percent of the account put at risk (0 < riskPct < 100)
 * @param priceDistance  entry to stop, in price units (not pips)
 * @param spreadPips     broker spread, in pips
 * @param commission     round-trip cost, in quote currency
 */
function sizePosition(spec, account, riskPct, priceDistance, spreadPips = 0, commission = 0) {
  if (!(account > 0)) throw new Error('account must be positive');
  if (!(riskPct > 0 && riskPct < 100)) throw new Error('risk_pct must be between 0 and 100');
  if (!(priceDistance > 0)) throw new Error('stop distance must be greater than zero');

  // 1.1000 - 1.0980 is 0.0020000000000000018 in binary floating point.
  // Snap the distance before it costs a whole step.
  const distance = Math.round((priceDistance + spreadPips * spec.pip_size) * 1e10) / 1e10;
  const lossPerLot = distance * spec.contract_size;
  if (!(lossPerLot > 0)) throw new Error('loss per lot is not positive');

  const riskAmount = (account * riskPct) / 100;
  const budget = riskAmount - commission;
  if (budget <= 0) {
    return { units: 0, lots: 0, riskAmount, lossPerLot, lossAtStop: 0, exhausted: true };
  }

  const rawUnits = (budget / lossPerLot) * spec.contract_size;
  const units = Math.floor(rawUnits / spec.unit_step) * spec.unit_step;
  const lots = units / spec.contract_size;
  return {
    units,
    lots,
    riskAmount,
    lossPerLot,
    lossAtStop: lots * lossPerLot,
    rawUnits,
    exhausted: false,
  };
}

module.exports = { loadSpecs, sizePosition };

if (require.main === module) {
  const argv = process.argv.slice(2);
  const arg = (name, def = null) => {
    const i = argv.indexOf('--' + name);
    return i >= 0 ? argv[i + 1] : def;
  };
  if (argv.includes('--list')) {
    const specs = loadSpecs();
    for (const [sym, s] of Object.entries(specs)) {
      console.log(`${sym.padEnd(22)} ${s.asset_class.padEnd(8)} pip=${s.pip_size} contract=${s.contract_size} step=${s.unit_step}`);
    }
    process.exit(0);
  }
  const specs = loadSpecs();
  const symbol = arg('symbol');
  if (!symbol || !specs[symbol]) {
    console.error(`Unknown or missing --symbol ${symbol}`);
    process.exit(1);
  }
  const spec = specs[symbol];
  const pips = arg('pips');
  const distance = pips != null ? Number(pips) * spec.pip_size : Math.abs(Number(arg('entry')) - Number(arg('stop')));
  const r = sizePosition(
    spec,
    Number(arg('account')),
    Number(arg('risk')),
    distance,
    Number(arg('spread-pips', 0) || 0),
    Number(arg('commission', 0) || 0)
  );
  console.log(`Symbol            ${symbol} (${spec.asset_class}, quoted in ${spec.quote_currency})`);
  console.log(`Risk per trade    ${arg('risk')}%  =  ${r.riskAmount.toFixed(2)}`);
  console.log(`Stop distance     ${distance} price units  =  ${(distance / spec.pip_size).toFixed(4)} pips`);
  console.log(`Loss per 1.0 lot  ${r.lossPerLot.toFixed(2)}`);
  if (r.exhausted) {
    console.log('Position size     0  (costs take the whole risk budget)');
  } else {
    console.log(`Position size     ${r.units} units  =  ${r.lots} lots`);
    console.log(`Loss if stopped   ${r.lossAtStop.toFixed(2)}`);
  }
}
