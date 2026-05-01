# cajas research layer for qlib-cajas

`cajas/` is the independent research layer in this `qlib-cajas` fork.

## Goal

Qlib-based Market Recognition Research for FX K-line data.

Current focus:
- EURUSD 15m K-line market recognition research

Current scope is research-only and is **not** a trading system.

## Out of Scope

This phase does not include:
- live trading
- automatic order placement
- broker integration
- profit prediction promises
- production investment advice

## Phase 0 Objectives

- establish an independent research directory under `cajas/`
- prepare a minimal FX dataset
- generate lightweight K-line features
- generate `future_direction_8` research labels
- provide a first draft Qlib/LightGBM experiment config

## Directory Structure

```text
cajas/
  scripts/       # data preparation and research utilities
  configs/       # draft experiment configs
  data_examples/ # expected input/output schema notes
```

## Phase 1: Run Real EURUSD 15m Preparation

Run:

```bash
python cajas/scripts/prepare_fx_dataset.py \
  --input ~/projects/research/data/EURUSD_15\ Mins_Bid_2025.01.01_2025.12.31.csv \
  --output-dir tmp/cajas/eurusd_15m_phase1 \
  --symbol EURUSD \
  --timeframe 15m
```

Notes:
- raw input CSV is local-only and should not be committed
- generated outputs are written under `tmp/` and should not be committed
- `future_direction_8` is a market-recognition research label, not a trading signal
- current phase validates data preparation only (no model training)
