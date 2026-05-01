# FX Dataset Schema Notes (Phase 0)

## Input CSV

Expected raw input is a 15m EURUSD Bid CSV.

Required columns:
- `Time (UTC)`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume` or `Volume `

Input format details:
- datetime format: `YYYY.MM.DD HH:MM:SS`
- timeframe: `15m`
- default symbol: `EURUSD`

## Output CSV (Research Dataset)

Phase 0 output is a plain research dataset CSV (not Qlib binary format).

Expected fields include at least:
- `datetime`
- `symbol`
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
