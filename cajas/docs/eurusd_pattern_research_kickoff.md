# EURUSD 15m Pattern Research Kickoff

## Why this phase exists

This phase transitions `qlib-cajas` from maintenance-only validation infrastructure into actual EURUSD market-structure research while preserving strict offline and non-trading boundaries.

## Expected data location

Primary local inputs:

- `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
- `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv`

## Expected schema

Canonical normalized columns:

- required: `timestamp`, `open`, `high`, `low`, `close`
- optional: `volume`, `spread`, `source`

Contract constraints:

- `high >= max(open, close, low)`
- `low <= min(open, close, high)`
- duplicate timestamp count must be reported
- missing OHLC counts/rate must be reported
- large timestamp gaps must be reported
- timestamps are handled and reported as UTC
- price precision profile is reported

Fixed policy:

- symbol: `EURUSD`
- side: `Bid`
- timeframe: `15m`
- no 1H/4H aggregation in this phase

## First pattern features

`cajas/research/eurusd_pattern_features.py` provides deterministic 15m feature scaffolding:

- candle body/wick/range geometry (`body`, `body_abs`, `upper_wick`, `lower_wick`, `range`, `body_ratio`)
- direction tags (`is_bullish`, `is_bearish`, `is_doji_like`)
- multi-horizon close percent change over `[3,5,8,13,21,34,55]`
- rolling range position by horizon
- efficiency ratio by horizon
- ATR-like rolling range average by horizon
- volatility-normalized horizon movement

## Out of scope

- no live trading
- no broker routing
- no order generation
- no production model training
- no Qlib core changes

## Next path

1. validate EURUSD dataset contract and audit
2. compute pattern features on 15m Bid bars
3. create manual label/review examples
4. test non-execution strategy hypotheses offline
5. evaluate ML labels/model training only in later phases
