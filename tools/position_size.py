#!/usr/bin/env python3
"""Position sizing from a fixed account risk.

Answer the question every sizing calculator is really answering:
given an account, a risk percentage and a stop distance, how much can I put on?

The instrument maths come from data/contract-specifications.csv
(pip size, contract size, minimum step), so the same function works
for a forex pair, a gold CFD, an index or a crypto pair.

Usage
-----
    python position_size.py --list
    python position_size.py --symbol EUR/USD --account 10000 --risk 1 \
        --entry 1.1000 --stop 1.0980
    python position_size.py --symbol XAU/USD --account 5000 --risk 2 \
        --pips 150 --spread-pips 3 --commission 4

No dependencies beyond the standard library. Python 3.8+.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "contract-specifications.csv")


def load_specs(path: str = DATA) -> dict:
    """Read the contract spec file into {SYMBOL: {...}} with floats applied."""
    specs = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            specs[row["symbol"].strip()] = {
                "asset_class": row["asset_class"].strip(),
                "quote_currency": row["quote_currency"].strip(),
                "pip_size": float(row["pip_size"]),
                "contract_size": float(row["contract_size"]),
                "unit_step": float(row["unit_step"]),
            }
    return specs


def size_position(
    spec: dict,
    account: float,
    risk_pct: float,
    price_distance: float,
    spread_pips: float = 0.0,
    commission: float = 0.0,
) -> dict:
    """Return the position that risks at most ``risk_pct`` percent of ``account``.

    price_distance
        Distance from entry to stop, in price units (not pips).
        For EUR/USD a 20 pip stop is 0.0020.
    spread_pips
        Broker spread in pips. It widens the loss per lot, so it shrinks the size.
    commission
        Flat cost in quote currency, paid out of the risk budget.

    The whole loss per lot is ``(price_distance + spread) * contract_size``:
    one lot moves one price unit per ``contract_size`` units of exposure.
    """
    if account <= 0:
        raise ValueError("account must be positive")
    if not 0 < risk_pct < 100:
        raise ValueError("risk_pct must be between 0 and 100 (exclusive)")
    if price_distance is None or price_distance <= 0:
        raise ValueError("stop distance must be greater than zero")

    pip_size = spec["pip_size"]
    contract_size = spec["contract_size"]
    step = spec["unit_step"]

    # Prices arrive as decimals; 1.1000 - 1.0980 is 0.0020000000000000018 in
    # binary floating point. Snap the distance before it costs a whole step.
    distance = round(price_distance + spread_pips * pip_size, 10)
    if distance <= 0:
        raise ValueError("stop distance must be greater than zero")

    loss_per_lot = distance * contract_size
    if loss_per_lot <= 0:
        raise ValueError("loss per lot is not positive - check the contract spec")

    budget = account * risk_pct / 100.0 - commission
    if budget <= 0:
        # Costs eat the whole risk budget: nothing is left to put on.
        return {
            "units": 0.0,
            "lots": 0.0,
            "risk_amount": account * risk_pct / 100.0,
            "loss_per_lot": loss_per_lot,
            "loss_at_stop": 0.0,
            "notional_at_entry": 0.0,
            "raw_units": 0.0,
            "step": step,
            "budget": budget,
            "exhausted": True,
        }

    raw_units = budget / loss_per_lot * contract_size
    # Brokers only accept whole steps; always round towards zero, never up.
    units = math.floor(raw_units / step) * step
    lots = units / contract_size
    loss_at_stop = (units / contract_size) * loss_per_lot

    return {
        "units": units,
        "lots": lots,
        "risk_amount": account * risk_pct / 100.0,
        "loss_per_lot": loss_per_lot,
        "loss_at_stop": loss_at_stop,
        "raw_units": raw_units,
        "step": step,
        "budget": budget,
        "exhausted": False,
    }


def pips_to_price(spec: dict, pips: float) -> float:
    return pips * spec["pip_size"]


def main(argv=None) -> int:
    specs = load_specs()
    ap = argparse.ArgumentParser(description="Position size from a fixed account risk.")
    ap.add_argument("--symbol", help="Symbol as written in data/contract-specifications.csv")
    ap.add_argument("--account", type=float, help="Account balance in quote currency")
    ap.add_argument("--risk", type=float, help="Risk per trade, percent of the account")
    ap.add_argument("--entry", type=float, help="Entry price")
    ap.add_argument("--stop", type=float, help="Stop price")
    ap.add_argument("--pips", type=float, help="Stop distance in pips (instead of --entry/--stop)")
    ap.add_argument("--spread-pips", type=float, default=0.0, help="Broker spread in pips")
    ap.add_argument("--commission", type=float, default=0.0, help="Round-trip commission")
    ap.add_argument("--price", type=float, help="Price used for the notional figure")
    ap.add_argument("--list", action="store_true", help="Print every known symbol and exit")
    args = ap.parse_args(argv)

    if args.list:
        for sym, s in specs.items():
            print(
                "%-22s %-8s pip=%-8g contract=%-8g step=%g"
                % (sym, s["asset_class"], s["pip_size"], s["contract_size"], s["unit_step"])
            )
        return 0

    if not args.symbol:
        ap.error("--symbol is required (or use --list)")
    key = args.symbol.strip()
    if key not in specs:
        close = [s for s in specs if key.upper() in s.upper()]
        hint = ("  Did you mean: " + ", ".join(close[:8])) if close else ""
        sys.exit("Unknown symbol %r.%s" % (args.symbol, hint))

    spec = specs[key]
    if args.pips is not None:
        distance = pips_to_price(spec, args.pips)
        pips = args.pips
    else:
        if args.entry is None or args.stop is None:
            ap.error("give either --pips or both --entry and --stop")
        distance = abs(args.entry - args.stop)
        pips = distance / spec["pip_size"]

    try:
        r = size_position(spec, args.account, args.risk, distance, args.spread_pips, args.commission)
    except ValueError as exc:
        sys.exit("cannot size: %s" % exc)

    price = args.price if args.price else (args.entry or 0.0)
    notional = r["units"] * price

    print("Symbol            %s (%s, quoted in %s)" % (key, spec["asset_class"], spec["quote_currency"]))
    print("Account           %.2f" % args.account)
    print("Risk per trade    %.4g%%  =  %.2f" % (args.risk, r["risk_amount"]))
    print("Stop distance     %.6g price units  =  %.4g pips" % (distance, pips))
    if args.spread_pips:
        print("Spread            %.4g pips (added to the stop distance)" % args.spread_pips)
    if args.commission:
        print("Commission        %.2f (taken out of the risk budget)" % args.commission)
    print("Loss per 1.0 lot  %.2f" % r["loss_per_lot"])
    print("-")
    if r["exhausted"]:
        print("Position size     0")
        print("  Costs take the whole risk budget: %.2f of costs against %.2f of risk."
              % (args.commission, r["risk_amount"]))
        return 0
    print("Position size     %g units  =  %.4g lots" % (r["units"], r["lots"]))
    print("Raw (unrounded)   %.6g units -> rounded down to the %.6g step" % (r["raw_units"], r["step"]))
    if price:
        print("Notional at entry %.2f" % notional)
    print("Loss if stopped   %.2f" % r["loss_at_stop"])
    if args.commission:
        print("Total worst case  %.2f (loss + commission)" % (r["loss_at_stop"] + args.commission))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
