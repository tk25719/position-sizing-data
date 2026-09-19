"use strict";

// Smoke test: every documented function must run and produce sane numbers.
// Run with: npm test

const assert = require("assert");
const pkg = require("../index.js");

function near(actual, expected, label) {
  assert.ok(Math.abs(actual - expected) < 1e-9, label + ": expected ~" + expected + ", got " + actual);
}

function run() {
  const specs = pkg.contractSpecifications();
  assert.ok(specs.length === 131, "expected 131 instrument rows, got " + specs.length);
  assert.ok(specs[0].symbol, "first row has no symbol");

  const pips = pkg.pipValues();
  assert.ok(pips.length === 4, "expected 4 lot rows, got " + pips.length);

  const streaks = pkg.losingStreakEquity();
  assert.ok(streaks.length === 20, "expected 20 streak rows, got " + streaks.length);

  const recovery = pkg.drawdownRecovery();
  assert.ok(recovery.length === 12, "expected 12 recovery rows, got " + recovery.length);

  // 10,000 balance, 1% risk, 20 pip stop at 1 pip of value -> budget 100
  const r1 = pkg.positionSize({ balance: 10000, riskPercent: 1, entry: 1.1, stop: 1.098, unitStep: 1000 });
  near(r1.riskBudget, 100, "riskBudget");
  near(r1.units, 50000, "units");
  near(r1.tradableUnits, 50000, "tradableUnits");
  near(r1.worstCaseLoss, 100, "worstCaseLoss");

  // floating point lands just below the step boundary; it must not lose a step
  near(pkg.floorToStep(49999.999999999956, 1000), 50000, "floorToStep boundary");
  near(pkg.floorToStep(1.9399999, 0.01), 1.93, "floorToStep rounds down");
  assert.strictEqual(pkg.floorToStep(0, 0.01), 0);

  // rounding down must not increase risk: step forces 1.934 -> 1.93
  const r2 = pkg.positionSize({ balance: 100000, riskPercent: 1, entry: 1.1, stop: 1.095, unitStep: 0.01 });
  const tol2 = 1e-9 * Math.max(1, Math.abs(r2.units));
  assert.ok(r2.tradableUnits <= r2.units + tol2, "rounded size must never exceed raw size by more than float noise");
  assert.ok(r2.worstCaseLoss <= r2.riskBudget + 1e-9 * Math.max(1, Math.abs(r2.riskBudget)), "rounded size must stay inside the budget");

  // spread and commission eat into the size
  const r3 = pkg.positionSize({
    balance: 10000,
    riskPercent: 1,
    entry: 1.1,
    stop: 1.098,
    spread: 0.0001,
    commission: 10,
    unitStep: 1000
  });
  assert.ok(r3.units < r1.units, "spread and commission must reduce the unit count");
  assert.ok(
    r3.worstCaseLoss <= r3.riskBudget + 1e-9 * Math.max(1, Math.abs(r3.riskBudget)),
    "worst case must stay inside the budget"
  );

  assert.throws(() => pkg.positionSize({ balance: 1000, riskPercent: 1, entry: 1.1, stop: 1.1 }), /stop distance/);
  assert.throws(() => pkg.loadCsv("nope.csv"), /unknown data file/);

  console.log("smoke test OK: 131 instruments, 4 lot rows, 20 streak rows, 12 recovery rows, sizes stay inside budget");
}

run();
