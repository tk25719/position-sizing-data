"""Tests for the packaged tables and for the one formula that rounds sizes down.

Run with ``python -m pytest`` from the ``pypi`` directory, or ``python -m
unittest discover -s tests`` without pytest installed.
"""

import math
import unittest

from position_sizing_data import (
    contract_specifications,
    drawdown_recovery,
    floor_to_step,
    losing_streak_equity,
    pip_values,
    position_size,
)


def percent(text: str) -> float:
    """Parse the ``"99.00%"`` style values used in the published tables."""
    return float(text.strip().rstrip("%"))


class TestFloorToStep(unittest.TestCase):
    def test_float_edge_does_not_collapse(self):
        """The bug this package shipped with in 0.1.0.

        10,000 USD at 1% risk over a 20 pip stop is exactly 50,000 units, but
        the division returns 49.999999999999956. A naive floor turns that into
        49,000 and the trader loses a whole mini lot without being told.
        """
        self.assertEqual(floor_to_step(49999.999999999956, 1000.0), 50000.0)

    def test_never_rounds_up(self):
        self.assertEqual(floor_to_step(49999.0, 1000.0), 49000.0)
        self.assertEqual(floor_to_step(50500.0, 1000.0), 50000.0)
        self.assertEqual(floor_to_step(0.999, 1.0), 0.0)

    def test_exact_multiples_are_unchanged(self):
        for value in (0.0, 1000.0, 50000.0, 123000.0):
            self.assertEqual(floor_to_step(float(value), 1000.0), float(value))

    def test_fractional_steps(self):
        self.assertAlmostEqual(floor_to_step(1.239, 0.01), 1.23, places=9)
        self.assertAlmostEqual(floor_to_step(1.2000000000000002, 0.01), 1.20, places=9)

    def test_zero_step_rejected(self):
        with self.assertRaises(ValueError):
            floor_to_step(100.0, 0.0)


class TestPositionSize(unittest.TestCase):
    def test_worked_example_from_the_documentation(self):
        result = position_size(
            balance=10000.0,
            risk_percent=1.0,
            entry=1.1000,
            stop=1.0980,
            unit_step=1000.0,
        )
        self.assertEqual(result["tradable_units"], 50000.0)
        self.assertAlmostEqual(result["risk_budget"], 100.0, places=9)

    def test_worst_case_loss_stays_inside_the_budget(self):
        params = dict(
            balance=10000.0,
            risk_percent=1.0,
            entry=1.1000,
            stop=1.0980,
            unit_step=1000.0,
        )
        result = position_size(**params)
        self.assertLessEqual(result["worst_case_loss"], result["risk_budget"] + 1e-9)

    def test_commission_is_taken_out_of_the_budget(self):
        base = position_size(10000.0, 1.0, 1.1000, 1.0980, unit_step=1000.0)
        with_fee = position_size(
            10000.0, 1.0, 1.1000, 1.0980, commission=7.0, unit_step=1000.0
        )
        self.assertLess(with_fee["tradable_units"], base["tradable_units"])

    def test_quote_rate_scales_the_result(self):
        usd = position_size(10000.0, 1.0, 1.1000, 1.0980, unit_step=1000.0)
        jpy = position_size(
            10000.0, 1.0, 1.1000, 1.0980, quote_rate=150.0, unit_step=1000.0
        )
        self.assertEqual(jpy["tradable_units"], 0.0)
        self.assertAlmostEqual(
            jpy["units"] * 150.0, usd["units"], delta=abs(usd["units"]) * 1e-9
        )

    def test_bad_inputs_rejected(self):
        with self.assertRaises(ValueError):
            position_size(10000.0, 1.0, 1.1000, 1.1000, unit_step=1000.0)
        with self.assertRaises(ValueError):
            position_size(10000.0, 1.0, 1.1000, 1.0980, quote_rate=0.0)
        with self.assertRaises(ValueError):
            position_size(10000.0, 1.0, 1.1000, 1.0980, unit_step=0.0)


class TestTables(unittest.TestCase):
    def test_row_counts(self):
        self.assertEqual(len(contract_specifications()), 131)
        self.assertEqual(len(pip_values()), 4)
        self.assertEqual(len(losing_streak_equity()), 20)
        self.assertEqual(len(drawdown_recovery()), 12)

    def test_recovery_math_is_right(self):
        """gain_required = 1 / (1 - drawdown) - 1.

        The published column is rounded to one decimal place, so this checks
        against the formula with a half-of-last-digit tolerance rather than
        exact equality.
        """
        for row in drawdown_recovery():
            drawdown = percent(row["drawdown_pct"]) / 100.0
            expected = (1.0 / (1.0 - drawdown) - 1.0) * 100.0
            self.assertAlmostEqual(
                percent(row["gain_required_pct_to_recover"]), expected, delta=0.06
            )

    def test_streak_math_is_right(self):
        """remaining = (1 - risk%)^n, checked on the 1% column."""
        for row in losing_streak_equity():
            n = int(row["consecutive_losses"])
            expected = (1.0 - 0.01) ** n * 100.0
            self.assertAlmostEqual(
                percent(row["equity_remaining_1pct"]), expected, delta=0.06
            )


if __name__ == "__main__":
    unittest.main()
