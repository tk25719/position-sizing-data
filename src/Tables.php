<?php

declare(strict_types=1);

namespace Psizing;

/**
 * Reference tables and arithmetic for risk-based position sizing.
 *
 * The four CSV files ship with this package, so nothing needs to be downloaded
 * and no API key is required. Every value except the instrument rows is
 * computed rather than copied, and the formula sits next to each accessor.
 *
 * Interactive calculator: https://positionsizetool.com/
 * Citable archive:        https://doi.org/10.5281/zenodo.22840538
 */
final class Tables
{
    public const CONTRACT_SPECIFICATIONS = 'contract-specifications.csv';
    public const PIP_VALUE_BY_LOT_SIZE   = 'pip-value-by-lot-size.csv';
    public const LOSING_STREAK_EQUITY    = 'losing-streak-equity.csv';
    public const DRAWDOWN_RECOVERY       = 'drawdown-recovery.csv';

    /** @return array<int, array<int, string>> every row of one table, including its header */
    public static function table(string $name): array
    {
        $path = self::dataPath($name);
        if (!is_file($path)) {
            throw new \InvalidArgumentException(sprintf('Unknown table "%s".', $name));
        }

        $rows = [];
        $handle = fopen($path, 'rb');
        if ($handle === false) {
            throw new \RuntimeException(sprintf('Could not open "%s".', $path));
        }
        while (($row = fgetcsv($handle)) !== false) {
            $rows[] = $row;
        }
        fclose($handle);

        return $rows;
    }

    /**
     * Every instrument row: symbol, asset class, quote currency, pip size,
     * contract size and unit step.
     *
     * These are typical retail contract specifications, not exchange-published
     * official values. Check them against your own broker before trading.
     *
     * @return array<int, array<string, mixed>>
     */
    public static function contracts(): array
    {
        $rows = self::table(self::CONTRACT_SPECIFICATIONS);
        array_shift($rows);

        $out = [];
        foreach ($rows as $row) {
            if (count($row) < 6) {
                continue;
            }
            $out[] = [
                'symbol'         => trim($row[0]),
                'asset_class'    => trim($row[1]),
                'quote_currency' => trim($row[2]),
                'pip_size'       => self::num($row[3]),
                'contract_size'  => self::num($row[4]),
                'unit_step'      => self::num($row[5]),
            ];
        }

        return $out;
    }

    /** @return array<string, mixed>|null the row for one symbol, or null when it is not listed */
    public static function contractFor(string $symbol): ?array
    {
        foreach (self::contracts() as $contract) {
            if (strcasecmp((string) $contract['symbol'], $symbol) === 0) {
                return $contract;
            }
        }

        return null;
    }

    /**
     * Round $value down to a whole multiple of $step.
     *
     * A plain floor() turns 49999.999999999956 into 49 steps of 1000, i.e.
     * 49000, throwing away size the risk budget already paid for. Anything
     * within a rounding hair of the next step counts as that step; everything
     * else still rounds down, because rounding up raises risk silently.
     */
    public static function floorToStep(float $value, float $step): float
    {
        if ($step <= 0.0) {
            return $value;
        }

        $quotient = $value / $step;
        $floor    = floor($quotient);
        if ($quotient - $floor > 1.0 - 1e-9) {
            $floor += 1.0;
        }

        return $floor * $step;
    }

    /**
     * Largest tradable size keeping the loss inside the risk budget:
     * units = (balance x risk%) / |entry - stop|, then floored to the unit step.
     */
    public static function positionSize(float $balance, float $riskPercent, float $entry, float $stop, float $unitStep): float
    {
        $distance = abs($entry - $stop);
        if ($distance === 0.0) {
            throw new \InvalidArgumentException('Entry and stop are identical.');
        }

        $budget = $balance * ($riskPercent / 100.0);

        return self::floorToStep($budget / $distance, $unitStep);
    }

    /** Fraction of equity left after $losses consecutive losses: (1 - risk%)^n */
    public static function remainingEquity(float $riskPercent, int $losses): float
    {
        return (1 - $riskPercent / 100.0) ** $losses;
    }

    /** Gain a reduced balance needs to return to its original value: 1/(1 - drawdown) - 1 */
    public static function recoveryGain(float $drawdown): float
    {
        if ($drawdown >= 1.0) {
            throw new \InvalidArgumentException('Drawdown must be below 100 percent.');
        }

        return 1 / (1 - $drawdown) - 1;
    }

    /** Pip value of a position: units x pip size x quote-to-account rate */
    public static function pipValue(float $units, float $pipSize, float $quoteToAccountRate = 1.0): float
    {
        return $units * $pipSize * $quoteToAccountRate;
    }

    private static function dataPath(string $name): string
    {
        $base = dirname(__DIR__);

        return $base . DIRECTORY_SEPARATOR . 'data' . DIRECTORY_SEPARATOR . basename($name);
    }

    private static function num(string $value): float
    {
        $trimmed = trim($value);

        return is_numeric($trimmed) ? (float) $trimmed : 0.0;
    }
}
