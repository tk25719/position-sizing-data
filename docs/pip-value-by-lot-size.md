# Pip value by lot size

What one pip is worth at each lot size, and what a 20 pip move costs. JPY pairs are priced at 150.00, which is why the pip value differs from a USD-quoted pair.

| lot | units | pip_value_usd_on_usd_quote_pair | pip_value_usd_on_jpy_pair_at_150_00 | loss_on_20_pip_move_usd | spread_cost_of_1_pip_usd |
| --- | --- | --- | --- | --- | --- |
| standard | 100000 | 10.0000 | 6.6667 | 200.00 | 10.0000 |
| mini | 10000 | 1.0000 | 0.6667 | 20.00 | 1.0000 |
| micro | 1000 | 0.1000 | 0.0667 | 2.00 | 0.1000 |
| nano | 100 | 0.0100 | 0.0067 | 0.20 | 0.0100 |

Machine-readable source: [`data/pip-value-by-lot-size.csv`](../data/pip-value-by-lot-size.csv)
