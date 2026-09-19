# position-sizing-data

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22840538.svg)](https://doi.org/10.5281/zenodo.22840538)

Reference data and arithmetic for position sizing across forex, stocks and crypto futures.

This repository exists because the numbers behind "how many units should I trade" are usually scattered across broker pages, forum posts and screenshots. Here they are in plain CSV and Markdown, with the formula written out, so anyone can check the arithmetic instead of trusting it.

An interactive implementation of the same calculation lives at [https://positionsizetool.com/](https://positionsizetool.com/).

An archival copy of this dataset is deposited at Zenodo: [doi:10.5281/zenodo.22840538](https://doi.org/10.5281/zenodo.22840538). Use that DOI to cite the data in anything that outlives the repository.

## Contents

| File | What is in it |
| --- | --- |
| `data/contract-specifications.csv` | Default contract size, pip size and unit step per instrument, for 131 symbols across forex, metals, energies, indices and crypto. |
| `data/pip-value-by-lot-size.csv` | Pip value per standard, mini, micro and nano lot, on a USD-denominated account, plus the cost of a 20-pip move and of a 1-pip spread. |
| `data/losing-streak-equity.csv` | Equity remaining after 1 to 20 consecutive losses at 0.5%, 1% and 2% risk per trade. |
| `data/drawdown-recovery.csv` | Gain required on the reduced balance to return to the original balance, for drawdowns from 5% to 90%. |
| `checklists/pre-trade-risk-checklist.md` | What to confirm before an order goes in. |
| `docs/position-sizing-formulas.md` | The formulas, why each term sits where it does, and a worked example. |

## The formula in one line

```
units = (risk_budget - commission) / ((|entry - stop| + spread) x quote_to_account_rate)
```

The tradable size is that number rounded **down** to the broker's unit step. Rounding up increases risk without saying so.

The full derivation, including why the spread is added to the stop distance while the commission is subtracted from the budget, is in `docs/position-sizing-formulas.md`.

## Where the numbers come from

- **Instrument rows** are the built-in defaults of the calculator linked above. They are typical retail contract specifications, not exchange-published official values, and several are editable by design. Verify the contract size and unit step of your own instrument against your broker before placing an order.
- **Everything else in `data/` is computed, not copied.** Each table has its generating formula stated at the top of this table's entry below:
  - `losing-streak-equity.csv`: `remaining = (1 - risk%)^n`
  - `drawdown-recovery.csv`: `gain_required = 1 / (1 - drawdown) - 1`
  - `pip-value-by-lot-size.csv`: `pip_value = units x pip_size`, converted to USD at the stated rate

## Cite

YI, JUN (2026). *Position sizing reference data and worked arithmetic for forex, stocks and crypto futures* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.22840538

## Licence

Code and documentation: MIT. Data files in `data/`: CC0 1.0 Universal, to the extent applicable.

The Zenodo deposit of this dataset carries its own licence, CC BY 4.0, chosen at deposit time; refer to the record for the terms that apply to the archived copy.

This is not investment advice. Nothing here recommends a trade, a size or a broker.
