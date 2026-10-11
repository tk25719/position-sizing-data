# position-sizing-data

Reference data and arithmetic for risk-based position sizing across forex,
stocks and crypto futures. This is the Rust flavour of the same dataset that is
also published as a Zenodo record (`10.5281/zenodo.22840538`), as a Python
package (`position-sizing-data` on PyPI), an npm package, a Go module and a PHP
package, and used by the web calculator at
<https://positionsizetool.com/>.

The numbers are broker-independent reference values, not quotes: contract
specifications per symbol, pip value by lot size, equity decay through losing
streaks, and the gain needed to recover from a drawdown. All four tables are
embedded in the crate with `include_str!`, so no files have to be shipped
alongside a binary.

## Install

```toml
[dependencies]
position-sizing-data = "0.1"
```

## Read a table

```rust
let specs = position_sizing_data::contract_specifications();
println!("{:?}", specs.header); // ["symbol", "asset_class", "quote_currency", ...]
println!("{} instruments", specs.rows.len());
```

Available: `contract_specifications()`, `pip_values()`,
`losing_streak_equity()`, `drawdown_recovery()`, plus
`load_csv("contract-specifications.csv")` and friends by file name.

## Size a position

`position_size` turns a risk budget into a unit count and rounds **down** to the
broker's minimum step. Rounding up raises risk without showing it anywhere, so
this crate never does it.

```rust
use position_sizing_data::position_size;

// 10,000 USD account, 1% risk, EUR/USD from 1.1000 with a stop at 1.0980,
// 1,000 unit step.
let size = position_size(10_000.0, 1.0, 1.1000, 1.0980, 0.0, 0.0, 1.0, 1000.0).unwrap();
assert_eq!(size.tradable_units, 50_000.0);
assert_eq!(size.worst_case_loss, 100.0);
```

`worst_case_loss` is recomputed from the rounded size, because that is what the
account actually loses when the stop is hit.

The rounding matters more than it looks. The division above comes out to
49.999999999999956, and `(units / step).floor() * step` would quietly cut the
trade to 49,000 units — a whole mini lot — for no reason other than floating
point. `floor_to_step` treats anything within a rounding hair of the next step
as that step, and still never rounds up beyond that tolerance.

## License

MIT. Data tables are released under CC0; see the Zenodo record for citation.
