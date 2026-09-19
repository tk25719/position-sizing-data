# Pre-trade risk checklist

Confirm every item before the order goes in. The order moving is not the risk decision — the risk decision happened earlier, and this is the check that it still holds.

## Before the size exists

1. **Balance** — the amount you are sizing from is your current balance, not your deposit, not your peak.
2. **Risk percentage** — chosen in advance and held constant. A percentage that changes per setup is not risk management.
3. **Stop price** — taken from where the trade is wrong on the chart, in price terms. Not from how much you can afford to lose, and not moved after sizing.
4. **Spread** — the spread at the moment of entry. A quoted average is not the number the trade will pay.
5. **Commission** — round turn, in your account currency.
6. **Unit step** — your broker's minimum increment for this instrument.
7. **Contract size** — how much underlying one unit represents. Wrong here and everything downstream is wrong by the same factor.

## Computing the size

8. Effective stop distance = `|entry - stop| + spread`. The spread is loss incurred at entry, so it belongs inside the stop distance.
9. Budget after costs = `risk budget - commission`. Money spent on fees can no longer be risked.
10. `units = budget after costs / effective stop distance`. If the quote currency differs from your account currency, include the conversion rate in the denominator.
11. Round **down** to the unit step. Never to nearest.
12. Recompute the worst case from the **rounded** size: `rounded units x effective stop distance + commission`. This is the number that must fit inside the budget, not the pre-rounding one.
13. If the rounded size is **zero**, the honest answers are a wider stop, a bigger percentage, or no trade. Rounding up is not one of them.

## Before you press send

14. **Margin** — required margin = position value / leverage. If free margin is short, the size comes down; the risk percentage does not.
15. **Liquidation or stop-out level** (crypto and CFD) — check that your stop sits well before the level at which the venue closes the position for you. A stop beyond liquidation is decoration.
16. **Correlation** — how many other open positions express the same view? The per-trade percentage applies to one trade, not to a book of five that move together.
17. **Event risk** — earnings, central bank decisions, funding timestamps. A stop does not guarantee its fill price through a gap.
18. **Funding / swap** (holds longer than a session) — a holding cost, not an entry cost. Account for it separately from the size.

## After the trade closes

19. Record the size you *placed*, the size the arithmetic *said*, and any difference with its reason. The difference is where most accounts leak.
