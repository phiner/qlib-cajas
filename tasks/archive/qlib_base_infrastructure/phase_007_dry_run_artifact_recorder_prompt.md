# Phase 7 Prompt: Fix Config Package Init and Add Dry-Run Artifact Recorder

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 7 prompt under `tasks/`.
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

Phase 6 completed with commits:

```text
661189a4 docs: add phase 6 experiment config prompt
9ff4f55c feat: add training-disabled experiment config loader
b5a66c29 feat: add experiment plan dry run validation
b518078a docs: document training-disabled experiment plan
```

Phase 6 added:

- `cajas/config/experiment_config.py`
- `cajas/scripts/run_experiment_plan_dry_run.py`
- config loader tests
- experiment plan dry-run tests
- YAML/docs updates

Phase 6 validation:

```text
experiment plan dry-run text mode: pass
experiment plan dry-run json mode: pass
experiment plan dry-run strict mode: pass
pytest: 24 passed
training executed: no
```

Known issue from Phase 6 report:

The config package init file was reported as:

```text
cajas/config/init.py
```

This is not the standard Python package initializer name.

It should be:

```text
cajas/config/__init__.py
```

## Phase 7 Goal

Phase 7 should move the project from "dry-run only" toward reproducible experiment planning, still without model training.

Main objectives:

1. Fix `cajas/config/init.py` to `cajas/config/__init__.py`.
2. Add a lightweight dry-run artifact recorder under `cajas/`.
3. Extend experiment plan dry-run so it can optionally write a local run directory with JSON artifacts.
4. Add a run manifest, config snapshot, workflow summary, and validation report.
5. Add tests for artifact writing.
6. Update docs/config.

This phase still does not train a model.

This phase still does not modify Qlib core.

This phase still does not introduce trading, backtesting, profit analysis, live execution, or automatic ordering.

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
12. Do not add heavy dependencies beyond existing dependencies.
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
git check-ignore -v tasks/phase_006_experiment_config_plan_dry_run_prompt.md || true
```

Expected:

- `.gitignore` should not ignore `tasks/`.

## Task 2: Fix Config Package Init File

Inspect:

```bash
find cajas/config -maxdepth 1 -type f -print | sort
```

If this exists:

```text
cajas/config/init.py
```

rename it with Git:

```bash
git mv cajas/config/init.py cajas/config/__init__.py
```

If both exist, inspect both and preserve useful exports/comments.

Recommended `cajas/config/__init__.py` content:

```python
from .experiment_config import (
    DataAdapterConfig,
    ExperimentConfig,
    SegmentConfig,
    TrainingConfig,
    WorkflowBridgeConfig,
    assert_training_disabled,
    build_workflow_config,
    load_experiment_config,
    validate_experiment_config,
)

__all__ = [
    "DataAdapterConfig",
    "ExperimentConfig",
    "SegmentConfig",
    "TrainingConfig",
    "WorkflowBridgeConfig",
    "assert_training_disabled",
    "build_workflow_config",
    "load_experiment_config",
    "validate_experiment_config",
]
```

Verify import:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.config import load_experiment_config, build_workflow_config
print(load_experiment_config.__name__, build_workflow_config.__name__)
PY
```

## Task 3: Add Dry-Run Artifact Recorder

Add:

```text
cajas/recorders/__init__.py
cajas/recorders/dry_run_recorder.py
```

Purpose:

- Write reproducible local dry-run artifacts.
- Keep output under a user-provided output directory.
- Do not commit generated artifacts.
- Avoid Qlib core dependencies.

Suggested classes/functions:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

@dataclass(frozen=True)
class DryRunArtifactPaths:
    run_dir: Path
    manifest_path: Path
    config_snapshot_path: Path
    workflow_summary_path: Path
    validation_report_path: Path

class DryRunRecorder:
    def __init__(self, output_dir: str | Path, run_name: str | None = None) -> None: ...

    @property
    def paths(self) -> DryRunArtifactPaths: ...

    def write_manifest(self, manifest: Mapping[str, Any]) -> Path: ...

    def write_config_snapshot(self, config_data: Mapping[str, Any]) -> Path: ...

    def write_workflow_summary(self, summary_data: Mapping[str, Any]) -> Path: ...

    def write_validation_report(self, report_data: Mapping[str, Any]) -> Path: ...

    def write_all(
        self,
        manifest: Mapping[str, Any],
        config_snapshot: Mapping[str, Any],
        workflow_summary: Mapping[str, Any],
        validation_report: Mapping[str, Any],
    ) -> DryRunArtifactPaths: ...
```

Artifact file names:

```text
run_manifest.json
config_snapshot.json
workflow_summary.json
validation_report.json
```

Run directory behavior:

- If `run_name` is provided, use:

```text
<output_dir>/<run_name>/
```

- If `run_name` is not provided, create a deterministic or timestamped name such as:

```text
dry_run_<YYYYMMDD_HHMMSS>/
```

Implementation rules:

- Use only standard library.
- JSON should be pretty printed with sorted keys where practical.
- Do not overwrite an existing run directory unless explicitly safe. Prefer raising `FileExistsError` for existing run directory.
- Store relative paths or strings that are easy to read.
- Do not include raw data rows.

## Task 4: Extend Experiment Plan Dry-Run CLI With Artifact Output

Update:

```text
cajas/scripts/run_experiment_plan_dry_run.py
```

Add optional flags:

```text
--output-dir tmp/cajas/experiment_dry_runs
--run-name phase7_dry_run
--write-artifacts
```

Behavior:

- Default behavior remains print-only. No files are written unless `--write-artifacts` is passed.
- When `--write-artifacts` is passed:
  - create the run directory
  - write `run_manifest.json`
  - write `config_snapshot.json`
  - write `workflow_summary.json`
  - write `validation_report.json`
  - print artifact paths

Example:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --write-artifacts   --output-dir tmp/cajas/experiment_dry_runs   --run-name phase7_eurusd_15m_dry_run
```

Expected text output should include:

```text
artifacts written: yes
run directory: tmp/cajas/experiment_dry_runs/phase7_eurusd_15m_dry_run
training executed: no
```

If the run directory already exists, the script should fail clearly unless you implement a safe unique suffix. Prefer failing clearly in Phase 7.

## Task 5: Artifact Content Requirements

### run_manifest.json

Include:

```json
{
  "run_name": "phase7_eurusd_15m_dry_run",
  "run_type": "experiment_plan_dry_run",
  "config_name": "fx_eurusd_15m_lightgbm_future_direction_8",
  "label_col": "future_direction_8",
  "training_enabled": false,
  "training_executed": false,
  "qlib_core_modified": false,
  "created_by": "cajas/scripts/run_experiment_plan_dry_run.py"
}
```

### config_snapshot.json

Include normalized config values from `ExperimentConfig`, not the raw YAML text.

Do not include raw dataset rows.

### workflow_summary.json

Use the `PreparedWorkflowSummary.to_dict()` result if available.

Include:

- feature columns
- feature count
- segment shapes
- label column

### validation_report.json

Include:

- validation issues/warnings
- strict mode status
- leakage columns declared
- leakage columns found in features: false
- training disabled check: pass
- dry_run_only check: pass

## Task 6: Add Recorder Tests

Add:

```text
cajas/tests/test_dry_run_recorder.py
```

Tests should cover:

- recorder creates expected files
- files contain valid JSON
- existing run directory raises clear error
- `write_all()` returns expected paths
- no raw data rows are required

Use temporary directories only.

## Task 7: Add Experiment Artifact CLI Tests

Update or add:

```text
cajas/tests/test_experiment_plan_artifacts.py
```

Tests should cover:

- a dry-run with artifact writing creates all four JSON files
- artifact manifest has `training_executed: false`
- workflow summary has segment shapes
- validation report says leakage columns found in features is false
- existing run name fails or raises clearly

Avoid shelling out if direct function-level testing is simpler.

If the script currently has a large `main()` only, consider extracting a small function:

```python
def run_experiment_plan_dry_run(args: argparse.Namespace) -> dict: ...
```

or:

```python
def build_experiment_plan_result(...) -> dict: ...
```

Do not over-engineer.

## Task 8: Update YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add a dry-run artifact section:

```yaml
artifacts:
  enabled: false
  default_output_dir: tmp/cajas/experiment_dry_runs
  default_run_name: phase7_eurusd_15m_dry_run
  generated_files:
    - run_manifest.json
    - config_snapshot.json
    - workflow_summary.json
    - validation_report.json
```

Clarify:

- Artifact writing is optional and local.
- Generated artifacts under `tmp/` are not committed.
- Training remains disabled.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 7:

- Dry-run artifact recorder added.
- CLI command for writing artifacts.
- Artifact file names.
- Generated artifact outputs stay under `tmp/` and are not committed.
- Test command.
- No qlib core changes/no training/no trading.

Integration notes should add Phase 7:

- Dry-run artifacts create reproducible experiment plan records.
- This is Qlib-recorder-inspired but not Qlib core.
- Phase 8 recommendation:
  - add a controlled baseline training preparation gate, still disabled by default, or
  - implement a true Qlib DatasetH compatibility probe if feasible.
- Actual model training remains disabled until explicitly enabled in a later phase.

Data examples should add:

- Dry-run artifacts do not contain raw dataset rows.
- Prepared CSV remains the local source.
- `tmp/` output is local-only.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/config/experiment_config.py
./.venv-qlib313/bin/python -m py_compile cajas/recorders/dry_run_recorder.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_experiment_plan_dry_run.py
```

Run existing dry-run commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --json

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --strict
```

Run artifact dry-run:

```bash
rm -rf tmp/cajas/experiment_dry_runs/phase7_eurusd_15m_dry_run

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --write-artifacts   --output-dir tmp/cajas/experiment_dry_runs   --run-name phase7_eurusd_15m_dry_run
```

Inspect generated files locally, but do not commit them:

```bash
find tmp/cajas/experiment_dry_runs/phase7_eurusd_15m_dry_run -maxdepth 1 -type f -print | sort
cat tmp/cajas/experiment_dry_runs/phase7_eurusd_15m_dry_run/run_manifest.json
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_prepared_csv_handler.py   cajas/tests/test_prepared_dataset.py   cajas/tests/test_prepared_workflow.py   cajas/tests/test_experiment_config.py   cajas/tests/test_experiment_plan_dry_run.py   cajas/tests/test_dry_run_recorder.py   cajas/tests/test_experiment_plan_artifacts.py
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

### Commit 1: Phase 7 prompt and config init fix

```bash
git add tasks/phase_007_dry_run_artifact_recorder_prompt.md
git add cajas/config/__init__.py
git add -u cajas/config
git commit -m "fix: use standard config package init"
```

If the prompt and init fix should be separate in your local workflow, split them.

### Commit 2: artifact recorder

```bash
git add cajas/recorders/__init__.py   cajas/recorders/dry_run_recorder.py   cajas/tests/test_dry_run_recorder.py
git commit -m "feat: add dry run artifact recorder"
```

### Commit 3: experiment plan artifact output

```bash
git add cajas/scripts/run_experiment_plan_dry_run.py   cajas/tests/test_experiment_plan_artifacts.py   cajas/tests/test_experiment_plan_dry_run.py
git commit -m "feat: write experiment plan dry run artifacts"
```

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   cajas/README.md   cajas/docs/qlib_integration_notes.md   cajas/data_examples/README.md
git commit -m "docs: document dry run artifact workflow"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 7 completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- config init:
- old init.py removed: yes/no/not applicable

Changed files:
- ...

DryRunRecorder:
- path:
- artifact files:
- overwrite behavior:
- training executed:

Experiment artifact dry-run:
- text mode:
- json mode:
- strict mode:
- write artifacts:
- run directory:
- files written:

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
