# Phase 3 Prompt: Track tasks Directory and Build Minimal Prepared Dataset Handler

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- Codex may read files under `tasks/`.
- Codex may add new phase prompt files under `tasks/` when explicitly asked.
- Codex must not silently rewrite previous phase prompt files unless explicitly asked.
- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Do not create `taskDocs/`.

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

Phase 0 completed:

- Created `cajas/` research layer.
- Added EURUSD 15m dataset preparation script.
- Added first draft LightGBM/Qlib experiment config.
- Added agent workflow documentation.
- Did not modify `qlib/` core.

Phase 1 completed:

- Ran real EURUSD 15m CSV through `prepare_fx_dataset.py`.
- Generated local outputs:

```text
tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
tmp/cajas/eurusd_15m_phase1/dataset_manifest.json
```

Dataset summary:

```text
raw rows: 24904
output rows: 24896
time range: 2025-01-01 22:00:00 to 2025-12-31 19:45:00
future_direction_8 distribution: up=12690, down=12100, flat=106
duplicate datetime count: 0
sorted by datetime: yes
```

Phase 1 commit:

```text
7ec5eab2 feat: validate phase 1 EURUSD dataset preparation
```

Phase 2 completed:

- Added Qlib integration notes:

```text
cajas/docs/qlib_integration_notes.md
```

- Compared:
  - Path A: Qlib native provider format
  - Path B: custom external DataHandler/Dataset under `cajas/`
- Recommended next path:
  - Start with Path B.
  - Implement a small external prepared dataset handler.
  - Validate segment slicing before model training.
  - Keep Qlib core unchanged.

Phase 2 commit:

```text
ab70eaf3 docs: map qlib integration path for cajas EURUSD research
```

## Phase 3 Goal

Phase 3 should do more than a small cleanup. The goal is:

> Make the project ready for a later Qlib DatasetH/workflow integration by adding a minimal, testable prepared CSV handler, a validation CLI, tracked task prompt directory rules, and updated docs.

This phase still does **not** train a model.

This phase still does **not** modify Qlib core.

This phase still does **not** introduce any trading, live execution, automatic ordering, position sizing, or profit analysis.

## Absolute Boundaries

Must follow:

1. Do not modify `qlib/` core.
2. Do not modify upstream official example behavior.
3. Do not commit raw EURUSD CSV files.
4. Do not commit `tmp/` generated outputs.
5. Do not commit `.codex/`.
6. Do not add `tasks/` to `.gitignore`.
7. Do not create or use `taskDocs/`.
8. Do not describe `future_direction_8` as a buy/sell signal.
9. Do not train LightGBM or any other model in this phase.
10. Do not run backtest/profit/return analysis.
11. Do not add trading strategy or execution logic.

## Task 1: Normalize Git Ignore and Track tasks/

Check `.gitignore`:

```bash
grep -n "tasks\|taskDocs" .gitignore || true
```

If `.gitignore` contains any of the following, remove them:

```gitignore
tasks/
taskDocs/
taskDocs/codex_tasks/
```

Do not add `tasks/` to `.gitignore`.

Ensure `tasks/` exists:

```bash
mkdir -p tasks
```

This prompt file itself should eventually live under:

```text
tasks/phase_003_track_tasks_and_prepared_handler_prompt.md
```

If the file is not already there, do not worry. Do not fail the phase just because the prompt file was copied manually by the user later.

## Task 2: Add Minimal Prepared CSV Handler

Add:

```text
cajas/handlers/__init__.py
cajas/handlers/prepared_csv_handler.py
```

Implement a lightweight `PreparedCsvHandler`.

Recommended responsibilities:

- Read Phase 1 `prepared_dataset.csv`.
- Parse `datetime`.
- Sort by `datetime`.
- Validate required columns.
- Validate no duplicate `datetime`.
- Identify candidate feature columns.
- Store label column.
- Provide dataset summary.
- Provide label distribution.
- Provide segment slicing by date range.
- Provide train/valid/test slicing helper.
- Avoid trading semantics.

Recommended API shape:

```python
from cajas.handlers.prepared_csv_handler import PreparedCsvHandler

handler = PreparedCsvHandler(
    csv_path="tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv",
    label_col="future_direction_8",
)

summary = handler.summary()

train_df = handler.prepare_segment("2025-01-01", "2025-08-31")
valid_df = handler.prepare_segment("2025-09-01", "2025-10-31")
test_df = handler.prepare_segment("2025-11-01", "2025-12-31")
```

Suggested class methods:

```python
class PreparedCsvHandler:
    def __init__(self, csv_path: str, label_col: str = "future_direction_8") -> None: ...

    @property
    def feature_columns(self) -> list[str]: ...

    @property
    def label_col(self) -> str: ...

    def summary(self) -> dict: ...

    def label_distribution(self, df=None) -> dict: ...

    def prepare_segment(self, start: str, end: str): ...

    def prepare_segments(self, segments: dict[str, tuple[str, str]]) -> dict[str, object]: ...
```

Required columns:

```text
datetime
symbol
timeframe
open
high
low
close
volume
future_direction_8
```

Candidate feature column rules:

- Include numeric columns.
- Exclude:
  - `datetime`
  - `symbol`
  - `timeframe`
  - label column
  - any obvious future leakage columns such as `future_close_8` and `future_return_8`

Important:

- `future_close_8` and `future_return_8` can exist in the prepared dataset for auditability, but they must not be treated as candidate features.
- Do not convert the label into trading actions.
- Keep this handler small and easy to inspect.

## Task 3: Add Validation CLI

Add:

```text
cajas/scripts/validate_prepared_dataset_handler.py
```

CLI requirements:

```bash
python cajas/scripts/validate_prepared_dataset_handler.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

Default segments:

```text
train: 2025-01-01 to 2025-08-31
valid: 2025-09-01 to 2025-10-31
test:  2025-11-01 to 2025-12-31
```

The script should:

- Instantiate `PreparedCsvHandler`.
- Print total row count.
- Print time range.
- Print feature column count and names.
- Print label distribution.
- Slice train/valid/test.
- Print segment row counts.
- Print segment label distributions.
- Exit non-zero if:
  - input file missing
  - required columns missing
  - duplicate datetime found
  - segment has zero rows
  - label column missing
  - no usable feature columns found

Optional CLI flags:

```text
--train-start
--train-end
--valid-start
--valid-end
--test-start
--test-end
```

## Task 4: Add Minimal Tests If Practical

If repository test setup is not too heavy, add small unit tests under:

```text
cajas/tests/test_prepared_csv_handler.py
```

The tests can create a temporary CSV with a few rows and verify:

- required columns validation
- feature column exclusion of future leakage columns
- segment slicing
- duplicate datetime rejection
- label distribution

If test setup is unclear, do not over-engineer. The validation CLI is required; unit tests are optional but preferred.

If tests are added, keep them independent of the real EURUSD CSV and `tmp/`.

## Task 5: Update Config Draft

Review:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Update it so it clearly states:

- It is still a draft.
- Data source is Phase 1 prepared CSV.
- Handler target is `cajas.handlers.prepared_csv_handler.PreparedCsvHandler`.
- Label is `future_direction_8`.
- Future leakage columns must not be used as features:
  - `future_close_8`
  - `future_return_8`
- No training should be run in Phase 3.
- No trading strategy or live execution.

Do not pretend the config is fully runnable through Qlib if it is not yet runnable.

Use TODO comments for unknown Qlib-specific fields.

## Task 6: Update Documentation

Update:

```text
cajas/README.md
```

Add Phase 3 section covering:

- `tasks/` is now tracked as project task history.
- `tasks/` should not be ignored.
- Minimal prepared CSV handler added.
- Validation CLI command.
- Phase 3 validates data access and segment slicing only.
- No training, no qlib core changes, no trading.

Update:

```text
cajas/docs/qlib_integration_notes.md
```

Add Phase 3 notes:

- Path B has started implementation through `PreparedCsvHandler`.
- It is not yet a full Qlib provider.
- It prepares the shape needed for a future Qlib DatasetH wrapper.
- It explicitly excludes future leakage fields from features.
- Recommended Phase 4:
  - Add a Qlib-compatible wrapper or experiment runner that validates DatasetH-like prepare semantics.
  - Still avoid model training until the dataset contract is stable.

Update or add:

```text
cajas/data_examples/README.md
```

If useful, document the prepared dataset expected columns, including the rule that `future_close_8` and `future_return_8` are audit columns, not features.

## Task 7: Run Validation Commands

Run:

```bash
git status
git branch --show-current
```

Run syntax checks:

```bash
python -m py_compile cajas/handlers/prepared_csv_handler.py
python -m py_compile cajas/scripts/validate_prepared_dataset_handler.py
```

Run the handler validation:

```bash
python cajas/scripts/validate_prepared_dataset_handler.py   --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv   --label-col future_direction_8
```

If tests were added, run the narrow test command. Examples:

```bash
python -m pytest cajas/tests/test_prepared_csv_handler.py
```

If pytest is unavailable, do not install new dependencies automatically. Report that tests were not run because pytest is unavailable, but still run py_compile and the validation CLI.

Check final Git state:

```bash
git status
git diff --stat
git diff
```

Confirm no raw CSV or `tmp/` generated output is staged.

## Suggested Commits

Prefer two commits if both `.gitignore` and code/docs changed.

Commit 1, only if `.gitignore` changed:

```bash
git add .gitignore
git commit -m "chore: allow tracked task prompts"
```

Commit 2:

```bash
git add tasks/   cajas/README.md   cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   cajas/data_examples/README.md   cajas/docs/qlib_integration_notes.md   cajas/handlers/__init__.py   cajas/handlers/prepared_csv_handler.py   cajas/scripts/validate_prepared_dataset_handler.py
```

If tests were added:

```bash
git add cajas/tests/test_prepared_csv_handler.py
```

Then:

```bash
git commit -m "feat: add prepared dataset handler validation"
git push
```

If the phase prompt file under `tasks/` is added manually before Codex runs, include it in the same docs/code commit or a separate docs commit:

```bash
git add tasks/phase_003_track_tasks_and_prepared_handler_prompt.md
git commit -m "docs: track phase 3 codex prompt"
```

Avoid committing old duplicate prompt locations.

## Completion Report Format

Report exactly in this style:

```text
Phase 3 completed.

Branch:
- cajas/market-recognition-phase-0

Task prompt policy:
- tasks/ tracked: yes/no
- tasks/ ignored in .gitignore: yes/no
- taskDocs present: yes/no

Changed files:
- ...

Handler:
- path:
- required columns:
- feature count:
- excluded leakage columns:
- label:

Validation commands run:
- ...

Dataset summary:
- rows:
- time range:
- duplicate datetime count:
- sorted by datetime:

Segment summary:
- train rows:
- valid rows:
- test rows:

Label distribution:
- full:
- train:
- valid:
- test:

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
- Train a model.
- Run backtest or profit analysis.
- Add trading strategy.
- Add live trading or order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Create `taskDocs/`.
- Treat `future_direction_8` as a buy/sell signal.
