# position-sizing-data

Reference data and arithmetic for risk-based position sizing across forex, stocks and crypto futures.

The same tables are published as a citable dataset: [doi:10.5281/zenodo.22840538](https://doi.org/10.5281/zenodo.22840538), and used by the web calculator at [https://positionsizetool.com/](https://positionsizetool.com/). Source repository: [https://github.com/tk25719/position-sizing-data](https://github.com/tk25719/position-sizing-data).

## Install

```console
pip install position-sizing-data
```

## What is in it

| Function | Returns |
| --- | --- |
| `contract_specifications()` | Pip size, contract size and minimum unit step for 131 instruments, across forex pairs, metals, energies, indices, crypto futures, stocks and ETFs. |
| `pip_values()` | Pip value and the loss on a 20 pip move for standard, mini, micro and nano lots. |
| `losing_streak_equity()` | Equity remaining after 1 to 20 consecutive losses at 0.5%, 1% and 2% risk per trade. |
| `drawdown_recovery()` | Gain required on the reduced balance to return to the original balance, for drawdowns from 5% to 90%. |
| `position_size(...)` | The risk-to-units calculation itself. |

Read the tables:

```python
from position_sizing_data import contract_specifications

rows = contract_specifications()
print(rows[0])
```

Compute a size:

```python
from position_sizing_data import position_size

result = position_size(
    balance=10000.0,
    risk_percent=1.0,
    entry=1.1000,
    stop=1.0980,
    unit_step=1000.0,   # 0.01 lot
)
print(result)
# {'risk_budget': 100.0, 'units': 50000.0, 'tradable_units': 50000.0, 'worst_case_loss': 100.0}
```

## The formula

```
units = (risk_budget - commission) / ((|entry - stop| + spread) x quote_rate)
```

The tradable size is that number rounded **down** to `unit_step`. `position_size` returns the worst-case loss recomputed from the rounded size, which is what the account actually loses when the stop is hit.

## Where the numbers come from

The rows in `contract_specifications()` are typical retail contract specifications, not exchange-published official values. Verify the contract size and unit step against your own broker before placing an order. The other three tables are closed-form arithmetic:

- losing streak: `remaining = (1 - risk)^n`
- drawdown recovery: `gain_required = 1 / (1 - drawdown) - 1`
- pip value: `pip_value = units x pip_size`

## Licence

MIT for the code. Data files are CC0 1.0 Universal, to the extent applicable. This is not investment advice.
