//! Reference data and arithmetic for risk-based position sizing.
//!
//! This crate ships the same CSV tables and the same risk-to-units formula that
//! are published as the Zenodo dataset `10.5281/zenodo.22840538` and used by the
//! web calculator at <https://positionsizetool.com/>.
//!
//! The tables are plain data, embedded into the crate so nothing has to be read
//! from disk at runtime. The one function that computes something,
//! [`position_size`], implements
//!
//! ```text
//! units = (risk_budget - commission) / ((|entry - stop| + spread) * quote_rate)
//! ```
//!
//! and rounds the result DOWN to the instrument's minimum unit step, because
//! rounding up raises risk without showing it anywhere.

use std::fmt;

/// A CSV table with its header row split off from the body rows.
#[derive(Debug, Clone, PartialEq)]
pub struct Table {
    pub header: Vec<String>,
    pub rows: Vec<Vec<String>>,
}

/// The four tables that ship with this crate.
pub const CSV_FILES: [&str; 4] = [
    "contract-specifications.csv",
    "pip-value-by-lot-size.csv",
    "losing-streak-equity.csv",
    "drawdown-recovery.csv",
];

/// Split one CSV line into fields, honouring double quotes.
fn split_line(line: &str) -> Vec<String> {
    let mut fields: Vec<String> = Vec::new();
    let mut current = String::new();
    let mut in_quotes = false;
    let mut chars = line.chars().peekable();

    while let Some(ch) = chars.next() {
        match ch {
            '"' if in_quotes && chars.peek() == Some(&'"') => {
                current.push('"');
                chars.next();
            }
            '"' => in_quotes = !in_quotes,
            ',' if !in_quotes => {
                fields.push(std::mem::take(&mut current));
            }
            other => current.push(other),
        }
    }
    fields.push(current);
    fields
}

/// Parse CSV text into a [`Table`]. Blank lines are skipped. Lines that are
/// shorter than the header are padded so a column index never panics.
pub fn parse_csv(raw: &str) -> Table {
    let cleaned = raw.trim_start_matches('\u{feff}');
    let mut lines = cleaned.lines().filter(|l| !l.trim().is_empty());
    let header = match lines.next() {
        Some(first) => split_line(first),
        None => return Table { header: Vec::new(), rows: Vec::new() },
    };
    let width = header.len();
    let rows = lines
        .map(|line| {
            let mut fields = split_line(line);
            fields.resize(width, String::new());
            fields
        })
        .collect();
    Table { header, rows }
}

/// Return one of the tables bundled with this crate.
///
/// Returns `Err` with the list of valid names when the name is unknown.
pub fn load_csv(name: &str) -> Result<Table, String> {
    match name {
        "contract-specifications.csv" => Ok(parse_csv(include_str!("../data/contract-specifications.csv"))),
        "pip-value-by-lot-size.csv" => Ok(parse_csv(include_str!("../data/pip-value-by-lot-size.csv"))),
        "losing-streak-equity.csv" => Ok(parse_csv(include_str!("../data/losing-streak-equity.csv"))),
        "drawdown-recovery.csv" => Ok(parse_csv(include_str!("../data/drawdown-recovery.csv"))),
        other => Err(format!(
            "unknown data file: {} (available: {})",
            other,
            CSV_FILES.join(", ")
        )),
    }
}

/// Pip size, contract size and minimum unit step per instrument.
pub fn contract_specifications() -> Table {
    load_csv("contract-specifications.csv").expect("contract-specifications.csv is bundled")
}

/// Pip value and the loss on a 20 pip move for standard, mini, micro and nano lots.
pub fn pip_values() -> Table {
    load_csv("pip-value-by-lot-size.csv").expect("pip-value-by-lot-size.csv is bundled")
}

/// Equity remaining after n consecutive losses at 0.5%, 1% and 2% risk per trade.
pub fn losing_streak_equity() -> Table {
    load_csv("losing-streak-equity.csv").expect("losing-streak-equity.csv is bundled")
}

/// Gain required to recover from a drawdown.
pub fn drawdown_recovery() -> Table {
    load_csv("drawdown-recovery.csv").expect("drawdown-recovery.csv is bundled")
}

/// Round `value` DOWN to a whole multiple of `step`.
///
/// A naive `(value / step).floor() * step` is wrong at the edges: with a
/// 10,000 USD account, 1% risk, a 20 pip stop and a 1,000 unit step the exact
/// answer is 50,000 units, but the division yields 49.999999999999956 and the
/// naive floor collapses it to 49,000, silently cutting the trade by a whole
/// mini lot.
///
/// Anything sitting within a rounding hair of the next step counts as that
/// step. Nothing is ever rounded up beyond that tolerance, so the result can
/// still be smaller than the raw unit count, never larger.
///
/// # Panics
///
/// Panics if `step` is not greater than zero.
pub fn floor_to_step(value: f64, step: f64) -> f64 {
    assert!(step > 0.0, "step must be greater than zero");
    let quotient = value / step;
    let nearest = quotient.round();
    let tolerance = 1e-9 * 1.0f64.max(nearest.abs());
    let steps = if (quotient - nearest).abs() < tolerance {
        nearest
    } else {
        quotient.floor()
    };
    steps * step
}

/// The budget, the raw unit count, the tradable size and the loss if the stop
/// is hit.
#[derive(Debug, Clone, PartialEq)]
pub struct PositionSize {
    /// Account currency amount the trader is willing to lose.
    pub risk_budget: f64,
    /// Unit count before rounding to the broker's step.
    pub units: f64,
    /// Unit count after rounding down to the broker's step.
    pub tradable_units: f64,
    /// Account currency lost if price reaches `stop`, recomputed from
    /// `tradable_units` rather than from the raw size.
    pub worst_case_loss: f64,
}

impl fmt::Display for PositionSize {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "budget {:.2} -> {:.2} units (rounded from {:.2}), worst case {:.2}",
            self.risk_budget, self.tradable_units, self.units, self.worst_case_loss
        )
    }
}

/// Turn a risk budget into a tradable unit count.
///
/// `balance` is in account currency. `risk_percent` is a number, `1.0` meaning
/// 1%. `quote_rate` converts one unit of quote currency into account currency;
/// leave it at `1.0` when the two are the same. `unit_step` is the broker's
/// minimum increment.
///
/// The returned `worst_case_loss` is recomputed from the rounded size, which is
/// the number that actually matters: it is what the account loses when the stop
/// is hit.
///
/// # Errors
///
/// Returns `Err` when the stop distance is zero, `quote_rate` is zero or
/// negative, or `unit_step` is zero or negative.
///
/// # Example
///
/// ```
/// use position_sizing_data::position_size;
///
/// // 10,000 USD account, 1% risk, EUR/USD from 1.1000 to 1.0980, 1,000 unit step.
/// let size = position_size(10_000.0, 1.0, 1.1000, 1.0980, 0.0, 0.0, 1.0, 1000.0).unwrap();
/// assert_eq!(size.tradable_units, 50_000.0);
/// ```
pub fn position_size(
    balance: f64,
    risk_percent: f64,
    entry: f64,
    stop: f64,
    spread: f64,
    commission: f64,
    quote_rate: f64,
    unit_step: f64,
) -> Result<PositionSize, String> {
    let stop_distance = (entry - stop).abs() + spread;
    if stop_distance <= 0.0 {
        return Err("stop distance must be greater than zero".to_string());
    }
    if quote_rate <= 0.0 {
        return Err("quote_rate must be greater than zero".to_string());
    }
    if unit_step <= 0.0 {
        return Err("unit_step must be greater than zero".to_string());
    }

    let risk_budget = balance * risk_percent / 100.0;
    let units = (risk_budget - commission) / (stop_distance * quote_rate);
    let tradable_units = floor_to_step(units, unit_step);
    let worst_case_loss = tradable_units * stop_distance * quote_rate + commission;

    Ok(PositionSize {
        risk_budget,
        units,
        tradable_units,
        worst_case_loss,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fifty_thousand_units_at_the_rounding_edge() {
        let size = position_size(10_000.0, 1.0, 1.1000, 1.0980, 0.0, 0.0, 1.0, 1000.0).unwrap();
        assert_eq!(size.tradable_units, 50_000.0);
        assert_eq!(size.worst_case_loss, 100.0);
    }

    #[test]
    fn never_rounds_up_over_the_budget() {
        let size = position_size(10_000.0, 1.0, 1.1000, 1.0980, 0.0, 0.0, 1.0, 1000.0).unwrap();
        assert!(size.worst_case_loss <= size.risk_budget + f64::EPSILON);
    }

    #[test]
    fn table_has_a_header_and_rows() {
        let specs = contract_specifications();
        assert_eq!(specs.header[0], "symbol");
        assert!(specs.rows.len() > 100);
    }

    #[test]
    fn unknown_table_is_an_error() {
        assert!(load_csv("nope.csv").is_err());
    }
}
