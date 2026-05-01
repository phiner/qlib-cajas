# FX Dataset Schema Notes (Phase 0-3)

## Input CSV

Expected raw input is a 15m EURUSD Bid CSV.

Required columns:
- `Time (UTC)`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume` or `Volume `

Header compatibility:
- the script trims header whitespace, so both `Volume` and `Volume ` are accepted

Input format details:
- datetime format: `YYYY.MM.DD HH:MM:SS`
- timeframe: `15m`
- default symbol: `EURUSD`

## Output CSV (Research Dataset)

Phase 0 output is a plain research dataset CSV (not Qlib binary format).

Expected fields include at least:
- `datetime`
- `symbol`
- `timeframe`
- `open`
- `high`
- `low`
- `close`
- `volume`
- lightweight K-line feature columns
- `future_return_8` (or `future_return_{horizon}`)
- `future_direction_8` (or `future_direction_{horizon}`)

## Temporary Label Definition

Use future close over horizon bars:
- `future_return_8 = close.shift(-8) / close - 1`

Three-class label rule:
- `up` when `future_return_8 > flat_threshold`
- `down` when `future_return_8 < -flat_threshold`
- `flat` otherwise

Default `flat_threshold` is `0.0002`.

Important: `future_direction_8` is a research label, not a trading signal.

## Phase 3 Prepared Handler Rules

- Required columns for `PreparedCsvHandler`:
  - `datetime`
  - `symbol`
  - `timeframe`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
  - `future_direction_8`
- Candidate feature columns are numeric columns excluding:
  - `datetime`
  - `symbol`
  - `timeframe`
  - label column (`future_direction_8` by default)
  - leakage columns: `future_close_8`, `future_return_8`
- `future_close_8` and `future_return_8` may remain in dataset output for auditability, but must not be used as model features.

## Phase 4 Adapter Notes

- `PreparedDataset` (DatasetH-like adapter) returns segment-wise features and labels.
- Audit columns remain allowed in the dataset file:
  - `future_close_8`
  - `future_return_8`
- These audit columns are explicitly excluded from feature sets.
- Labels remain string classes (`up`, `down`, `flat`) in this phase.

## Phase 5 Workflow Bridge Notes

- Workflow bridge input remains the Phase 1 prepared CSV output.
- `PreparedWorkflow` validates segment data shapes in dry-run mode only.
- Leakage audit columns are never used as features:
  - `future_close_8`
  - `future_return_8`
- Labels remain string classes (`up`, `down`, `flat`).

## Phase 6 Experiment Config Notes

- Default config path:
  - `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Config points to the Phase 1 prepared CSV by default.
- CSV path can be overridden in local dry-run testing with `--input-override`.
- Leakage audit columns remain non-feature fields:
  - `future_close_8`
  - `future_return_8`

## Phase 7 Dry-Run Artifact Notes

- Dry-run artifacts are local metadata files and do not contain raw dataset rows.
- Prepared CSV remains a local source input for dry-run validation.
- Artifact output under `tmp/` is local-only and should not be committed.

## Phase 8 Audit Rules

- Feature audit rules:
  - leakage columns must not appear in feature inputs
  - non-numeric features are rejected
  - all-null feature columns are rejected
  - constant feature columns are warnings
- Label audit rules:
  - expected classes are `down`, `flat`, `up`
  - unknown classes are rejected
  - missing labels are rejected
  - very rare classes are warnings
- `future_close_8` and `future_return_8` remain audit columns, not model features.

## Phase 9 Planning Notes

- Missing-value audit now includes:
  - missing counts
  - missing ratios
  - top missing feature summary
- Baseline plan artifacts do not contain raw rows.
- Dependency probe is environment-only and does not install packages.
