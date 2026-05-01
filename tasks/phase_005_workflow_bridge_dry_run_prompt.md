# Phase 5 Prompt: Fix Package Init Names and Add Minimal Qlib Workflow Bridge

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 5 prompt under `tasks/`.
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

Phase 4 completed with commits:

```text
6a2fd959 chore: clean task prompt tracking and handler package init
4b83a488 chore: add pytest dev dependency
4a0c14f3 feat: add prepared dataset adapter validation
908fe367 docs: document prepared dataset adapter workflow
```

Phase 4 added:

- `requirements-dev.txt` with `pytest`
- `tasks/phase_000_*`
- `tasks/phase_001_*`
- `tasks/phase_002_*`
- `tasks/phase_004_package_cleanup_and_dataset_adapter_prompt.md`
- `cajas/datasets/prepared_dataset.py`
- `cajas/scripts/validate_prepared_dataset_adapter.py`
- `cajas/tests/test_prepared_dataset.py`
- updated docs/config

Phase 4 validation:

```text
pytest: 10 passed
handler validation: pass
adapter validation: pass
leakage columns in features: no
```

Known issue from Phase 4 report:

The package init files were reported as:

```text
cajas/handlers/init.py
cajas/datasets/init.py
```

These are not the standard Python package initializer names.

They should be:

```text
cajas/handlers/__init__.py
cajas/datasets/__init__.py
```

## Phase 5 Goal

Phase 5 should do a larger forward step:

1. Fix Python package initializer names.
2. Add a minimal Qlib workflow bridge under `cajas/` that does not modify Qlib core.
3. Add a dry-run experiment runner that loads the prepared dataset adapter and prints Qlib-like train/valid/test data shapes.
4. Add tests for the workflow bridge / experiment runner logic.
5. Update config/docs so Phase 6 can move toward an actual Qlib-compatible training config, but still do not train in Phase 5.

This phase remains a **data/workflow integration validation phase**.

No model training.

No trading.

No backtest/profit analysis.

No qlib core changes.

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
12. Do not add heavy dependencies beyond existing dev-only pytest.
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

Check task prompt policy:

```bash
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_004_package_cleanup_and_dataset_adapter_prompt.md || true
```

Expected:

- `.gitignore` should not ignore `tasks/`.
- `tasks/` should remain tracked project history.

## Task 2: Fix Package Init File Names

Inspect:

```bash
find cajas/handlers cajas/datasets -maxdepth 1 -type f -print | sort
```

If either exists:

```text
cajas/handlers/init.py
cajas/datasets/init.py
```

rename using Git:

```bash
git mv cajas/handlers/init.py cajas/handlers/__init__.py
git mv cajas/datasets/init.py cajas/datasets/__init__.py
```

If the destination already exists, inspect both files and preserve useful exports/comments.

After fixing, verify these paths exist:

```text
cajas/handlers/__init__.py
cajas/datasets/__init__.py
```

Recommended `cajas/handlers/__init__.py` content:

```python
from .prepared_csv_handler import PreparedCsvHandler

__all__ = ["PreparedCsvHandler"]
```

Recommended `cajas/datasets/__init__.py` content:

```python
from .prepared_dataset import PreparedDataset

__all__ = ["PreparedDataset"]
```

Verify imports:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.handlers import PreparedCsvHandler
from cajas.datasets import PreparedDataset
print(PreparedCsvHandler.__name__, PreparedDataset.__name__)
PY
```

## Task 3: Add Minimal Workflow Bridge

Add:

```text
cajas/workflows/__init__.py
cajas/workflows/prepared_workflow.py
```

Purpose:

Create a small Qlib-inspired workflow bridge around `PreparedDataset`.

This should be an external `cajas/` layer, not a Qlib core modification.

Suggested classes/functions:

```python
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class PreparedWorkflowConfig:
    csv_path: str
    label_col: str
    segments: dict[str, tuple[str, str]]

@dataclass(frozen=True)
class SegmentShape:
    segment: str
    feature_rows: int
    feature_cols: int
    label_rows: int
    label_name: str

@dataclass(frozen=True)
class PreparedWorkflowSummary:
    label_col: str
    feature_columns: list[str]
    segment_shapes: list[SegmentShape]

class PreparedWorkflow:
    def __init__(self, config: PreparedWorkflowConfig) -> None: ...

    @property
    def dataset(self) -> PreparedDataset: ...

    def prepare(self, segment: str): ...

    def dry_run(self) -> PreparedWorkflowSummary: ...
```

Expected behavior:

- Wrap `PreparedDataset`.
- Do not train.
- Do not import or require Qlib unless already available and needed.
- Dry-run should validate:
  - train/valid/test all prepare successfully
  - feature/label row counts match
  - feature count > 0
  - leakage columns are absent
- Return a structured summary object.
- Keep labels as strings: `up`, `down`, `flat`.

Add clear docstrings explaining:

- This is Qlib-inspired external workflow validation.
- It is not a trading strategy.
- It is not a full Qlib workflow yet.
- It prepares the shape for later Qlib DatasetH/workflow integration.

## Task 4: Add Workflow Dry-Run CLI

Add:

```text
cajas/scripts/run_prepared_workflow_dry_run.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Default segments:

```text
train: 2025-01-01 to 2025-08-31
valid: 2025-09-01 to 2025-10-31
test:  2025-11-01 to 2025-12-31
```

Optional flags:

```text
--train-start
--train-end
--valid-start
--valid-end
--test-start
--test-end
--json
```

Behavior:

- Build `PreparedWorkflowConfig`.
- Instantiate `PreparedWorkflow`.
- Run `dry_run()`.
- Print:
  - label col
  - feature count
  - segment names
  - feature shape per segment
  - label shape per segment
  - leakage columns check
- If `--json` is passed, print JSON summary.
- Exit non-zero on validation failure.

Example text output:

```text
Prepared workflow dry-run completed.
label: future_direction_8
feature count: 24
segments:
  train: features=(16512, 24), labels=16512
  valid: features=(4225, 24), labels=4225
  test: features=(3985, 24), labels=3985
leakage columns in features: no
training executed: no
```

## Task 5: Add Workflow Tests

Add:

```text
cajas/tests/test_prepared_workflow.py
```

Use temporary CSV data, not real EURUSD data.

Tests should cover:

1. `PreparedWorkflow.dry_run()` returns segment shape summary.
2. Feature/label row counts match.
3. Leakage columns are excluded.
4. Unknown segment raises a clear error through `prepare()`.
5. Empty segment or invalid segment raises a clear error.
6. JSON-serializable summary if you expose a helper for JSON.

Keep tests small and deterministic.

Run:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_prepared_csv_handler.py   cajas/tests/test_prepared_dataset.py   cajas/tests/test_prepared_workflow.py
```

## Task 6: Optional JSON Serialization Helper

If useful, add a method to `PreparedWorkflowSummary` or helper function:

```python
def to_dict(self) -> dict: ...
```

or

```python
def workflow_summary_to_dict(summary: PreparedWorkflowSummary) -> dict: ...
```

Use it in `--json`.

Keep this lightweight.

Do not add pydantic or other dependencies.

## Task 7: Update Config Draft

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Clarify Phase 5 structure:

```yaml
workflow_bridge:
  class: cajas.workflows.prepared_workflow.PreparedWorkflow
  config_class: cajas.workflows.prepared_workflow.PreparedWorkflowConfig
  dataset_class: cajas.datasets.prepared_dataset.PreparedDataset
  handler_class: cajas.handlers.prepared_csv_handler.PreparedCsvHandler
  dry_run_only: true
```

Keep:

```yaml
training:
  enabled: false
```

or equivalent.

Make clear:

- This is still draft/research config.
- It documents the intended workflow shape.
- It does not execute Qlib LightGBM training yet.
- Future leakage columns are excluded.
- `future_direction_8` is a recognition label, not a trading signal.

## Task 8: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 5 section:

- Package init naming fixed.
- `PreparedWorkflow` dry-run bridge added.
- CLI command for workflow dry-run.
- Test command.
- No training/no trading/no qlib core changes.

Integration notes should add Phase 5:

- PreparedWorkflow is a Qlib-inspired bridge.
- It validates dataset shape and segment shape.
- It is still external to Qlib core.
- Phase 6 recommendation:
  - introduce a minimal training-disabled Qlib-style experiment config loader, or
  - build a true Qlib-compatible DatasetH wrapper if feasible,
  - only then consider a controlled LightGBM baseline in a later phase.

Data examples should mention:

- Workflow bridge consumes the Phase 1 prepared CSV.
- Leakage audit columns are never features.
- Labels remain strings.

## Task 9: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/handlers/prepared_csv_handler.py
./.venv-qlib313/bin/python -m py_compile cajas/datasets/prepared_dataset.py
./.venv-qlib313/bin/python -m py_compile cajas/workflows/prepared_workflow.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/validate_prepared_dataset_handler.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/validate_prepared_dataset_adapter.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_prepared_workflow_dry_run.py
```

Run existing validations:

```bash
./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_handler.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8

./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_adapter.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Run new workflow dry-run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Run JSON mode:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8   --json
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_prepared_csv_handler.py   cajas/tests/test_prepared_dataset.py   cajas/tests/test_prepared_workflow.py
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

### Commit 1: package init fix

```bash
git add cajas/handlers/__init__.py cajas/datasets/__init__.py
git add -u cajas/handlers cajas/datasets
git commit -m "fix: use standard package init files"
```

### Commit 2: Phase 5 prompt

If the Phase 5 prompt is in `tasks/`:

```bash
git add tasks/phase_005_workflow_bridge_dry_run_prompt.md
git commit -m "docs: add phase 5 workflow bridge prompt"
```

### Commit 3: workflow bridge

```bash
git add cajas/workflows/__init__.py   cajas/workflows/prepared_workflow.py   cajas/scripts/run_prepared_workflow_dry_run.py   cajas/tests/test_prepared_workflow.py
git commit -m "feat: add prepared workflow dry run bridge"
```

### Commit 4: docs/config updates

```bash
git add cajas/README.md   cajas/docs/qlib_integration_notes.md   cajas/data_examples/README.md   cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
git commit -m "docs: document prepared workflow dry run bridge"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 5 completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- handlers init:
- datasets init:
- old init.py files removed: yes/no

Changed files:
- ...

PreparedWorkflow:
- path:
- config class:
- summary class:
- segments:
- feature count:
- label:
- leakage columns in features: yes/no
- training executed: yes/no

Validation commands run:
- ...

Workflow dry-run summary:
- train features/labels:
- valid features/labels:
- test features/labels:
- json mode: pass/fail

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
