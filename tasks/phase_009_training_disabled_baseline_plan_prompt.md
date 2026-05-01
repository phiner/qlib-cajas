# Phase 9 Prompt: Fix Audit/Readiness Init and Add Training-Disabled Baseline Plan

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 9 prompt under `tasks/`.
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

Phase 8 completed with commits:

```text
1a001a14 docs: add phase 8 baseline readiness prompt
ee88943d feat: add feature and label audits
f5b70242 feat: add baseline readiness gate
b377a5e2 docs: document baseline readiness gate
```

Phase 8 added:

- `cajas/audits/feature_audit.py`
- `cajas/audits/label_audit.py`
- `cajas/readiness/baseline_readiness.py`
- `cajas/scripts/check_baseline_readiness.py`
- tests for feature audit, label audit, and readiness
- docs/config updates

Phase 8 validation:

```text
baseline readiness non-strict: ready true
baseline readiness strict: false due warning-level missing feature values
training enabled: false
training executed: false
pytest: 40 passed
```

Known issue from Phase 8 report:

The package init files were reported as:

```text
cajas/audits/init.py
cajas/readiness/init.py
```

These should be:

```text
cajas/audits/__init__.py
cajas/readiness/__init__.py
```

Also note: the Phase 8 reported pytest command text had typo paths like `caixas/tests/...`, but final result was 40 passed. In Phase 9, run the correct `cajas/tests/...` paths.

## Phase 9 Goal

Phase 9 should prepare a future baseline training phase without enabling training.

Main objectives:

1. Fix audit/readiness package init file names.
2. Add a training-disabled baseline plan object.
3. Add a dependency probe for optional future baseline tools such as `lightgbm` and `sklearn`.
4. Add missing-value audit details so the strict readiness warning is easier to understand.
5. Add a baseline plan CLI that reports what would be trained later, without training anything.
6. Extend local artifacts with a baseline plan report.
7. Add tests and docs.

This phase still does not train a model.

This phase still does not modify Qlib core.

This phase still does not introduce trading, backtesting, profit analysis, live execution, automatic ordering, or position sizing.

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
10. Do not fit, predict, evaluate, or serialize any model.
11. Do not run backtest/profit/return analysis.
12. Do not add trading strategy, live execution, auto order, or position sizing logic.
13. Do not install new runtime dependencies automatically.
14. Do not claim a config is fully Qlib-runnable unless it has actually been run successfully.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_008_baseline_readiness_gate_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.

## Task 2: Fix Audit and Readiness Package Init Files

Inspect:

```bash
find cajas/audits cajas/readiness -maxdepth 1 -type f -print | sort
```

If these exist:

```text
cajas/audits/init.py
cajas/readiness/init.py
```

rename them with Git:

```bash
git mv cajas/audits/init.py cajas/audits/__init__.py
git mv cajas/readiness/init.py cajas/readiness/__init__.py
```

If destination files already exist, inspect both and preserve useful exports/comments.

Recommended `cajas/audits/__init__.py` content:

```python
from .feature_audit import FeatureAuditIssue, FeatureAuditReport, audit_features
from .label_audit import LabelAuditIssue, LabelAuditReport, audit_labels

__all__ = [
    "FeatureAuditIssue",
    "FeatureAuditReport",
    "LabelAuditIssue",
    "LabelAuditReport",
    "audit_features",
    "audit_labels",
]
```

Recommended `cajas/readiness/__init__.py` content:

```python
from .baseline_readiness import BaselineReadinessReport, run_baseline_readiness_check

__all__ = ["BaselineReadinessReport", "run_baseline_readiness_check"]
```

Verify imports:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.audits import audit_features, audit_labels
from cajas.readiness import run_baseline_readiness_check
print(audit_features.__name__, audit_labels.__name__, run_baseline_readiness_check.__name__)
PY
```

## Task 3: Improve Missing-Value Audit Details

Update:

```text
cajas/audits/feature_audit.py
```

Current strict readiness is false due warning-level missing feature values. Make this more actionable.

Enhance `FeatureAuditReport` if needed with:

```python
missing_value_ratios: dict[str, float]
top_missing_features: list[dict[str, object]]
```

Suggested rules:

- Keep existing `missing_value_counts`.
- Add ratios relative to row count.
- Add top N missing features, default 10.
- Missing values remain warnings unless the whole column is null.
- Do not mutate input DataFrame.
- Preserve backwards compatibility where practical.

Add tests for:

- missing count and ratio
- top missing features sorted by missing count descending
- no missing features produces empty top list

## Task 4: Add Dependency Probe

Add:

```text
cajas/environment/__init__.py
cajas/environment/dependency_probe.py
```

Purpose:

- Probe optional dependencies for future baseline training.
- Do not install anything.
- Do not fail the project if optional future dependencies are missing.
- Return structured availability information.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class DependencyStatus:
    name: str
    available: bool
    version: str | None
    import_error: str | None

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class DependencyProbeReport:
    dependencies: list[DependencyStatus]

    def to_dict(self) -> dict: ...

    @property
    def missing(self) -> list[str]: ...
```

Suggested function:

```python
def probe_dependencies(names: tuple[str, ...] = ("pandas", "yaml", "sklearn", "lightgbm")) -> DependencyProbeReport: ...
```

Rules:

- Use `importlib.import_module`.
- Use `getattr(module, "__version__", None)` when available.
- Do not import heavy modules more than necessary.
- Do not install packages.
- Missing `lightgbm` or `sklearn` should be reported as "missing optional future baseline dependency", not a Phase 9 failure.
- `pandas` and `yaml` should normally be available in the current project venv. If missing, report clearly.

Add tests with fake module names and known modules where practical.

## Task 5: Add Training-Disabled Baseline Plan

Add:

```text
cajas/baseline/__init__.py
cajas/baseline/baseline_plan.py
```

Purpose:

- Create a plan/spec for a future baseline model run.
- Keep training disabled.
- Combine config, readiness, dependency probe, and workflow summary.
- Make explicit what would be required before a later baseline training phase.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BaselineModelSpec:
    model_family: str
    target_label: str
    task_type: str
    enabled: bool
    training_allowed: bool

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class BaselinePlanReport:
    config_name: str
    ready_non_strict: bool
    ready_strict: bool
    training_enabled: bool
    training_allowed: bool
    training_executed: bool
    model_spec: BaselineModelSpec
    dependency_probe: dict
    readiness_report: dict
    required_next_steps: list[str]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_baseline_plan(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    strict: bool = False,
) -> BaselinePlanReport: ...
```

Behavior:

1. Load config.
2. Run non-strict readiness.
3. Run strict readiness.
4. Probe dependencies.
5. Build model spec with:
   - `model_family: LightGBM`
   - `target_label: future_direction_8`
   - `task_type: multiclass_classification`
   - `enabled: false`
   - `training_allowed: false`
6. `training_enabled` must be false.
7. `training_allowed` must be false in Phase 9.
8. `training_executed` must always be false.
9. Add blockers/warnings:
   - strict readiness false
   - optional missing dependencies
   - training disabled by phase policy
   - config not fully Qlib-runnable if applicable
10. No model construction, fit, predict, evaluation, or serialization.

## Task 6: Add Baseline Plan CLI

Add:

```text
cajas/scripts/build_baseline_plan.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--model-family LightGBM
--json
--strict
--write-artifacts
--output-dir tmp/cajas/baseline_plans
--run-name phase9_baseline_plan
```

Behavior:

- Text mode prints:
  - config name
  - model family
  - target label
  - task type
  - ready non-strict
  - ready strict
  - training enabled false
  - training allowed false
  - training executed false
  - dependency probe summary
  - blockers
  - warnings
- JSON mode prints `BaselinePlanReport.to_dict()`.
- If `--write-artifacts`, write:
  - `baseline_plan_report.json`
- Use local output directory under `tmp/` only.

Example text output:

```text
Baseline plan completed.
config: fx_eurusd_15m_lightgbm_future_direction_8
model family: LightGBM
target label: future_direction_8
task type: multiclass_classification
ready non-strict: yes
ready strict: no
training enabled: false
training allowed: false
training executed: false
blockers:
  - Training remains disabled by Phase 9 policy.
warnings:
  - Strict readiness is false due warning-level issues.
```

## Task 7: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
baseline_plan:
  enabled: true
  model_family: LightGBM
  task_type: multiclass_classification
  target_label: future_direction_8
  training_allowed: false
  training_executed: false
  required_optional_dependencies:
    - sklearn
    - lightgbm
  artifacts:
    default_output_dir: tmp/cajas/baseline_plans
    default_run_name: phase9_baseline_plan
    generated_files:
      - baseline_plan_report.json
```

Keep training disabled:

```yaml
training:
  enabled: false
```

Clarify:

- Baseline plan prepares for a future phase only.
- No training is enabled in Phase 9.
- No trading signal is produced.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_dependency_probe.py
cajas/tests/test_baseline_plan.py
```

Update:

```text
cajas/tests/test_feature_audit.py
```

Tests should cover:

### Feature audit enhancements

- missing value ratios
- top missing features
- sorted missing feature summary

### Dependency probe

- known module available
- fake module missing
- report serializes to dict
- missing list works

### Baseline plan

- plan reports training_allowed false
- plan reports training_executed false
- plan includes readiness report
- plan includes dependency probe
- JSON serialization works
- artifact writing creates `baseline_plan_report.json`
- strict false readiness becomes warning/blocker, not training

Use temporary CSV/YAML data.

Do not require `lightgbm` or `sklearn` to be installed for tests.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 9:

- Baseline plan added.
- Dependency probe added.
- Missing-value audit improved.
- CLI commands:
  - `check_baseline_readiness.py`
  - `build_baseline_plan.py`
- Training still disabled.
- No Qlib core changes/no trading.

Integration notes should add Phase 9:

- Baseline plan is a planning artifact only.
- It documents blockers and dependencies before future baseline training.
- It still does not train.
- Phase 10 recommendation:
  - add a controlled baseline training scaffold with `training.enabled` still false by default, or
  - implement a real Qlib DatasetH compatibility probe before enabling training.

Data examples should add:

- Missing-value audit details.
- Baseline plan artifacts do not contain raw rows.
- Dependency probe is environment-only and does not install packages.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/audits/feature_audit.py
./.venv-qlib313/bin/python -m py_compile cajas/audits/label_audit.py
./.venv-qlib313/bin/python -m py_compile cajas/environment/dependency_probe.py
./.venv-qlib313/bin/python -m py_compile cajas/readiness/baseline_readiness.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_plan.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/check_baseline_readiness.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/build_baseline_plan.py
```

Run existing readiness checks:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run baseline plan:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact baseline plan:

```bash
rm -rf tmp/cajas/baseline_plans/phase9_baseline_plan

./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/baseline_plans \
  --run-name phase9_baseline_plan

find tmp/cajas/baseline_plans/phase9_baseline_plan -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_baseline_readiness.py \
  cajas/tests/test_dependency_probe.py \
  cajas/tests/test_baseline_plan.py
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

### Commit 1: Phase 9 prompt and package init fixes

```bash
git add tasks/phase_009_training_disabled_baseline_plan_prompt.md
git add cajas/audits/__init__.py cajas/readiness/__init__.py
git add -u cajas/audits cajas/readiness
git commit -m "fix: use standard audit and readiness package init"
```

If prompt and init fix should be separate, split them.

### Commit 2: audit enhancements and dependency probe

```bash
git add cajas/audits/feature_audit.py \
  cajas/environment/__init__.py \
  cajas/environment/dependency_probe.py \
  cajas/tests/test_feature_audit.py \
  cajas/tests/test_dependency_probe.py
git commit -m "feat: add baseline dependency and missing value audit details"
```

### Commit 3: baseline plan

```bash
git add cajas/baseline/__init__.py \
  cajas/baseline/baseline_plan.py \
  cajas/scripts/build_baseline_plan.py \
  cajas/tests/test_baseline_plan.py
git commit -m "feat: add training-disabled baseline plan"
```

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document training-disabled baseline plan"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 9 completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- audits init:
- readiness init:
- old init.py removed: yes/no/not applicable

Changed files:
- ...

Feature audit enhancements:
- missing ratios:
- top missing features:
- strict readiness impact:

Dependency probe:
- path:
- pandas:
- yaml:
- sklearn:
- lightgbm:

Baseline plan:
- path:
- model family:
- task type:
- target label:
- ready non-strict:
- ready strict:
- training enabled:
- training allowed:
- training executed:
- blockers:
- warnings:

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
- Fit/predict/evaluate/serialize any model.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
