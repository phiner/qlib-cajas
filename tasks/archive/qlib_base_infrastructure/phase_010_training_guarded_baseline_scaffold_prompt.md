# Phase 10 Prompt: Fix Baseline Package Init and Add Training-Guarded Baseline Scaffold

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 10 prompt under `tasks/`.
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

Phase 9 completed with commits:

```text
144b5a87 docs: add phase 9 training-disabled baseline prompt
c4427c1f feat: add baseline dependency and missing value audit details
c7b897bb feat: add training-disabled baseline plan
2e378a5b docs: document training-disabled baseline plan
```

Phase 9 added:

- `cajas/environment/dependency_probe.py`
- `cajas/baseline/baseline_plan.py`
- `cajas/scripts/build_baseline_plan.py`
- dependency probe tests
- baseline plan tests
- docs/config updates

Phase 9 validation:

```text
dependency probe: pandas/yaml/sklearn/lightgbm available
baseline plan ready non-strict: yes
baseline plan ready strict: no
training enabled: false
training allowed: false
training executed: false
pytest: 46 passed
```

Known issue from Phase 9 report:

The package init files were reported as:

```text
cajas/environment/init.py
cajas/baseline/init.py
```

These should be:

```text
cajas/environment/__init__.py
cajas/baseline/__init__.py
```

## Phase 10 Goal

Phase 10 should add a training-guarded baseline scaffold, but keep training disabled by default and do not execute any model fitting.

Main objectives:

1. Fix `cajas/environment/init.py` and `cajas/baseline/init.py` to standard `__init__.py`.
2. Add a baseline training scaffold with a hard safety guard.
3. Add a CLI that validates all prerequisites and exits before training unless an explicit future flag/config enables it.
4. Add a baseline design/spec artifact describing what would be trained later.
5. Add tests proving training cannot run while disabled.
6. Update docs/config.

This phase must still do no training.

This phase must still do no model construction, fit, predict, evaluation, or serialization.

This phase must still do no trading, backtesting, profit analysis, live execution, automatic ordering, or position sizing.

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
10. Do not build, fit, predict, evaluate, or serialize any model.
11. Do not run backtest/profit/return analysis.
12. Do not add trading strategy, live execution, auto order, or position sizing logic.
13. Do not install new runtime dependencies automatically.
14. Do not enable training in YAML.
15. Do not claim a config is fully Qlib-runnable unless it has actually been run successfully.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_009_training_disabled_baseline_plan_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.

## Task 2: Fix Environment and Baseline Package Init Files

Inspect:

```bash
find cajas/environment cajas/baseline -maxdepth 1 -type f -print | sort
```

If these exist:

```text
cajas/environment/init.py
cajas/baseline/init.py
```

rename them with Git:

```bash
git mv cajas/environment/init.py cajas/environment/__init__.py
git mv cajas/baseline/init.py cajas/baseline/__init__.py
```

If destination files already exist, inspect both and preserve useful exports/comments.

Recommended `cajas/environment/__init__.py` content:

```python
from .dependency_probe import DependencyProbeReport, DependencyStatus, probe_dependencies

__all__ = ["DependencyProbeReport", "DependencyStatus", "probe_dependencies"]
```

Recommended `cajas/baseline/__init__.py` content:

```python
from .baseline_plan import BaselineModelSpec, BaselinePlanReport, build_baseline_plan

__all__ = ["BaselineModelSpec", "BaselinePlanReport", "build_baseline_plan"]
```

After adding the scaffold in later tasks, update `cajas/baseline/__init__.py` to export the new scaffold objects too.

Verify imports:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.environment import probe_dependencies
from cajas.baseline import build_baseline_plan
print(probe_dependencies.__name__, build_baseline_plan.__name__)
PY
```

## Task 3: Add Baseline Training Safety Guard

Add:

```text
cajas/baseline/training_guard.py
```

Purpose:

- Centralize the policy that baseline training is disabled unless explicitly allowed in a later phase.
- Make accidental training impossible through the Phase 10 CLI.

Suggested dataclasses/exceptions:

```python
class TrainingDisabledError(RuntimeError):
    pass

@dataclass(frozen=True)
class TrainingGuardResult:
    allowed: bool
    reason: str
    config_training_enabled: bool
    phase_policy_allows_training: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def assert_baseline_training_allowed(
    *,
    config_training_enabled: bool,
    phase_policy_allows_training: bool = False,
) -> TrainingGuardResult:
    ...
```

Behavior:

- If `config_training_enabled` is false, raise `TrainingDisabledError`.
- If `phase_policy_allows_training` is false, raise `TrainingDisabledError`.
- In Phase 10, default `phase_policy_allows_training` must always be false.
- If both are true in a later phase, return `TrainingGuardResult(allowed=True, ...)`.
- Do not train anything.

Tests must prove the guard raises when:
- config training is false
- phase policy is false
- both are false

## Task 4: Add Baseline Scaffold

Add:

```text
cajas/baseline/baseline_scaffold.py
```

Purpose:

- Represent a future baseline training pipeline shape without constructing or fitting a model.
- Convert existing baseline plan/readiness information into a training-disabled scaffold report.
- Make the next phase easier while preserving hard safety.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BaselineDatasetSpec:
    feature_count: int
    label_col: str
    segments: dict[str, dict[str, int]]
    leakage_columns_in_features: bool

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class BaselineTrainingScaffoldReport:
    config_name: str
    model_family: str
    task_type: str
    target_label: str
    dataset_spec: BaselineDatasetSpec
    dependency_probe: dict
    readiness: dict
    training_guard: dict
    training_enabled: bool
    training_allowed: bool
    training_executed: bool
    next_steps: list[str]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_training_disabled_baseline_scaffold(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselineTrainingScaffoldReport:
    ...
```

Behavior:

1. Build the Phase 9 baseline plan.
2. Run the training guard.
3. Catch `TrainingDisabledError` and include it as a blocker.
4. Build a dataset spec from plan/readiness summary.
5. Set:
   - `training_enabled: false`
   - `training_allowed: false`
   - `training_executed: false`
6. Add next steps such as:
   - resolve strict readiness warnings
   - decide label encoding strategy
   - decide baseline metrics for classification
   - add explicit training enable flag in a future phase
7. Do not import LightGBM.
8. Do not instantiate any model.
9. Do not fit/predict/evaluate/serialize anything.

## Task 5: Add Baseline Scaffold CLI

Add:

```text
cajas/scripts/build_baseline_scaffold.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--model-family LightGBM
--json
--write-artifacts
--output-dir tmp/cajas/baseline_scaffolds
--run-name phase10_baseline_scaffold
```

Behavior:

- Text mode prints:
  - config name
  - model family
  - task type
  - target label
  - feature count
  - train/valid/test rows
  - training enabled false
  - training allowed false
  - training executed false
  - blockers
  - warnings
  - next steps
- JSON mode prints `BaselineTrainingScaffoldReport.to_dict()`.
- If `--write-artifacts`, write:
  - `baseline_scaffold_report.json`
- Exit zero if the only blocker is "training disabled by phase policy" because this is expected in Phase 10.
- Exit non-zero for data/config errors such as leakage, missing config, or invalid dataset.

Example text output:

```text
Baseline scaffold completed.
config: fx_eurusd_15m_lightgbm_future_direction_8
model family: LightGBM
task type: multiclass_classification
target label: future_direction_8
feature count: 24
training enabled: false
training allowed: false
training executed: false
expected blocker:
  - Training remains disabled by Phase 10 policy.
```

## Task 6: Add Label Encoding Plan

Add a lightweight, non-executable label encoding plan.

Option A: integrate into `cajas/baseline/baseline_scaffold.py`.

Option B: add:

```text
cajas/baseline/label_encoding_plan.py
```

Preferred labels:

```text
down
flat
up
```

Suggested mapping for future baseline only:

```python
{"down": 0, "flat": 1, "up": 2}
```

Rules:

- Do not transform the actual dataset in Phase 10.
- Do not write encoded labels into CSV.
- Do not train.
- Include the mapping only as a plan/spec.
- Document that this is for future multiclass classification, not a trading action.

## Task 7: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
baseline_scaffold:
  enabled: true
  training_allowed: false
  training_executed: false
  model_family: LightGBM
  task_type: multiclass_classification
  label_encoding_plan:
    down: 0
    flat: 1
    up: 2
  artifacts:
    default_output_dir: tmp/cajas/baseline_scaffolds
    default_run_name: phase10_baseline_scaffold
    generated_files:
      - baseline_scaffold_report.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is a scaffold only.
- No model is built.
- No label transformation is executed.
- No trading signal is produced.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_training_guard.py
cajas/tests/test_baseline_scaffold.py
```

Update if needed:

```text
cajas/tests/test_baseline_plan.py
```

Tests should use temporary CSV/YAML data, not real EURUSD data.

Training guard tests:

- config disabled raises
- phase policy disabled raises
- both disabled raises
- both enabled returns allowed result, but do not use this path to train

Baseline scaffold tests:

- returns `training_executed: false`
- returns `training_allowed: false`
- includes training-disabled blocker
- includes dataset spec
- includes label encoding plan if implemented
- JSON serialization works
- artifact writing creates `baseline_scaffold_report.json`
- no model object is constructed

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 10:

- Baseline scaffold added.
- Training guard added.
- CLI command for scaffold.
- Artifact output.
- Label encoding plan.
- Training still disabled.
- No Qlib core changes/no trading.

Integration notes should add Phase 10:

- The project now has a baseline plan and baseline scaffold.
- The scaffold is a safety wrapper, not training.
- Phase 11 recommendation:
  - add a controlled baseline training command with training still disabled by default and explicit safety flags, or
  - first add a Qlib DatasetH compatibility probe if that is preferred.
- Actual training remains disabled until explicitly enabled in a later phase.

Data examples should add:

- Label encoding plan is not applied to data in Phase 10.
- Prepared CSV labels remain strings.
- Scaffold artifacts do not contain raw rows.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/environment/dependency_probe.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_plan.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/training_guard.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_scaffold.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/build_baseline_plan.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/build_baseline_scaffold.py
```

Run existing commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new scaffold commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact scaffold:

```bash
rm -rf tmp/cajas/baseline_scaffolds/phase10_baseline_scaffold

./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/baseline_scaffolds \
  --run-name phase10_baseline_scaffold

find tmp/cajas/baseline_scaffolds/phase10_baseline_scaffold -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_baseline_plan.py \
  cajas/tests/test_training_guard.py \
  cajas/tests/test_baseline_scaffold.py
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

### Commit 1: Phase 10 prompt and package init fixes

```bash
git add tasks/phase_010_training_guarded_baseline_scaffold_prompt.md
git add cajas/environment/__init__.py cajas/baseline/__init__.py
git add -u cajas/environment cajas/baseline
git commit -m "fix: use standard environment and baseline package init"
```

If prompt and init fix should be separate, split them.

### Commit 2: training guard

```bash
git add cajas/baseline/training_guard.py cajas/tests/test_training_guard.py
git commit -m "feat: add baseline training safety guard"
```

### Commit 3: baseline scaffold

```bash
git add cajas/baseline/baseline_scaffold.py \
  cajas/scripts/build_baseline_scaffold.py \
  cajas/tests/test_baseline_scaffold.py
git commit -m "feat: add training-disabled baseline scaffold"
```

If label encoding plan is a separate module:

```bash
git add cajas/baseline/label_encoding_plan.py
```

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document training-disabled baseline scaffold"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 10 completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- environment init:
- baseline init:
- old init.py removed: yes/no/not applicable

Changed files:
- ...

Training guard:
- path:
- config disabled behavior:
- phase policy disabled behavior:
- training executed:

Baseline scaffold:
- path:
- model family:
- task type:
- target label:
- feature count:
- label encoding plan:
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
- Build/fit/predict/evaluate/serialize any model.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
