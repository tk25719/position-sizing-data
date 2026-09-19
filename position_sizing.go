// Package positionsizing loads the position sizing reference tables that ship
// with this module and repeats the arithmetic behind them.
//
// The data files are embedded, so importing this package needs no network
// access and no credentials. Every calculation here mirrors the ones documented
// in docs/position-sizing-formulas.md, and every number in data/ comes with the
// formula that produces it.
//
// Interactive calculator: https://positionsizetool.com/
// Citable archive: https://doi.org/10.5281/zenodo.22840538
package positionsizing

import (
	"embed"
	"encoding/csv"
	"errors"
	"math"
	"strconv"
	"strings"
)

//go:embed data
var Data embed.FS

// ErrNoSuchTable is returned when an unknown table name is requested.
var ErrNoSuchTable = errors.New("positionsizing: unknown table")

// Table names embedded in this module.
const (
	ContractSpecificationsTable = "contract-specifications.csv"
	PipValueByLotSizeTable      = "pip-value-by-lot-size.csv"
	LosingStreakEquityTable     = "losing-streak-equity.csv"
	DrawdownRecoveryTable       = "drawdown-recovery.csv"
)

// Table returns every row of one embedded CSV file, including its header row.
func Table(name string) ([][]string, error) {
	f, err := Data.Open("data/" + name)
	if err != nil {
		return nil, ErrNoSuchTable
	}
	defer f.Close()
	return csv.NewReader(f).ReadAll()
}

// Contract is one row of contract-specifications.csv.
type Contract struct {
	Symbol        string
	AssetClass    string
	QuoteCurrency string
	PipSize       float64
	ContractSize  float64
	UnitStep      float64
}

// Contracts returns every instrument row. These are typical retail contract
// specifications, not exchange-published official values: verify them against
// your own broker before placing an order.
func Contracts() ([]Contract, error) {
	rows, err := Table(ContractSpecificationsTable)
	if err != nil {
		return nil, err
	}
	out := make([]Contract, 0, len(rows))
	for i, row := range rows {
		if i == 0 || len(row) < 6 {
			continue
		}
		out = append(out, Contract{
			Symbol:        strings.TrimSpace(row[0]),
			AssetClass:    strings.TrimSpace(row[1]),
			QuoteCurrency: strings.TrimSpace(row[2]),
			PipSize:       num(row[3]),
			ContractSize:  num(row[4]),
			UnitStep:      num(row[5]),
		})
	}
	return out, nil
}

// ContractFor returns the row for one symbol, or false when it is not listed.
func ContractFor(symbol string) (Contract, bool) {
	cs, err := Contracts()
	if err != nil {
		return Contract{}, false
	}
	for _, c := range cs {
		if strings.EqualFold(c.Symbol, symbol) {
			return c, true
		}
	}
	return Contract{}, false
}

// FloorToStep rounds v down to a whole multiple of step.
//
// A naive floor turns 49999.999999999956 into 49 units of 1000, i.e. 49000,
// losing 999 units of size that the risk budget actually pays for. Anything
// within a rounding hair of the next step is treated as that step; everything
// else still rounds down, because rounding up raises risk without saying so.
func FloorToStep(v, step float64) float64 {
	if step <= 0 {
		return v
	}
	q := v / step
	floor := math.Floor(q)
	if q-floor > 1-1e-9 {
		floor = floor + 1
	}
	return floor * step
}

// PositionSize returns the largest tradable size that keeps the loss inside the
// risk budget, given a balance, a risk percentage, an entry price and a stop
// price. The result is floored to unitStep. It never rounds up.
func PositionSize(balance, riskPercent, entry, stop, unitStep float64) (float64, error) {
	distance := math.Abs(entry - stop)
	if distance == 0 {
		return 0, errors.New("positionsizing: entry and stop are identical")
	}
	riskBudget := balance * riskPercent / 100
	return FloorToStep(riskBudget/distance, unitStep), nil
}

// RemainingEquity returns the fraction of equity left after n consecutive
// losses of riskPercent each: remaining = (1 - risk%)^n.
func RemainingEquity(riskPercent float64, losses int) float64 {
	return math.Pow(1-riskPercent/100, float64(losses))
}

// RecoveryGain returns the gain a reduced balance needs to get back to its
// original value: gain = 1/(1 - drawdown) - 1.
func RecoveryGain(drawdown float64) (float64, error) {
	if drawdown >= 1 {
		return 0, errors.New("positionsizing: drawdown must be below 100%")
	}
	return 1/(1-drawdown) - 1, nil
}

// PipValue returns the pip value of a position size: pip value = units x pip size.
func PipValue(units, pipSize, quoteToAccountRate float64) float64 {
	if quoteToAccountRate == 0 {
		quoteToAccountRate = 1
	}
	return units * pipSize * quoteToAccountRate
}

func num(s string) float64 {
	v, err := strconv.ParseFloat(strings.TrimSpace(s), 64)
	if err != nil {
		return 0
	}
	return v
}
