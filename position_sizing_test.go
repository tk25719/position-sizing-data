package positionsizing

import (
	"math"
	"testing"
)

func TestPositionSizeFloorsToStep(t *testing.T) {
	// 100 USD risk over a 20 pip stop is 50,000 units. Naive flooring turns
	// 49999.999999999956 into 49 units of 1000; the tolerance-aware floor keeps
	// it at 50,000.
	got, err := PositionSize(10000, 1, 1.1000, 1.0980, 1000)
	if err != nil {
		t.Fatalf("PositionSize: %v", err)
	}
	if got != 50000 {
		t.Fatalf("PositionSize = %v, want 50000", got)
	}
}

func TestPositionSizeNeverRoundsUp(t *testing.T) {
	got, err := PositionSize(10000, 1, 1.1000, 1.0985, 1000)
	if err != nil {
		t.Fatalf("PositionSize: %v", err)
	}
	// budget / distance = 100 / 0.0015 = 66666.66..., floored to 66000.
	if got != 66000 {
		t.Fatalf("PositionSize = %v, want 66000", got)
	}
}

func TestPositionSizeRejectsZeroDistance(t *testing.T) {
	if _, err := PositionSize(10000, 1, 1.1000, 1.1000, 1000); err == nil {
		t.Fatal("expected an error when entry equals stop")
	}
}

func TestEmbeddedTables(t *testing.T) {
	if n, err := countRows(ContractSpecificationsTable); err != nil || n != 131 {
		t.Fatalf("contract rows = %v (err %v), want 131", n, err)
	}
	if n, err := countRows(PipValueByLotSizeTable); err != nil || n != 4 {
		t.Fatalf("pip rows = %v (err %v), want 4", n, err)
	}
	if n, err := countRows(LosingStreakEquityTable); err != nil || n != 20 {
		t.Fatalf("streak rows = %v (err %v), want 20", n, err)
	}
	if n, err := countRows(DrawdownRecoveryTable); err != nil || n != 12 {
		t.Fatalf("recovery rows = %v (err %v), want 12", n, err)
	}
}

func TestKnownSymbol(t *testing.T) {
	c, ok := ContractFor("EUR/USD")
	if !ok {
		t.Fatal("EUR/USD is missing")
	}
	if c.ContractSize != 100000 || c.PipSize != 0.0001 || c.UnitStep != 1000 {
		t.Fatalf("unexpected EUR/USD row: %+v", c)
	}
}

func TestFormulas(t *testing.T) {
	if got := RemainingEquity(1, 1); math.Abs(got-0.99) > 1e-12 {
		t.Fatalf("RemainingEquity(1,1) = %v, want 0.99", got)
	}
	got, err := RecoveryGain(0.5)
	if err != nil {
		t.Fatalf("RecoveryGain: %v", err)
	}
	if math.Abs(got-1.0) > 1e-12 {
		t.Fatalf("RecoveryGain(0.5) = %v, want 1", got)
	}
}

func TestTableRejectsUnknownName(t *testing.T) {
	if _, err := Table("nope.csv"); err != ErrNoSuchTable {
		t.Fatalf("Table(unknown) err = %v, want ErrNoSuchTable", err)
	}
}

func countRows(name string) (int, error) {
	rows, err := Table(name)
	if err != nil {
		return 0, err
	}
	return len(rows) - 1, nil
}
