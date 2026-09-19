"""Reference data and arithmetic for risk-based position sizing.

This package ships the same CSV tables and the same risk-to-units formula that
are published as the Zenodo dataset 10.5281/zenodo.22840538 and used by the web
calculator at https://positionsizetool.com/.

The tables are plain data. The one function that computes something,
``position_size``, implements the formula::

    units = (risk_budget - commission) / ((|entry - stop| + spread) x rate)

and rounds the result DOWN to the instrument's minimum unit step, because
rounding up raises risk without showing it anywhere.
"""

from __future__ import annotations

import csv
import math
from importlib import resources
from typing import Dict, List

__version__ = "0.1.1"

__all__ = [
    "load_csv",
    "contract_specifications",
    "pip_values",
    "losing_streak_equity",
    "drawdown_recovery",
    "floor_to_step",
    "position_size",
]


def floor_to_step(value: float, step: float) -> float:
    """Round ``value`` DOWN to a whole multiple of ``step``.

    A naive ``math.floor(value / step) * step`` is wrong at the edges: with a
    10,000 USD account, 1% risk, a 20 pip stop and a 1,000 unit step, the exact
    answer is 50,000 units, but the division yields 49.999999999999956 and the
    naive floor collapses it to 49,000. That silently cuts the trade by a whole
    mini lot.

    Anything sitting within a rounding hair of the next step is treated as that
    step. Nothing is ever rounded up beyond that tolerance, so the result can
    still be smaller than the raw unit count, never larger.
    """
    if step <= 0:
        raise ValueError("step must be greater than zero")
    quotient = value / step
    nearest = round(quotient)
    tolerance = 1e-9 * max(1.0, abs(nearest))
    if abs(quotient - nearest) < tolerance:
        steps = float(nearest)
    else:
        steps = float(math.floor(quotient))
    return steps * step

CSV_FILES = {
    "contract-specifications.csv",
    "pip-value-by-lot-size.csv",
    "losing-streak-equity.csv",
    "drawdown-recovery.csv",
}


def load_csv(name: str) -> List[Dict[str, str]]:
    """Return one of the packaged CSV files as a list of dicts."""
    if name not in CSV_FILES:
        raise ValueError("unknown data file: " + name)
    resource = resources.files(__package__).joinpath("data", name)
    text = resource.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    return [dict(row) for row in reader]


def contract_specifications() -> List[Dict[str, str]]:
    """Pip size, contract size and minimum step per instrument (131 rows)."""
    return load_csv("contract-specifications.csv")


def pip_values() -> List[Dict[str, str]]:
    """Pip value and loss on a 20 pip move for standard, mini, micro and nano lots."""
    return load_csv("pip-value-by-lot-size.csv")


def losing_streak_equity() -> List[Dict[str, str]]:
    """Equity remaining after n consecutive losses at 0.5%, 1% and 2% risk."""
    return load_csv("losing-streak-equity.csv")


def drawdown_recovery() -> List[Dict[str, str]]:
    """Gain required on the reduced balance to return to the original balance."""
    return load_csv("drawdown-recovery.csv")


def position_size(
    balance: float,
    risk_percent: float,
    entry: float,
    stop: float,
    spread: float = 0.0,
    commission: float = 0.0,
    quote_rate: float = 1.0,
    unit_step: float = 0.01,
) -> Dict[str, float]:
    """Convert a risk budget into a tradable unit count.

    ``balance`` and ``commission`` are in account currency. ``risk_percent`` is
    expressed as a number (1 means 1%). ``quote_rate`` converts one unit of the
    quote currency into account currency; leave it at 1.0 when they are the
    same. ``unit_step`` is the broker's minimum increment.

    The returned ``worst_case_loss`` is recomputed from the ROUNDED size, which
    is the number that actually matters: it is what the account loses if the
    stop is hit.
    """
    budget = balance * risk_percent / 100.0
    stop_distance = abs(entry - stop) + spread
    if stop_distance <= 0:
        raise ValueError("stop distance must be greater than zero")
    if quote_rate <= 0:
        raise ValueError("quote_rate must be greater than zero")
    if unit_step <= 0:
        raise ValueError("unit_step must be greater than zero")
    units = (budget - commission) / (stop_distance * quote_rate)
    tradable = floor_to_step(units, unit_step)
    worst_case = tradable * stop_distance * quote_rate + commission
    return {
        "risk_budget": budget,
        "units": units,
        "tradable_units": tradable,
        "worst_case_loss": worst_case,
    }
