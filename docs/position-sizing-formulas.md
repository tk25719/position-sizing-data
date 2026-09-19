# Position sizing formulas

Position sizing answers one question: given the amount I accept losing if this trade goes against me, and the distance between my entry and my stop, how many units am I allowed to hold?

## Inputs

| Input | Meaning |
| --- | --- |
| `balance` | Current account balance |
| `risk` | Percentage of balance, or a fixed cash amount |
| `entry` | Entry price |
| `stop` | Stop-loss price |
| `spread` | The instrument spread at entry, in price terms |
| `commission` | Round-turn commission in account currency |
| `step` | Broker's minimum unit increment |
| `rate` | Quote-currency to account-currency rate (1 when they match) |

## The calculation

```
risk_budget          = balance x risk
stop_distance        = |entry - stop|
effective_stop       = stop_distance + spread
budget_after_costs   = risk_budget - commission
units                = budget_after_costs / (effective_stop x rate)
tradable_units       = floor(units / step) x step
max_loss_at_stop     = tradable_units x effective_stop x rate + commission
```

Derived figures:

```
position_value       = tradable_units x entry x rate
required_margin      = position_value / leverage
exposure             = position_value / balance
```

## Why each term sits where it does

- **Spread is added to the stop distance.** You pay it the instant you enter, so it is part of what you lose when the trade goes straight to the stop. Treating it separately understates every loss.
- **Commission is subtracted from the budget.** Money spent on fees cannot also be risked on the trade.
- **Rounding always goes down.** Rounding to nearest puts you over budget on roughly half your trades, silently.
- **Leverage appears only in margin.** It decides how much you post, not how much you risk. Since it is absent from the units equation, changing leverage cannot change the correct size.

## Worked example (forex, EUR/USD)

Account 10,000 USD, risk 1%, buy at 1.1000, stop at 1.0980, spread 1 pip (0.0001), commission 7 USD round turn, unit step 1,000, USD quote against a USD account so `rate = 1`.

```
risk_budget        = 10,000 x 1%            = 100.00
stop_distance      = 1.1000 - 1.0980        = 0.0020  (20 pips)
effective_stop     = 0.0020 + 0.0001        = 0.0021  (21 pips)
budget_after_costs = 100.00 - 7.00          = 93.00
units              = 93.00 / 0.0021         = 44,285.71
tradable_units     = floor(44,285.71/1000)x1000 = 44,000  (0.44 lots)
max_loss_at_stop   = 44,000 x 0.0021 + 7.00 = 99.40
```

The cost-free version of the same trade is `100.00 / 0.0020 = 50,000` units, or 0.50 lots, whose real loss is `50,000 x 0.0021 + 7.00 = 112.00` — 12% over budget, on every trade, forever. That gap is why the costs belong inside the formula.

## Worked example (crypto perpetual, BTCUSDT)

Account 10,000 USD, risk 1%, long at 60,000, stop at 59,400, spread 10, commission 12 USD, unit step 0.001, contract size 1 coin per unit.

```
risk_budget        = 100.00
stop_distance      = 600.00
effective_stop     = 610.00
budget_after_costs = 88.00
units              = 88.00 / 610.00         = 0.144262
tradable_units     = 0.144 BTC
max_loss_at_stop   = 0.144 x 610.00 + 12.00 = 99.84
```

Notional exposure is `0.144 x 60,000 = 8,640 USD`, or 86.4% of the account, while risk stays at 1%. That gap between exposure and risk is normal; it is what leverage does, and it is the whole reason this arithmetic exists.

## See also

- `../data/losing-streak-equity.csv` — what a run of losses costs at different percentages
- `../data/drawdown-recovery.csv` — why losses and gains are not symmetrical
- `../checklists/pre-trade-risk-checklist.md` — what to check before sending the order
