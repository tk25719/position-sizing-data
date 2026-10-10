#!/usr/bin/env python3
"""Run with:  python tests/test_position_size.py   (no pytest needed)

Every expected number here can be checked by hand from the formula
    units = floor( (account * risk% - commission) / ((stop_distance + spread) * contract_size) * contract_size / step ) * step
so nothing in this file is a recorded output - it is arithmetic written down.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

from position_size import load_specs, size_position  # noqa: E402

SPECS = load_specs()
CASES = [
    # name, symbol, account, risk%, distance, spread_pips, commission, expected units
    ("20 pip stop on 10k EUR/USD at 1%", "EUR/USD", 10000, 1, 0.0020, 0, 0, 50000),
    # 0.0020 + 3 pips = 0.0023 -> 230 per lot; budget 95 -> 41304 raw -> 41000
    ("same but 3 pip spread + 5 commission", "EUR/USD", 10000, 1, 0.0020, 3, 5, 41000),
    ("gold, 150 pip stop, 2% of 5k", "XAU/USD", 5000, 2, 1.50, 0, 0, 66),
    ("US30, 50 point stop, 1% of 10k, 1 spread 6 commission", "US30", 10000, 1, 50, 1, 6, 1),
    ("BTC, 1500 dollar stop, 1% of 2k", "BTCUSDT", 2000, 1, 1500, 0, 0, 0.013),
    ("commission larger than the risk budget", "EUR/USD", 100, 1, 0.0020, 0, 5, 0),
]

fails = 0
for name, sym, acct, risk, dist, spread, comm, want in CASES:
    got = size_position(SPECS[sym], acct, risk, dist, spread, comm)
    ok = abs(got["units"] - want) < 1e-9 and got["exhausted"] == (want == 0)
    print("%-58s want %-10g got %-10g %s" % (name, want, got["units"], "OK" if ok else "FAIL"))
    if not ok:
        fails += 1

# rounding never goes above the budget
for sym in ("EUR/USD", "XAU/USD", "US30", "BTCUSDT"):
    s = SPECS[sym]
    for dist in (0.0005, 0.0020, 0.0137, 1.5, 37.0):
        r = size_position(s, 10000, 1, dist, 0, 0)
        if r["loss_at_stop"] > r["risk_amount"] + 1e-9:
            print("FAIL %s dist=%g loss %g > risk %g" % (sym, dist, r["loss_at_stop"], r["risk_amount"]))
            fails += 1

print("\n%d checks failed" % fails)
sys.exit(1 if fails else 0)
