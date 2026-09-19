# position-sizing-data

Reference data and arithmetic for risk-based position sizing across forex, stocks and crypto futures. Zero dependencies.

The same tables are published as a citable dataset: [doi:10.5281/zenodo.22840538](https://doi.org/10.5281/zenodo.22840538), and used by the web calculator at [https://positionsizetool.com/](https://positionsizetool.com/). Source repository: [https://github.com/tk25719/position-sizing-data](https://github.com/tk25719/position-sizing-data).

## Install

```console
npm install position-sizing-data
```

## What is in it

| Function | Returns |
| --- | --- |
| `contractSpecifications()` | Pip size, contract size and minimum unit step for 131 instruments, across forex pairs, metals, energies, indices, crypto futures, stocks and ETFs. |
| `pipValues()` | Pip value and the loss on a 20 pip move for standard, mini, micro and nano lots. |
| `losingStreakEquity()` | Equity remaining after 1 to 20 consecutive losses at 0.5%, 1% and 2% risk per trade. |
| `drawdownRecovery()` | Gain required on the reduced balance to return to the original balance, for drawdowns from 5% to 90%. |
| `positionSize(options)` | The risk-to-units calculation itself. |
| `loadCsv(fileName)` | Any of the four CSV files as an array of plain objects. |

Read the tables:

```js
const { contractSpecifications } = require("position-sizing-data");

const rows = contractSpecifications();
console.log(rows.length); // 131
console.log(rows[0]); // { symbol: 'EUR/USD', asset_class: 'forex', ... }
```

Compute a size:

```js
const { positionSize } = require("position-sizing-data");

const r = positionSize({
  balance: 10000,
  riskPercent: 1,
  entry: 1.1,
  stop: 1.098,
  unitStep: 1000 // 0.01 lot
});

console.log(r);
// { riskBudget: 100, units: 50000, tradableUnits: 50000, worstCaseLoss: 100 }
```

Spread, commission and a quote-to-account rate all belong in the call:

```js
positionSize({
  balance: 5000,
  riskPercent: 0.5,
  entry: 150.25,
  stop: 149.95,
  quoteRate: 0.0066, // USD/JPY, account in USD
  spread: 0.02,
  commission: 2.5,
  unitStep: 1000
});
```

## The formula

```
units = (riskBudget - commission) / ((|entry - stop| + spread) x quoteRate)
```

The tradable size is that number rounded **down** to `unitStep`, and `worstCaseLoss` is recomputed from the rounded size. That last part is the point: it is what the account actually loses when the stop is hit.

Rounding down has one trap that this library handles. `100 / (0.002 x 1)` evaluates to `49999.999999999956` in IEEE 754 floating point, and a naive `Math.floor(units / step) * step` would drop 50,000 units to 49,000 — a whole step lost to representation error. `floorToStep()` treats anything within a tolerance of a step boundary as that boundary, so the answer stays 50,000. It still never rounds up above the raw size.

## Where the numbers come from

The rows in `contractSpecifications()` are typical retail contract specifications, not exchange-published official values. Verify the contract size and unit step against your own broker before placing an order. The other three tables are closed-form arithmetic:

- losing streak: `remaining = (1 - risk)^n`
- drawdown recovery: `gain_required = 1 / (1 - drawdown) - 1`
- pip value: `pip_value = units x pip_size`

## Licence

MIT for the code. Data files are CC0 1.0 Universal, to the extent applicable. This is not investment advice.
