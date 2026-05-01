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
