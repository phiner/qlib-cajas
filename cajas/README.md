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

## Phase 9: Training-Disabled Baseline Plan

- Added dependency probe module:
  - `cajas/environment/dependency_probe.py`
- Enhanced feature audit details:
  - missing value ratios
  - top missing feature summary
- Added training-disabled baseline planning module:
  - `cajas/baseline/baseline_plan.py`
- Added baseline plan CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- JSON mode:
  - `./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --json`
- Optional local artifact:
  - `--write-artifacts --output-dir tmp/cajas/baseline_plans --run-name phase9_baseline_plan`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 8: Baseline Readiness Gate

- Added feature audit module:
  - `cajas/audits/feature_audit.py`
- Added label audit module:
  - `cajas/audits/label_audit.py`
- Added baseline readiness gate:
  - `cajas/readiness/baseline_readiness.py`
- Added readiness CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- JSON mode:
  - `./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --json`
- Optional artifact output:
  - `--write-artifacts --output-dir tmp/cajas/baseline_readiness --run-name phase8_baseline_readiness`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 7: Dry-Run Artifact Recorder

- Added local dry-run artifact recorder:
  - `cajas/recorders/dry_run_recorder.py`
- Extended experiment plan dry-run CLI with optional artifact writing:
  - `--write-artifacts`
  - `--output-dir`
  - `--run-name`
- Artifact file names:
  - `run_manifest.json`
  - `config_snapshot.json`
  - `workflow_summary.json`
  - `validation_report.json`
- Example:
  - `./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --write-artifacts --output-dir tmp/cajas/experiment_dry_runs --run-name phase7_eurusd_15m_dry_run`
- Artifact outputs under `tmp/` are local-only and should not be committed.
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py cajas/tests/test_prepared_workflow.py cajas/tests/test_experiment_config.py caixas/tests/test_experiment_plan_dry_run.py cajas/tests/test_dry_run_recorder.py caixas/tests/test_experiment_plan_artifacts.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 6: Experiment Config Plan Dry-Run

- Added training-disabled config loader:
  - `cajas/config/experiment_config.py`
- Added experiment plan dry-run CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Safety gates:
  - config validation
  - `training.enabled` must remain `false`
  - workflow remains dry-run only
- Optional flags:
  - `--input-override`
  - `--json`
  - `--strict`
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py cajas/tests/test_prepared_workflow.py cajas/tests/test_experiment_config.py cajas/tests/test_experiment_plan_dry_run.py`

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
