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

## Anomaly triage and clean-view policy

Current raw-data finding:

- the 2020-2024 file has `10` OHLC anomaly rows violating raw-bar consistency checks
- raw inputs remain immutable and are never overwritten

Reviewable triage artifacts:

- `tmp/validation-eurusd-ohlc-anomaly-triage.json`
- `tmp/validation-eurusd-ohlc-anomaly-triage.md`

Clean-view artifacts:

- `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
- `tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv`
- `tmp/validation-eurusd-clean-dataset-view.json`
- `tmp/validation-eurusd-clean-dataset-view.md`

Research gating rule:

- raw dataset audit may remain `blocked`
- pattern research may proceed only when clean-view report is `ready` or non-blocking `watch`
- readiness state for this path is `ready_for_pattern_research_with_clean_view`

## Pattern candidate sample pack policy

Approved input:

- `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`

Generated candidate artifacts:

- `tmp/eurusd/EURUSD_15m_pattern_candidates.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_samples.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl`
- `tmp/validation-eurusd-pattern-candidate-pack.json`
- `tmp/validation-eurusd-pattern-candidate-pack.md`

Candidate review scope:

- candidate tags are for human review only
- candidate tags are not trading signals
- no buy/sell/order/position outputs are produced

## Out of scope

- no live trading
- no broker routing
- no order generation
- no production model training
- no Qlib core changes

## Next path

1. validate EURUSD dataset contract and audit
2. triage and quarantine anomaly rows
3. generate clean-view candidate sample pack
4. review candidate samples manually
5. create manual label/review examples
6. test non-execution strategy hypotheses offline
7. evaluate ML labels/model training only in later phases
