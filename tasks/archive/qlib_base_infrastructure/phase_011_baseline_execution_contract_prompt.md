# Phase 11 Prompt: Add Baseline Execution Contract and CLI Path Hygiene

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 11 prompt under `tasks/`.
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

Phase 10 completed with commits:

```text
6d78ad7b docs: add phase 10 training-guarded baseline prompt
aad8649c feat: add baseline training safety guard
01cba5b8 feat: add training-disabled baseline scaffold
e2a10d44 docs: document training-disabled baseline scaffold
```

Phase 10 added:

- `cajas/baseline/training_guard.py`
- `cajas/baseline/baseline_scaffold.py`
- `cajas/scripts/build_baseline_scaffold.py`
- training guard tests
- baseline scaffold tests
- docs/config updates

Phase 10 validation:

```text
training enabled: false
training allowed: false
training executed: false
pytest: 52 passed
```

Known issue from Phase 10 report:

Some validation command text contained typo paths like:

```text
caixas/scripts/...
caixas/tests/...
```

The final tests passed, but Phase 11 should add explicit repo path hygiene checks and documented validation commands using only `cajas/...`.

## Phase 11 Goal

Phase 11 should add a baseline execution contract that documents and validates what is allowed before any future training phase.

Main objectives:

1. Add command/path hygiene checks to catch `caixas/` typo paths in docs/tasks or generated command reports.
2. Add a baseline execution contract that explicitly separates:
   - planning
   - scaffolding
   - future training
   - forbidden trading/execution behavior
3. Add a hard preflight CLI that validates all conditions required before training could ever be enabled, while still refusing to train in Phase 11.
4. Add artifact output for the execution contract and preflight report.
5. Add tests and docs.

This phase still does not train a model.

This phase still does not build, fit, predict, evaluate, or serialize any model.

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
git check-ignore -v tasks/phase_010_training_guarded_baseline_scaffold_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.

## Task 2: Add Path Hygiene Checker

Add:

```text
cajas/quality/__init__.py
cajas/quality/path_hygiene.py
```

Purpose:

- Detect obvious typo paths in repository docs/tasks/reports before they become repeated workflow instructions.
- Specifically catch `caixas/` typo references.
- Optionally catch `taskDocs/` if it returns.
- Do not fail on generated `tmp/` because it is ignored and local.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class PathHygieneIssue:
    path: str
    line: int
    pattern: str
    message: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class PathHygieneReport:
    checked_files: int
    issues: list[PathHygieneIssue]

    @property
    def passed(self) -> bool: ...

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def check_path_hygiene(
    *,
    root: str | Path,
    include_globs: tuple[str, ...] = (
        "tasks/*.md",
        "cajas/**/*.md",
        "cajas/**/*.py",
        "cajas/**/*.yaml",
        "cajas/**/*.yml",
    ),
    forbidden_patterns: tuple[str, ...] = ("caixas/", "taskDocs/"),
) -> PathHygieneReport:
    ...
```

Rules:

- Use standard library only.
- Skip `.git/`, `.venv*`, `tmp/`, `.codex/`, `__pycache__/`.
- Report path and line number.
- Do not automatically edit files.
- Tests should use temporary files.

## Task 3: Add Path Hygiene CLI

Add:

```text
cajas/scripts/check_path_hygiene.py
```

CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Optional flags:

```text
--root .
--json
--allow-taskdocs
```

Behavior:

- Text output:
  - checked files
  - issue count
  - each issue path:line pattern message
- JSON output prints `PathHygieneReport.to_dict()`.
- Exit non-zero if issues are found.
- If `--allow-taskdocs`, do not treat `taskDocs/` as forbidden, but still catch `caixas/`.

After implementing, run it. If it finds typo paths inside previous task prompts or docs, fix those files if appropriate. Do not rewrite old prompt history unless the typo creates active validation confusion. It is acceptable to fix typo paths in tracked task prompts if they are known mistakes.

## Task 4: Add Baseline Execution Contract

Add:

```text
cajas/baseline/execution_contract.py
```

Purpose:

- Represent allowed and forbidden actions for future baseline phases.
- Make training gates explicit and machine-checkable.
- Keep Phase 11 training disabled.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class ExecutionPermission:
    name: str
    allowed: bool
    reason: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class BaselineExecutionContract:
    phase: str
    config_name: str
    model_family: str
    target_label: str
    permissions: list[ExecutionPermission]
    required_before_training: list[str]
    forbidden_actions: list[str]

    def to_dict(self) -> dict: ...

    def permission_map(self) -> dict[str, bool]: ...
```

Suggested function:

```python
def build_phase11_execution_contract(
    *,
    config_path: str,
    model_family: str = "LightGBM",
) -> BaselineExecutionContract:
    ...
```

Required permissions in Phase 11:

```text
load_config: allowed
validate_dataset: allowed
run_readiness_check: allowed
build_plan: allowed
build_scaffold: allowed
probe_dependencies: allowed
write_local_artifacts: allowed

build_model: not allowed
fit_model: not allowed
predict: not allowed
evaluate_model: not allowed
serialize_model: not allowed
backtest: not allowed
trade: not allowed
submit_orders: not allowed
```

Required before training list should include:

- explicit future phase approval
- `training.enabled: true` in config
- phase policy allows training
- strict readiness warnings reviewed or accepted
- label encoding finalized
- baseline metrics finalized
- artifact output location confirmed
- no Qlib core modifications required

Forbidden actions should include:

- live trading
- order submission
- position sizing
- profit claims
- backtest optimization

## Task 5: Add Baseline Preflight Gate

Add:

```text
cajas/baseline/baseline_preflight.py
```

Purpose:

- Combine:
  - experiment config
  - readiness
  - baseline plan
  - baseline scaffold
  - dependency probe
  - execution contract
  - path hygiene
- Produce a single preflight report for a future training phase.
- Still refuse training in Phase 11.

Suggested dataclass:

```python
@dataclass(frozen=True)
class BaselinePreflightReport:
    config_name: str
    phase: str
    can_train_now: bool
    training_enabled: bool
    phase_policy_allows_training: bool
    training_executed: bool
    readiness_ready: bool
    strict_readiness_ready: bool
    path_hygiene_passed: bool
    execution_contract: dict
    baseline_plan: dict
    baseline_scaffold: dict
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_baseline_preflight(
    *,
    config_path: str,
    root: str | Path = ".",
    input_override: str | None = None,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselinePreflightReport:
    ...
```

Behavior:

- `can_train_now` must be false in Phase 11.
- `training_executed` must always be false.
- If path hygiene fails, include blockers.
- If strict readiness fails, include warning or blocker depending on current policy. Use warning by default.
- Include the execution contract.
- Do not import LightGBM.
- Do not construct or fit models.

## Task 6: Add Baseline Preflight CLI

Add:

```text
cajas/scripts/run_baseline_preflight.py
```

CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--root .
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--model-family LightGBM
--json
--write-artifacts
--output-dir tmp/cajas/baseline_preflight
--run-name phase11_baseline_preflight
```

Behavior:

- Text mode prints:
  - config name
  - phase
  - can_train_now false
  - training enabled false
  - phase policy allows training false
  - training executed false
  - readiness status
  - path hygiene status
  - permissions summary
  - blockers
  - warnings
- JSON mode prints `BaselinePreflightReport.to_dict()`.
- If `--write-artifacts`, write:
  - `baseline_preflight_report.json`
  - `baseline_execution_contract.json`
- Exit zero if `can_train_now` is false only because Phase 11 policy disables training.
- Exit non-zero for config/data/path hygiene errors.

## Task 7: Update YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
baseline_preflight:
  enabled: true
  phase: phase11
  phase_policy_allows_training: false
  can_train_now: false
  training_executed: false
  path_hygiene:
    forbidden_patterns:
      - caixas/
      - taskDocs/
  artifacts:
    default_output_dir: tmp/cajas/baseline_preflight
    default_run_name: phase11_baseline_preflight
    generated_files:
      - baseline_preflight_report.json
      - baseline_execution_contract.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is preflight only.
- It does not train.
- It does not allow trading.
- It does not make Qlib core changes.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_path_hygiene.py
cajas/tests/test_execution_contract.py
cajas/tests/test_baseline_preflight.py
```

Update if needed:

```text
cajas/tests/test_baseline_scaffold.py
```

Tests should use temporary CSV/YAML data where data is needed.

Path hygiene tests:

- clean files pass
- `caixas/` typo is detected
- ignored directories are skipped
- JSON dict shape is stable

Execution contract tests:

- allowed permissions are allowed
- forbidden model/trading permissions are false
- required_before_training contains explicit future phase approval
- permission_map works

Baseline preflight tests:

- `can_train_now` false in Phase 11
- `training_executed` false
- path hygiene blocker appears when typo exists
- clean path hygiene passes
- artifact writing creates both files
- JSON serialization works

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 11:

- Path hygiene checker added.
- Baseline execution contract added.
- Baseline preflight added.
- CLI commands:
  - `check_path_hygiene.py`
  - `run_baseline_preflight.py`
- Training still disabled.
- No Qlib core changes/no trading.

Integration notes should add Phase 11:

- Baseline preflight consolidates config/readiness/plan/scaffold/path hygiene.
- Execution contract separates allowed planning actions from forbidden training/trading actions.
- Phase 12 recommendation:
  - add an explicitly disabled training command skeleton with no model fit, or
  - if user explicitly approves, start controlled baseline training in a later phase with artifacts only and no trading.

Data examples should add:

- Preflight reports do not contain raw rows.
- Path hygiene protects project command accuracy.
- Prepared CSV labels remain strings.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/quality/path_hygiene.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/execution_contract.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_preflight.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_baseline_preflight.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Run existing commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run preflight:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact preflight:

```bash
rm -rf tmp/cajas/baseline_preflight/phase11_baseline_preflight

./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/baseline_preflight \
  --run-name phase11_baseline_preflight

find tmp/cajas/baseline_preflight/phase11_baseline_preflight -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_baseline_scaffold.py \
  cajas/tests/test_path_hygiene.py \
  cajas/tests/test_execution_contract.py \
  cajas/tests/test_baseline_preflight.py
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

### Commit 1: Phase 11 prompt

```bash
git add tasks/phase_011_baseline_execution_contract_prompt.md
git commit -m "docs: add phase 11 baseline execution contract prompt"
```

### Commit 2: path hygiene

```bash
git add cajas/quality/__init__.py \
  cajas/quality/path_hygiene.py \
  cajas/scripts/check_path_hygiene.py \
  cajas/tests/test_path_hygiene.py
git commit -m "feat: add path hygiene checks"
```

### Commit 3: execution contract

```bash
git add cajas/baseline/execution_contract.py \
  cajas/tests/test_execution_contract.py
git commit -m "feat: add baseline execution contract"
```

### Commit 4: baseline preflight

```bash
git add cajas/baseline/baseline_preflight.py \
  cajas/scripts/run_baseline_preflight.py \
  cajas/tests/test_baseline_preflight.py \
  cajas/baseline/__init__.py
git commit -m "feat: add baseline preflight gate"
```

### Commit 5: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document baseline preflight workflow"
```

Then:

```bash
git push
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly:

```text
Phase 11 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Path hygiene:
- path:
- checked files:
- issues:
- status:

Execution contract:
- path:
- allowed actions:
- forbidden actions:
- can build model:
- can fit model:
- can trade:

Baseline preflight:
- path:
- can_train_now:
- training enabled:
- phase policy allows training:
- training executed:
- readiness:
- strict readiness:
- path hygiene:
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
