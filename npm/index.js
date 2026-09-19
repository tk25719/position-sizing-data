"use strict";

/**
 * Reference data and arithmetic for risk-based position sizing.
 *
 * Mirrors the Zenodo dataset 10.5281/zenodo.22840538 and the web calculator at
 * https://positionsizetool.com/. No dependencies.
 */

const fs = require("fs");
const path = require("path");

const DATA_DIR = path.join(__dirname, "data");

const DATA_FILES = {
  "contract-specifications.csv": "contractSpecifications",
  "pip-value-by-lot-size.csv": "pipValues",
  "losing-streak-equity.csv": "losingStreakEquity",
  "drawdown-recovery.csv": "drawdownRecovery"
};

/**
 * Round SIZE down to a whole number of steps.
 *
 * A plain floor loses one entire step when floating point lands just below a
 * boundary: 100 / (0.002 x 1) evaluates to 49999.999999999956, and flooring to
 * a step of 1000 would drop 50000 to 49000. Any value that is within a
 * tolerance of a step boundary is therefore treated as that boundary.
 */
function floorToStep(value, step) {
  const ratio = value / step;
  const nearest = Math.round(ratio);
  const tolerance = 1e-9 * Math.max(1, Math.abs(nearest));
  const steps = Math.abs(ratio - nearest) < tolerance ? nearest : Math.floor(ratio);
  return steps * step;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
      continue;
    }
    if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field);
      field = "";
      rows.push(row);
      row = [];
    } else if (ch !== "\r") {
      field += ch;
    }
  }
  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((r) => r.some((c) => c !== ""));
}

function loadCsv(fileName) {
  if (!Object.prototype.hasOwnProperty.call(DATA_FILES, fileName)) {
    throw new Error("unknown data file: " + fileName);
  }
  const raw = fs.readFileSync(path.join(DATA_DIR, fileName), "utf8").replace(/^\uFEFF/, "");
  const rows = parseCsv(raw);
  if (rows.length === 0) {
    return [];
  }
  const header = rows[0];
  return rows.slice(1).map((cells) => {
    const record = {};
    header.forEach((key, idx) => {
      record[key] = cells[idx] === undefined ? "" : cells[idx];
    });
    return record;
  });
}

function contractSpecifications() {
  return loadCsv("contract-specifications.csv");
}

function pipValues() {
  return loadCsv("pip-value-by-lot-size.csv");
}

function losingStreakEquity() {
  return loadCsv("losing-streak-equity.csv");
}

function drawdownRecovery() {
  return loadCsv("drawdown-recovery.csv");
}

/**
 * Convert a risk budget into a tradable unit count.
 *
 * units = (riskBudget - commission) / ((|entry - stop| + spread) * quoteRate)
 * rounded DOWN to unitStep, with the worst-case loss recomputed from the
 * rounded size.
 */
function positionSize(options) {
  const opts = options || {};
  const balance = Number(opts.balance);
  const riskPercent = Number(opts.riskPercent);
  const entry = Number(opts.entry);
  const stop = Number(opts.stop);
  const spread = opts.spread === undefined ? 0 : Number(opts.spread);
  const commission = opts.commission === undefined ? 0 : Number(opts.commission);
  const quoteRate = opts.quoteRate === undefined ? 1 : Number(opts.quoteRate);
  const unitStep = opts.unitStep === undefined ? 0.01 : Number(opts.unitStep);

  [balance, riskPercent, entry, stop, spread, commission, quoteRate, unitStep].forEach((v) => {
    if (!Number.isFinite(v)) {
      throw new Error("position size inputs must be finite numbers");
    }
  });

  const stopDistance = Math.abs(entry - stop) + spread;
  if (stopDistance <= 0) {
    throw new Error("stop distance must be greater than zero");
  }
  if (quoteRate <= 0) {
    throw new Error("quoteRate must be greater than zero");
  }
  if (unitStep <= 0) {
    throw new Error("unitStep must be greater than zero");
  }

  const budget = (balance * riskPercent) / 100;
  const units = (budget - commission) / (stopDistance * quoteRate);
  const roundedUnits = floorToStep(units, unitStep);
  return { riskBudget: budget, units: units, tradableUnits: roundedUnits, worstCaseLoss: roundedUnits * stopDistance * quoteRate + commission };
}

module.exports = {
  loadCsv,
  contractSpecifications,
  pipValues,
  losingStreakEquity,
  drawdownRecovery,
  positionSize,
  floorToStep
};
