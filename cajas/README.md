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

## Phase 2: Qlib Integration Mapping

- Phase 1 prepared dataset output is used as the current research input for integration planning:
  - `tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv`
  - `tmp/cajas/eurusd_15m_phase1/dataset_manifest.json`
- Phase 2 focus is mapping how this dataset can connect to Qlib `DatasetH` / `DataHandler` workflows.
- Integration notes are documented in:
  - `cajas/docs/qlib_integration_notes.md`
- Qlib core remains unchanged.
- This phase does not run formal training or trading workflows.

## Phase 3: Tracked Tasks and Prepared Handler

- `tasks/` is tracked as project task history and should not be ignored.
- `taskDocs/` is not used in this repository workflow.
- Added minimal prepared dataset handler:
  - `cajas/handlers/prepared_csv_handler.py`
- Added validation CLI:
  - `python cajas/scripts/validate_prepared_dataset_handler.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- This phase validates dataset access, schema checks, and train/valid/test segment slicing only.
- No model training, no qlib core changes, no trading logic.

## Phase 4: Package Cleanup and Dataset Adapter

- Confirmed package init path:
  - `cajas/handlers/__init__.py`
- Added dev test dependency file:
  - `requirements-dev.txt` (pytest)
- Added DatasetH-like external adapter:
  - `cajas/datasets/prepared_dataset.py`
- Added adapter validation CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_adapter.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- Existing handler validation CLI remains:
  - `./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_handler.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 5: Workflow Bridge Dry-Run

- Package init naming is standard and confirmed:
  - `cajas/handlers/__init__.py`
  - `cajas/datasets/__init__.py`
- Added Qlib-inspired workflow bridge:
  - `cajas/workflows/prepared_workflow.py`
- Added workflow dry-run CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- JSON output mode:
  - `./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8 --json`
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py cajas/tests/test_prepared_workflow.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic
