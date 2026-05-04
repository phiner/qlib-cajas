# Phase 6 Prompt: Add Experiment Config Loader and Training-Disabled Experiment Plan Validator

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 6 prompt under `tasks/`.
- Codex must not silently rewrite previous phase prompt files unless explicitly asked.
- Do not create new task prompt directories.

## Repository

Repository working directory:

```text
/home/phiner/projects/research/qlib-cajas/
```

Current branch:

```text
cajas/market-recognition-phase-0
```

## Current Status

Phase 5 completed with commits:

```text
09d4c298 docs: add phase 5 workflow bridge prompt
d4d8dc5e feat: add prepared workflow dry run bridge
4c4a0a50 docs: document prepared workflow dry run bridge
```

Phase 5 added:

- `cajas/workflows/prepared_workflow.py`
- `cajas/scripts/run_prepared_workflow_dry_run.py`
- `cajas/tests/test_prepared_workflow.py`
- docs/config updates

Phase 5 validation:

```text
PreparedWorkflow dry-run: pass
JSON mode: pass
pytest: 16 passed
feature count: 24
label: future_direction_8
leakage columns in features: no
training executed: no
```

Current pipeline:

```text
Phase 1 prepared CSV
  -> PreparedCsvHandler
  -> PreparedDataset
  -> PreparedWorkflow dry-run bridge
```

## Phase 6 Goal

Phase 6 should move one step closer to a Qlib-style experiment while still keeping training disabled.

The goal:

> Add a structured experiment config loader and validator that reads the existing YAML config, resolves the prepared dataset/workflow settings, validates the training-disabled safety gates, and runs a full dry-run experiment plan without training.

This phase should produce a clean bridge between the YAML config and `PreparedWorkflow`.

No model training.

No qlib core changes.

No trading.

No backtest/profit analysis.

## Absolute Boundaries

Must follow:

1. Do not modify `qlib/` core.
2. Do not modify official upstream examples.
3. Do not commit raw EURUSD CSV files.
4. Do not commit `tmp/` generated outputs.
5. Do not commit `.codex/`.
6. Do not add `tasks/` to `.gitignore`.
7. Do not create new task prompt directories.
8. Do not describe `future_direction_8` as a buy/sell signal.
9. Do not train LightGBM or any other model.
10. Do not run backtest/profit/return analysis.
11. Do not add trading strategy, live execution, auto order, or position sizing logic.
12. Do not add heavy dependencies unless already available.
13. Do not claim a config is fully Qlib-runnable unless it has actually been run successfully.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
```

Confirm branch:

```text
cajas/market-recognition-phase-0
```

Confirm `tasks/` is tracked/not ignored:

```bash
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_005_workflow_bridge_dry_run_prompt.md || true
```

Expected:

- `.gitignore` should not ignore `tasks/`.
- `tasks/` remains project task history.

## Task 2: Inspect Current YAML Config

Open:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Review current fields for:

- data source / input CSV
- label column
- leakage columns
- train/valid/test segments
- handler class
- dataset class
- workflow bridge class
- training enabled/disabled flag
- notes saying this is draft/research only

Do not remove existing warnings.

## Task 3: Add Lightweight Config Loader

Add:

```text
cajas/config/__init__.py
cajas/config/experiment_config.py
```

If `cajas/config/` conflicts with another naming convention, use `cajas/experiment_config/`, but prefer `cajas/config/`.

Purpose:

- Load the YAML experiment config.
- Validate required fields.
- Normalize config into typed dataclasses.
- Ensure training is disabled.
- Ensure leakage columns are declared.
- Ensure prepared dataset/workflow classes match the current `cajas/` implementation.

Use only the standard library if possible, plus `yaml` only if PyYAML is already available in the environment. If PyYAML is not available, implement a minimal fallback or report clearly.

Before deciding, run:

```bash
./.venv-qlib313/bin/python - <<'PY'
try:
    import yaml
    print("PyYAML available")
except Exception as exc:
    print("PyYAML unavailable:", exc)
PY
```

If PyYAML is available, use it.

Do not add new runtime dependencies for YAML unless necessary.

Recommended dataclasses:

```python
@dataclass(frozen=True)
class SegmentConfig:
    start: str
    end: str

@dataclass(frozen=True)
class DataAdapterConfig:
    csv_path: str
    label_col: str
    leakage_columns: tuple[str, ...]
    segments: dict[str, SegmentConfig]
    handler_class: str | None = None
    dataset_class: str | None = None

@dataclass(frozen=True)
class WorkflowBridgeConfig:
    workflow_class: str
    dry_run_only: bool

@dataclass(frozen=True)
class TrainingConfig:
    enabled: bool

@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    data_adapter: DataAdapterConfig
    workflow_bridge: WorkflowBridgeConfig
    training: TrainingConfig
```

Recommended functions:

```python
def load_experiment_config(path: str | Path) -> ExperimentConfig: ...

def validate_experiment_config(config: ExperimentConfig) -> list[str]: ...

def assert_training_disabled(config: ExperimentConfig) -> None: ...

def build_workflow_config(config: ExperimentConfig, csv_path_override: str | None = None) -> PreparedWorkflowConfig: ...
```

Important:

- `validate_experiment_config()` should return warnings or issues as strings.
- Fatal config errors should raise a clear `ValueError`.
- `assert_training_disabled()` should raise if training is enabled.
- The loader should not train anything.
- The loader should not import Qlib unless necessary. Prefer not to import Qlib in Phase 6.

## Task 4: Normalize YAML Config Shape

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Make sure it has clear fields compatible with the loader.

Suggested shape:

```yaml
name: fx_eurusd_15m_lightgbm_future_direction_8
description: >
  Draft market recognition research config for EURUSD 15m future_direction_8.
  This config is training-disabled in Phase 6.

research_scope:
  market_recognition_only: true
  trading_signal: false
  live_trading: false
  backtest_profit_analysis: false

data_adapter:
  csv_path: tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
  label_col: future_direction_8
  handler_class: cajas.handlers.prepared_csv_handler.PreparedCsvHandler
  dataset_class: cajas.datasets.prepared_dataset.PreparedDataset
  leakage_columns:
    - future_close_8
    - future_return_8
  segments:
    train:
      start: "2025-01-01"
      end: "2025-08-31"
    valid:
      start: "2025-09-01"
      end: "2025-10-31"
    test:
      start: "2025-11-01"
      end: "2025-12-31"

workflow_bridge:
  class: cajas.workflows.prepared_workflow.PreparedWorkflow
  config_class: cajas.workflows.prepared_workflow.PreparedWorkflowConfig
  dry_run_only: true

model:
  draft_class: LightGBM
  enabled: false
  note: "Model training is disabled in Phase 6."

training:
  enabled: false
  reason: "Phase 6 validates config and workflow dry-run only."

qlib:
  core_modified: false
  provider_format_enabled: false
  note: "No Qlib core provider integration is performed in Phase 6."
```

If the current YAML has useful fields, preserve them.

Do not add fields that imply trading.

## Task 5: Add Experiment Plan Dry-Run CLI

Add:

```text
cajas/scripts/run_experiment_plan_dry_run.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--json
--strict
```

Behavior:

1. Load YAML config.
2. Validate config.
3. Assert training disabled.
4. Build `PreparedWorkflowConfig`.
5. Run `PreparedWorkflow.dry_run()`.
6. Print:
   - config name
   - label column
   - csv path
   - training enabled: false
   - dry_run_only: true
   - feature count
   - segment shapes
   - leakage columns in features: no
   - warnings/issues, if any
7. If `--json`, print JSON summary.
8. If `--strict`, exit non-zero when validation issues exist.
9. Exit non-zero if training is enabled.

Example text output:

```text
Experiment plan dry-run completed.
config: fx_eurusd_15m_lightgbm_future_direction_8
csv: tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
label: future_direction_8
training enabled: false
workflow dry-run only: true
feature count: 24
segments:
  train: features=(16512, 24), labels=16512
  valid: features=(4225, 24), labels=4225
  test: features=(3985, 24), labels=3985
leakage columns in features: no
training executed: no
```

## Task 6: Add Config Loader and Plan Tests

Add:

```text
cajas/tests/test_experiment_config.py
cajas/tests/test_experiment_plan_dry_run.py
```

Use temporary YAML and temporary CSV data, not the real EURUSD CSV.

Tests should cover:

### Config loader

- Loads valid config.
- Parses train/valid/test segments.
- Fails if label column missing.
- Fails if training.enabled is true.
- Fails or warns if leakage columns are missing.
- Supports input override when building workflow config.

### Experiment plan dry-run

- Dry-run returns matching segment shapes.
- JSON output helper is serializable if implemented.
- Strict mode behavior can be covered at function level if CLI testing is too heavy.
- Training is never executed.

Do not add heavy test frameworks beyond pytest.

## Task 7: Add Optional Internal Helper for JSON Summary

If useful, add a small module:

```text
cajas/utils/json_utils.py
```

or keep JSON conversion local to scripts.

Do not add dependencies.

## Task 8: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 6:

- Config loader added.
- Experiment plan dry-run CLI command.
- Training-disabled safety gate.
- Test command.
- No qlib core changes/no training/no trading.

Integration notes should add Phase 6:

- YAML config now drives the dry-run workflow bridge.
- This creates a bridge from config to workflow without Qlib core modification.
- Phase 7 recommendation:
  - Add a minimal Qlib-style recorder/artifact output for dry-run reports, or
  - Start a controlled, still non-trading LightGBM baseline preparation only after config contract stabilizes.
- Make clear that actual training remains disabled until explicitly enabled in a later phase.

Data examples should add:

- Config points to Phase 1 prepared CSV by default.
- CSV path can be overridden for local testing.
- Leakage audit columns remain non-features.

## Task 9: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/config/experiment_config.py
./.venv-qlib313/bin/python -m py_compile cajas/workflows/prepared_workflow.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_prepared_workflow_dry_run.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_experiment_plan_dry_run.py
```

Run existing validations:

```bash
./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_handler.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8

./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_adapter.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8

./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Run new experiment plan dry-run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --json

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --strict
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_prepared_csv_handler.py   cajas/tests/test_prepared_dataset.py   cajas/tests/test_prepared_workflow.py   cajas/tests/test_experiment_config.py   cajas/tests/test_experiment_plan_dry_run.py
```

Check Git:

```bash
git status --short
git diff --stat
git diff
```

Confirm no raw CSV or `tmp/` generated outputs are staged.

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 6 prompt

```bash
git add tasks/phase_006_experiment_config_plan_dry_run_prompt.md
git commit -m "docs: add phase 6 experiment config prompt"
```

### Commit 2: config loader

```bash
git add cajas/config/__init__.py   cajas/config/experiment_config.py   cajas/tests/test_experiment_config.py
git commit -m "feat: add training-disabled experiment config loader"
```

### Commit 3: experiment plan dry-run

```bash
git add cajas/scripts/run_experiment_plan_dry_run.py   cajas/tests/test_experiment_plan_dry_run.py
git commit -m "feat: add experiment plan dry run validation"
```

### Commit 4: YAML/docs

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   cajas/README.md   cajas/docs/qlib_integration_notes.md   cajas/data_examples/README.md
git commit -m "docs: document training-disabled experiment plan"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 6 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Experiment config:
- path:
- loader:
- config name:
- label:
- csv path:
- training enabled:
- dry_run_only:
- leakage columns:

Experiment plan dry-run:
- text mode:
- json mode:
- strict mode:
- feature count:
- leakage columns in features:
- training executed:

Segment summary:
- train features/labels:
- valid features/labels:
- test features/labels:

Validation commands run:
- ...

Tests:
- total:
- result:

Git:
- commit(s):
- push: done/not done

Notes:
- ...
```

## Forbidden Work

Do not:

- Modify `qlib/` core.
- Modify official examples.
- Train any model.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
