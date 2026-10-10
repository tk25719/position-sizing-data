# Gain needed to recover from a drawdown

Recovery is not symmetrical: the gain required is `1 / (1 - drawdown) - 1`, so a 50% drawdown needs a 100% gain, not a 50% gain.

| drawdown_pct | gain_required_pct_to_recover |
| --- | --- |
| 5% | 5.3% |
| 10% | 11.1% |
| 15% | 17.6% |
| 20% | 25.0% |
| 25% | 33.3% |
| 30% | 42.9% |
| 40% | 66.7% |
| 50% | 100.0% |
| 60% | 150.0% |
| 70% | 233.3% |
| 80% | 400.0% |
| 90% | 900.0% |

Machine-readable source: [`data/drawdown-recovery.csv`](../data/drawdown-recovery.csv)
