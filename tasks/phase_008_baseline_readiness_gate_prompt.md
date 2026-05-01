# Phase 8 Prompt: Fix Recorder Init and Add Baseline Readiness Gate

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 8 prompt under `tasks/`.
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

Phase 7 completed with commits:

```text
bc0bc8f4 docs: add phase 7 dry run artifact prompt
8452fc63 feat: add dry run artifact recorder
375942d0 feat: write experiment plan dry run artifacts
a8b27bbc docs: document dry run artifact workflow
```

Phase 7 validation:

```text
text mode: pass
json mode: pass
strict mode: pass
artifact writing: pass
pytest: 28 passed
training executed: no
```

Known issue from Phase 7 report:

The recorder package init file was reported as:

```text
cajas/recorders/init.py
```

This should be:

```text
cajas/recorders/__init__.py
```

Also note: the Phase 7 reported pytest command text had typos like `caixas/tests/...`, but the final result was 28 passed. In Phase 8, run the correct `cajas/tests/...` paths.

## Phase 8 Goal

Phase 8 prepares the project for a future controlled baseline without enabling training.

Main objectives:

1. Fix `cajas/recorders/init.py` to `cajas/recorders/__init__.py`.
2. Add feature audit and label audit modules.
3. Add a baseline readiness gate that checks whether the current prepared dataset/config/workflow is safe and complete enough for a future baseline phase.
4. Add a readiness CLI with text, JSON, strict, and optional artifact output.
5. Add tests and documentation.

No model training. No Qlib core changes. No trading, backtesting, profit analysis, live execution, or automatic ordering.

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
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_007_dry_run_artifact_recorder_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.

## Task 2: Fix Recorder Package Init File

Inspect:

```bash
find cajas/recorders -maxdepth 1 -type f -print | sort
```

If this exists:

```text
cajas/recorders/init.py
```

rename it with Git:

```bash
git mv cajas/recorders/init.py cajas/recorders/__init__.py
```

If both exist, inspect both and preserve useful exports/comments.

Recommended `cajas/recorders/__init__.py` content:

```python
from .dry_run_recorder import DryRunArtifactPaths, DryRunRecorder

__all__ = ["DryRunArtifactPaths", "DryRunRecorder"]
```

Verify import:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.recorders import DryRunRecorder, DryRunArtifactPaths
print(DryRunRecorder.__name__, DryRunArtifactPaths.__name__)
PY
```

## Task 3: Add Feature Audit Module

Add:

```text
cajas/audits/__init__.py
cajas/audits/feature_audit.py
```

Purpose:

- Audit candidate feature columns before any future baseline.
- Ensure leakage columns are excluded.
- Detect non-numeric feature columns.
- Detect all-null or constant feature columns.
- Summarize missing values.
- Summarize feature count and feature names.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class FeatureAuditIssue:
    severity: str
    code: str
    message: str
    column: str | None = None

@dataclass(frozen=True)
class FeatureAuditReport:
    feature_count: int
    feature_columns: list[str]
    leakage_columns_declared: list[str]
    leakage_columns_found: list[str]
    non_numeric_features: list[str]
    all_null_features: list[str]
    constant_features: list[str]
    missing_value_counts: dict[str, int]
    issues: list[FeatureAuditIssue]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def audit_features(
    features_df,
    *,
    declared_leakage_columns: list[str] | tuple[str, ...],
) -> FeatureAuditReport: ...
```

Rules:

- Leakage columns in features are errors.
- No feature columns is an error.
- Non-numeric feature columns are errors.
- All-null feature columns are errors.
- Constant columns are warnings, not errors.
- Missing values are warnings unless the whole column is null.
- Do not mutate input DataFrame.
- Use pandas already available in the project venv.

## Task 4: Add Label Audit Module

Add:

```text
cajas/audits/label_audit.py
```

Purpose:

- Audit classification labels before any future baseline.
- Confirm expected classes.
- Summarize label distribution.
- Detect missing labels.
- Detect very rare classes.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class LabelAuditIssue:
    severity: str
    code: str
    message: str
    label: str | None = None

@dataclass(frozen=True)
class LabelAuditReport:
    label_col: str
    expected_classes: list[str]
    observed_classes: list[str]
    distribution: dict[str, int]
    missing_count: int
    total_count: int
    issues: list[LabelAuditIssue]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def audit_labels(
    labels,
    *,
    label_col: str = "future_direction_8",
    expected_classes: tuple[str, ...] = ("down", "flat", "up"),
    rare_class_min_count: int = 10,
) -> LabelAuditReport: ...
```

Rules:

- Missing labels are errors.
- Unknown classes are errors.
- Missing expected classes are warnings or errors. Use warning if the segment is small, but error for full dataset if a class is entirely absent.
- Very rare classes are warnings.
- Keep label semantics neutral. No trading language.

## Task 5: Add Baseline Readiness Gate

Add:

```text
cajas/readiness/__init__.py
cajas/readiness/baseline_readiness.py
```

Purpose:

- Combine config validation, workflow dry-run, feature audit, and label audit into a single readiness report.
- Training remains disabled.
- The gate answers: "Is this dataset/config safe enough to consider a future baseline phase?"

Suggested dataclass:

```python
@dataclass(frozen=True)
class BaselineReadinessReport:
    ready: bool
    training_enabled: bool
    training_executed: bool
    config_name: str
    label_col: str
    feature_count: int
    segments: dict[str, dict[str, int]]
    feature_audit: dict
    label_audit: dict
    issues: list[dict]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_baseline_readiness_check(
    *,
    config_path: str,
    input_override: str | None = None,
    strict: bool = False,
) -> BaselineReadinessReport: ...
```

Behavior:

1. Load experiment config.
2. Assert training disabled.
3. Build workflow config.
4. Run `PreparedWorkflow.dry_run()`.
5. Prepare all segments.
6. Run feature audit.
7. Run label audit for the full dataset and/or segments.
8. Combine issues.
9. `ready` should be true only if there are no error-severity issues.
10. In `strict` mode, warning-severity issues may make `ready` false.
11. `training_enabled` must remain false.
12. `training_executed` must always be false.

## Task 6: Add Baseline Readiness CLI

Add:

```text
cajas/scripts/check_baseline_readiness.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--json
--strict
--write-artifacts
--output-dir tmp/cajas/baseline_readiness
--run-name phase8_baseline_readiness
```

Behavior:

- Text mode prints config name, ready yes/no, training enabled/executed, feature count, segment rows, feature audit issue count, label audit issue count.
- JSON mode prints `BaselineReadinessReport.to_dict()`.
- If `--write-artifacts`, write `baseline_readiness_report.json` under the run directory.
- If strict and warnings exist, exit non-zero if `ready` is false.
- Exit non-zero for error-severity issues.

If the `flat` class is rare, a warning is acceptable; do not force failure unless in strict mode.

## Task 7: Optional Readiness Artifact Integration

Update `cajas/scripts/run_experiment_plan_dry_run.py` only if clean and low-risk.

Optional behavior:

- Add `--include-readiness`.
- When used with `--write-artifacts`, also write `baseline_readiness_report.json`.

If this is too invasive, keep readiness artifact writing only in `check_baseline_readiness.py`.

## Task 8: Update YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add:

```yaml
readiness:
  enabled: true
  training_must_be_disabled: true
  expected_label_classes:
    - down
    - flat
    - up
  rare_class_min_count: 10
  fail_on_feature_leakage: true
  fail_on_non_numeric_features: true
  strict_warnings: false
```

Clarify:

- Readiness checks prepare for a future baseline but do not enable training.
- `flat` may be rare.
- This is not a trading readiness check.

## Task 9: Add Tests

Add:

```text
cajas/tests/test_feature_audit.py
cajas/tests/test_label_audit.py
cajas/tests/test_baseline_readiness.py
```

Tests should use temporary CSV/YAML data, not real EURUSD data.

Feature audit tests:

- leakage columns in features produce error
- non-numeric feature produces error
- all-null feature produces error
- constant feature produces warning
- clean numeric features pass

Label audit tests:

- expected classes pass
- unknown class produces error
- missing labels produce error
- rare class produces warning

Baseline readiness tests:

- valid temporary config/dataset returns ready true or ready true with warnings depending on rare labels
- training enabled config fails
- leakage column in features fails
- strict mode treats warnings as not ready if implemented

## Task 10: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 8:

- Baseline readiness gate added.
- Feature audit added.
- Label audit added.
- CLI command for readiness check.
- Optional readiness artifacts.
- No training/no trading/no Qlib core changes.

Integration notes should add Phase 8:

- Readiness gate is the final safety check before any future baseline phase.
- It is not model training.
- It checks for leakage, feature schema, label classes, and disabled training.
- Phase 9 recommendation:
  - add a training-disabled LightGBM baseline plan object, or
  - if explicitly approved later, add a controlled baseline training command that writes local artifacts but does not trade.

Data examples should add:

- Feature audit rules.
- Label audit rules.
- `future_close_8` and `future_return_8` remain audit columns, not features.

## Task 11: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/audits/feature_audit.py
./.venv-qlib313/bin/python -m py_compile cajas/audits/label_audit.py
./.venv-qlib313/bin/python -m py_compile cajas/readiness/baseline_readiness.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/check_baseline_readiness.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_experiment_plan_dry_run.py
```

Run existing dry-run commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json

./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --strict
```

Run readiness checks:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact readiness check:

```bash
rm -rf tmp/cajas/baseline_readiness/phase8_baseline_readiness

./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/baseline_readiness \
  --run-name phase8_baseline_readiness

find tmp/cajas/baseline_readiness/phase8_baseline_readiness -maxdepth 1 -type f -print | sort
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_prepared_csv_handler.py \
  cajas/tests/test_prepared_dataset.py \
  cajas/tests/test_prepared_workflow.py \
  cajas/tests/test_experiment_config.py \
  cajas/tests/test_experiment_plan_dry_run.py \
  cajas/tests/test_dry_run_recorder.py \
  cajas/tests/test_experiment_plan_artifacts.py \
  cajas/tests/test_feature_audit.py \
  cajas/tests/test_label_audit.py \
  cajas/tests/test_baseline_readiness.py
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

### Commit 1: Phase 8 prompt and recorder init fix

```bash
git add tasks/phase_008_baseline_readiness_gate_prompt.md
git add cajas/recorders/__init__.py
git add -u cajas/recorders
git commit -m "fix: use standard recorder package init"
```

If the prompt and init fix should be separate, split them.

### Commit 2: audit modules

```bash
git add cajas/audits/__init__.py \
  cajas/audits/feature_audit.py \
  cajas/audits/label_audit.py \
  cajas/tests/test_feature_audit.py \
  cajas/tests/test_label_audit.py
git commit -m "feat: add feature and label audits"
```

### Commit 3: baseline readiness gate

```bash
git add cajas/readiness/__init__.py \
  cajas/readiness/baseline_readiness.py \
  cajas/scripts/check_baseline_readiness.py \
  cajas/tests/test_baseline_readiness.py
git commit -m "feat: add baseline readiness gate"
```

### Commit 4: optional artifact integration

If `run_experiment_plan_dry_run.py` or recorder behavior changed:

```bash
git add cajas/scripts/run_experiment_plan_dry_run.py \
  cajas/recorders/dry_run_recorder.py \
  cajas/tests/test_experiment_plan_artifacts.py
git commit -m "feat: include readiness in dry run artifacts"
```

### Commit 5: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document baseline readiness gate"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 8 completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- recorder init:
- old init.py removed: yes/no/not applicable

Changed files:
- ...

Feature audit:
- path:
- errors:
- warnings:
- leakage columns found:

Label audit:
- path:
- observed classes:
- rare classes:
- errors:
- warnings:

Baseline readiness:
- path:
- ready:
- strict ready:
- training enabled:
- training executed:
- feature count:
- segments:

Artifacts:
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
