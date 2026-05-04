# Phase 4 Prompt: Package Cleanup, Dev Test Setup, and DatasetH-like Prepared Dataset Adapter

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Do not create `taskDocs/`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 4 prompt under `tasks/`.
- Codex must not silently rewrite previous phase prompt files unless explicitly asked.

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

Phase 3 completed with commits:

```text
99798bf1 chore: allow tracked task prompts
60e51f5c feat: add prepared dataset handler validation
```

Phase 3 added:

- `tasks/phase_003_track_tasks_and_prepared_handler_prompt.md`
- `cajas/handlers/prepared_csv_handler.py`
- `cajas/scripts/validate_prepared_dataset_handler.py`
- `cajas/tests/test_prepared_csv_handler.py`
- README/config/integration notes updates

Phase 3 validation passed with project venv:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/handlers/prepared_csv_handler.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/validate_prepared_dataset_handler.py
./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_handler.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Phase 3 dataset summary:

```text
rows: 24896
time range: 2025-01-01T22:00:00+00:00 to 2025-12-31T19:45:00+00:00
duplicate datetime count: 0
sorted by datetime: yes

full label distribution:
{'down': 12100, 'flat': 106, 'up': 12690}

train rows: 16512
valid rows: 4225
test rows: 3985
```

Known issues from Phase 3:

1. `pytest` is unavailable in `.venv-qlib313`, so tests were added but not run.
2. The changed-files report listed `cajas/handlers/init.py`. This may be a typo or an actual wrong file. Python packages should normally use:

```text
cajas/handlers/__init__.py
```

3. There are untracked older prompt files:

```text
tasks/phase_000_*
tasks/phase_001_*
tasks/phase_002_*
```

These should be reviewed and either tracked as project task history or intentionally removed. Do not leave them ambiguous.

## Phase 4 Goal

Phase 4 should clean up packaging and developer workflow, then add a minimal DatasetH-like adapter layer that makes the prepared dataset closer to Qlib usage without modifying Qlib core and without training a model.

Main objectives:

1. Fix/confirm `cajas/handlers/__init__.py`.
2. Add dev test dependency documentation for `pytest`.
3. Run the Phase 3 tests after installing pytest if acceptable in the local venv.
4. Track the older phase prompt files under `tasks/` if they are present and valid.
5. Add a minimal DatasetH-like prepared dataset adapter under `cajas/`.
6. Add a validation CLI that checks feature/label segment output shape.
7. Update docs/config.

Still no model training.

Still no qlib core changes.

Still no trading.

## Absolute Boundaries

Must follow:

1. Do not modify `qlib/` core.
2. Do not modify official upstream examples.
3. Do not commit raw EURUSD CSV files.
4. Do not commit `tmp/` generated outputs.
5. Do not commit `.codex/`.
6. Do not add `tasks/` to `.gitignore`.
7. Do not create `taskDocs/`.
8. Do not describe `future_direction_8` as a buy/sell signal.
9. Do not train LightGBM or any other model.
10. Do not run backtest/profit/return analysis.
11. Do not add trading strategy, live execution, auto order, or position sizing logic.
12. Do not add heavy dependencies beyond minimal dev-only `pytest`, unless already present.

## Task 1: Check Git State and Branch

Run:

```bash
git status --short
git branch --show-current
```

Confirm current branch:

```text
cajas/market-recognition-phase-0
```

Confirm `tasks/` is not ignored:

```bash
grep -n "tasks\|taskDocs" .gitignore || true
git check-ignore -v tasks/phase_003_track_tasks_and_prepared_handler_prompt.md || true
```

Expected:

- `.gitignore` should not contain `tasks/`.
- `git check-ignore` should not say `tasks/...` is ignored.
- `taskDocs/` should not exist.

## Task 2: Fix or Confirm Python Package Init

Inspect:

```bash
find cajas/handlers -maxdepth 1 -type f -print
```

If there is:

```text
cajas/handlers/init.py
```

then rename it to:

```text
cajas/handlers/__init__.py
```

Use:

```bash
mv cajas/handlers/init.py cajas/handlers/__init__.py
```

if appropriate.

If both exist, inspect contents and keep the correct `__init__.py`, removing duplicate `init.py`.

Then verify imports:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.handlers.prepared_csv_handler import PreparedCsvHandler
print(PreparedCsvHandler.__name__)
PY
```

## Task 3: Add Dev Dependency Documentation for pytest

Check if the repository already has dev requirements:

```bash
find . -maxdepth 3 -iname "*requirements*dev*" -o -name "requirements-dev.txt"
```

If no suitable file exists, add:

```text
requirements-dev.txt
```

with:

```text
pytest
```

If a dev requirements file already exists, add `pytest` there without duplicating it.

Important:

- This is a dev dependency only.
- Do not add pytest to runtime dependency files unless no separate dev dependency convention exists.
- Do not pin an arbitrary version unless the repo already uses pinned dev dependencies.

If installing is allowed locally, run:

```bash
./.venv-qlib313/bin/python -m pip install -r requirements-dev.txt
```

If installation fails or is not appropriate, report it and continue with py_compile/CLI validation.

## Task 4: Run Unit Tests

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py
```

If pytest still unavailable, report it clearly.

If tests fail because of implementation bugs, fix the code or tests.

Do not weaken tests just to pass.

Tests should remain independent of the real EURUSD CSV and `tmp/`.

## Task 5: Track Older Prompt Files

Check:

```bash
find tasks -maxdepth 1 -type f -name "phase_*.md" -print | sort
```

If untracked older prompts exist and are valid project task history, add them to Git.

Expected examples:

```text
tasks/phase_000_*.md
tasks/phase_001_*.md
tasks/phase_002_*.md
tasks/phase_003_track_tasks_and_prepared_handler_prompt.md
tasks/phase_004_package_cleanup_and_dataset_adapter_prompt.md
```

Do not edit old prompt content unless needed to remove secrets or broken paths.

If old prompts are duplicates or invalid, report which ones were left untracked and why.

## Task 6: Add DatasetH-like Prepared Dataset Adapter

Add:

```text
cajas/datasets/__init__.py
cajas/datasets/prepared_dataset.py
```

Implement a lightweight adapter that wraps `PreparedCsvHandler`.

Suggested class:

```python
PreparedDataset
```

Purpose:

- Provide a Qlib-inspired, DatasetH-like interface without depending on or modifying Qlib core.
- Prepare data by named segment.
- Return features and labels separately.
- Keep future leakage columns excluded.
- Stay small and transparent.

Recommended API:

```python
from cajas.datasets.prepared_dataset import PreparedDataset

dataset = PreparedDataset(
    csv_path="tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv",
    label_col="future_direction_8",
    segments={
        "train": ("2025-01-01", "2025-08-31"),
        "valid": ("2025-09-01", "2025-10-31"),
        "test": ("2025-11-01", "2025-12-31"),
    },
)

train_x, train_y = dataset.prepare("train")
valid_x, valid_y = dataset.prepare("valid")
test_x, test_y = dataset.prepare("test")
```

Recommended methods:

```python
class PreparedDataset:
    def __init__(self, csv_path: str, label_col: str, segments: dict[str, tuple[str, str]]) -> None: ...

    @property
    def feature_columns(self) -> list[str]: ...

    @property
    def segments(self) -> dict[str, tuple[str, str]]: ...

    def prepare(self, segment: str): ...

    def prepare_all(self) -> dict[str, tuple[object, object]]: ...

    def summary(self) -> dict: ...
```

Behavior:

- `prepare("train")` returns `(features_df, labels_series_or_df)`.
- Raise a clear error for unknown segment names.
- Raise a clear error for empty segment.
- Use the handler feature columns.
- Do not include:
  - `future_close_8`
  - `future_return_8`
  - `datetime`
  - `symbol`
  - `timeframe`
  - label column
- Do not encode labels in this phase unless already naturally handled. Keep labels as string classes: `up`, `down`, `flat`.

This is not yet a full Qlib DatasetH subclass. Name it as DatasetH-like or Qlib-inspired, not full Qlib-compatible unless it truly is.

## Task 7: Add Dataset Adapter Validation CLI

Add:

```text
cajas/scripts/validate_prepared_dataset_adapter.py
```

CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_adapter.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Default segments:

```text
train: 2025-01-01 to 2025-08-31
valid: 2025-09-01 to 2025-10-31
test:  2025-11-01 to 2025-12-31
```

The script should print:

```text
Prepared dataset adapter validation completed.
feature columns: ...
label: future_direction_8
segments:
  train: X rows, Y labels
  valid: X rows, Y labels
  test: X rows, Y labels
label distribution:
  train: ...
  valid: ...
  test: ...
```

It should exit non-zero if:

- input file missing
- unknown segment
- empty segment
- features/labels row counts mismatch
- no feature columns
- leakage columns are found in features

## Task 8: Add Adapter Unit Tests

Add:

```text
cajas/tests/test_prepared_dataset.py
```

Tests should use temporary CSV data, not real EURUSD data.

Cover:

- `prepare("train")` returns matching feature/label lengths.
- unknown segment raises error.
- empty segment raises error.
- future leakage columns excluded from features.
- labels remain available.

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py
```

## Task 9: Update Config Draft

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Clarify:

- Phase 4 introduces `PreparedDataset` as a DatasetH-like external adapter.
- It is still not a full Qlib workflow.
- It must exclude future leakage columns.
- Training remains disabled/deferred.
- This is market recognition research, not trading.

Add or update fields/comments such as:

```yaml
data_adapter:
  class: cajas.datasets.prepared_dataset.PreparedDataset
  handler_class: cajas.handlers.prepared_csv_handler.PreparedCsvHandler
  label_col: future_direction_8
  leakage_columns:
    - future_close_8
    - future_return_8
  segments:
    train: ["2025-01-01", "2025-08-31"]
    valid: ["2025-09-01", "2025-10-31"]
    test: ["2025-11-01", "2025-12-31"]
```

Use TODO comments for unknown Qlib runtime fields.

Do not make false claims that this can already run Qlib training.

## Task 10: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should include:

- Phase 4 summary.
- How to run handler validation.
- How to run adapter validation.
- How to run tests.
- `requirements-dev.txt` if added.
- Explicit warning: no training/no trading/no qlib core changes.

Integration notes should include:

- Phase 4 starts DatasetH-like external adapter.
- It is intentionally outside qlib core.
- It prepares for future Qlib DatasetH or workflow integration.
- It does not yet run Qlib LightGBM training.

Data examples should document:

- Prepared dataset expected columns.
- Audit columns:
  - `future_close_8`
  - `future_return_8`
- Audit columns are not features.

## Task 11: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Run compile checks:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/handlers/prepared_csv_handler.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/validate_prepared_dataset_handler.py
./.venv-qlib313/bin/python -m py_compile cajas/datasets/prepared_dataset.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/validate_prepared_dataset_adapter.py
```

Run CLIs:

```bash
./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_handler.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8

./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_adapter.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Run tests if pytest installed:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py
```

Check Git:

```bash
git status --short
git diff --stat
git diff
```

Confirm no raw CSV or `tmp/` output is staged.

## Suggested Commits

Prefer multiple focused commits.

### Commit 1: task prompt and package cleanup

```bash
git add .gitignore tasks/ cajas/handlers/__init__.py
git commit -m "chore: clean task prompt tracking and handler package init"
```

Only include `.gitignore` if changed.

### Commit 2: dev test dependency

```bash
git add requirements-dev.txt
git commit -m "chore: add pytest dev dependency"
```

Only if `requirements-dev.txt` changed.

### Commit 3: dataset adapter

```bash
git add cajas/datasets/__init__.py   cajas/datasets/prepared_dataset.py   cajas/scripts/validate_prepared_dataset_adapter.py   cajas/tests/test_prepared_dataset.py   cajas/tests/test_prepared_csv_handler.py
git commit -m "feat: add prepared dataset adapter validation"
```

### Commit 4: docs/config

```bash
git add cajas/README.md   cajas/docs/qlib_integration_notes.md   cajas/data_examples/README.md   cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
git commit -m "docs: document prepared dataset adapter workflow"
```

Then:

```bash
git push
```

If some commits are unnecessary because files did not change, skip them.

## Completion Report Format

Report exactly:

```text
Phase 4 completed.

Branch:
- cajas/market-recognition-phase-0

Task prompt policy:
- tasks/ tracked:
- tasks/ ignored:
- taskDocs present:

Package cleanup:
- handlers init path:
- removed wrong init.py: yes/no/not applicable

Dev test setup:
- requirements-dev.txt added/updated:
- pytest installed in .venv-qlib313: yes/no
- pytest command result:

Changed files:
- ...

PreparedDataset:
- path:
- interface:
- feature count:
- excluded leakage columns:
- label:

Validation commands run:
- ...

Adapter validation summary:
- train features/labels:
- valid features/labels:
- test features/labels:
- leakage columns in features: yes/no

Tests:
- ...

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
- Create `taskDocs/`.
- Treat `future_direction_8` as a buy/sell signal.
