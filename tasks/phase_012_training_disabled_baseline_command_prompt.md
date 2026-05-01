# Phase 12 Prompt: Add Training-Disabled Baseline Command Skeleton and Manual Push Policy

## Codex Communication Rules

- Communicate with the user in English only.
- All progress updates, questions, command summaries, and completion reports must be written in English.
- Do not use Chinese in Codex-facing interaction unless the user explicitly asks.
- Do not run `git push`.
- Stop after local commits and report the exact `git push` command for the user to run manually.

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 12 prompt under `tasks/`.
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

Phase 11 completed with local commits and push done previously by Codex, but from now on Codex must not push.

Phase 11 added:

- `cajas/quality/path_hygiene.py`
- `cajas/scripts/check_path_hygiene.py`
- `cajas/baseline/execution_contract.py`
- `cajas/baseline/baseline_preflight.py`
- `cajas/scripts/run_baseline_preflight.py`
- path hygiene tests
- execution contract tests
- baseline preflight tests
- docs/config updates

Phase 11 validation:

```text
path hygiene: pass
baseline preflight: can_train_now false
training enabled: false
phase policy allows training: false
training executed: false
pytest: 61 passed
```

Known issue pattern:

Previous reports sometimes included typo paths like `caixas/tests/...` in copied command logs even when tests passed. Phase 12 must keep commands and docs using only `cajas/...`.

## Phase 12 Goal

Phase 12 should add a training-disabled baseline command skeleton that defines the future training entry point but hard-stops before model construction or fitting.

Main objectives:

1. Update persistent agent rules so Codex speaks English only and never runs `git push`.
2. Add a baseline training command skeleton that performs all preflight checks but refuses to train.
3. Add a future training configuration contract with double safety gates.
4. Add a baseline run artifact schema for future training, but write only a blocked-training report in Phase 12.
5. Add CLI tests proving the command cannot train while disabled.
6. Add docs/config updates.

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
15. Do not run `git push`.
16. Do not claim a config is fully Qlib-runnable unless it has actually been run successfully.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_011_baseline_execution_contract_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.

## Task 2: Update AGENTS.md

Update:

```text
AGENTS.md
```

Add or update a clear section:

```markdown
## Codex Communication and Push Policy

- Codex must communicate with the user in English only.
- Codex must not use Chinese in progress updates, questions, or completion reports unless explicitly requested.
- Codex must not run `git push`.
- Codex may create local commits after validation.
- After local commits, Codex must stop and report:
  - commit hashes
  - `git status --short`
  - exact `git push` command for the user to run manually.
```

Preserve existing project rules.

## Task 3: Add Baseline Run Contract

Add:

```text
cajas/baseline/run_contract.py
```

Purpose:

- Define the future baseline run contract, but keep execution blocked.
- Make explicit which steps are allowed in Phase 12 and which remain forbidden.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BaselineRunStep:
    name: str
    allowed: bool
    executed: bool
    reason: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class BaselineRunContract:
    config_name: str
    phase: str
    model_family: str
    target_label: str
    training_enabled: bool
    phase_policy_allows_training: bool
    can_train: bool
    steps: list[BaselineRunStep]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...

    def step_map(self) -> dict[str, bool]: ...
```

Suggested function:

```python
def build_phase12_baseline_run_contract(
    *,
    config_path: str,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselineRunContract:
    ...
```

Required step names:

```text
load_config
validate_config
run_preflight
build_dataset
encode_labels
build_model
fit_model
predict
evaluate
serialize_model
write_artifacts
```

Phase 12 expected behavior:

- Allowed:
  - load_config
  - validate_config
  - run_preflight
  - build_dataset metadata only
  - encode_labels plan only
  - write blocked-training artifacts
- Not allowed:
  - build_model
  - fit_model
  - predict
  - evaluate
  - serialize_model
- `executed` must be false for model/training/evaluation steps.
- `can_train` must be false.

## Task 4: Add Training-Disabled Baseline Runner

Add:

```text
cajas/baseline/baseline_runner.py
```

Purpose:

- Provide the future baseline training entry point.
- In Phase 12, it must stop before any model construction or training.
- It should return a structured blocked-run report.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BaselineBlockedRunReport:
    config_name: str
    phase: str
    model_family: str
    target_label: str
    training_enabled: bool
    phase_policy_allows_training: bool
    can_train: bool
    training_executed: bool
    model_built: bool
    predictions_generated: bool
    evaluation_executed: bool
    serialized_model: bool
    run_contract: dict
    preflight_report: dict
    blockers: list[str]
    warnings: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_training_disabled_baseline(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselineBlockedRunReport:
    ...
```

Behavior:

1. Build baseline preflight report.
2. Build Phase 12 run contract.
3. Verify config `training.enabled` is false.
4. Verify `phase_policy_allows_training` is false.
5. Return a blocked-run report.
6. Set:
   - `can_train: false`
   - `training_executed: false`
   - `model_built: false`
   - `predictions_generated: false`
   - `evaluation_executed: false`
   - `serialized_model: false`
7. Do not import LightGBM.
8. Do not instantiate any model.
9. Do not call fit/predict/evaluate.
10. Do not write model files.

## Task 5: Add Baseline Runner CLI

Add:

```text
cajas/scripts/run_baseline_disabled.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--model-family LightGBM
--json
--write-artifacts
--output-dir tmp/cajas/baseline_disabled_runs
--run-name phase12_baseline_disabled
```

Behavior:

- Text mode prints:
  - config name
  - phase
  - model family
  - target label
  - can_train false
  - training enabled false
  - phase policy allows training false
  - training executed false
  - model built false
  - predictions generated false
  - evaluation executed false
  - serialized model false
  - blockers
  - next steps
- JSON mode prints `BaselineBlockedRunReport.to_dict()`.
- If `--write-artifacts`, write:
  - `baseline_blocked_run_report.json`
  - `baseline_run_contract.json`
- Exit zero if the baseline is blocked only because training is disabled by Phase 12 policy.
- Exit non-zero for config/data/path hygiene failures.

## Task 6: Add Artifact Writer Helper for Baseline Reports

If useful, add:

```text
cajas/baseline/baseline_artifacts.py
```

Purpose:

- Reuse a simple local JSON writer for baseline plan/scaffold/preflight/blocked-run artifacts.
- Do not over-engineer.
- Do not replace existing recorders unless the change is small and safe.

Suggested function:

```python
def write_baseline_report_artifacts(
    *,
    output_dir: str | Path,
    run_name: str,
    reports: dict[str, Mapping[str, object]],
) -> dict[str, str]:
    ...
```

Behavior:

- Create `<output_dir>/<run_name>/`.
- Refuse to overwrite existing run directory.
- Write each report as `<name>.json`.
- Return file paths.
- Use standard library only.

Use it in `run_baseline_disabled.py` if clean.

## Task 7: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
baseline_disabled_run:
  enabled: true
  phase: phase12
  phase_policy_allows_training: false
  can_train: false
  training_executed: false
  model_built: false
  predictions_generated: false
  evaluation_executed: false
  serialized_model: false
  artifacts:
    default_output_dir: tmp/cajas/baseline_disabled_runs
    default_run_name: phase12_baseline_disabled
    generated_files:
      - baseline_blocked_run_report.json
      - baseline_run_contract.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is the future training command skeleton.
- Phase 12 blocks before model construction.
- No model artifacts are produced.
- No trading signal is produced.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_run_contract.py
cajas/tests/test_baseline_runner.py
```

Optionally add:

```text
cajas/tests/test_baseline_artifacts.py
```

Tests should use temporary CSV/YAML data.

Run contract tests:

- can_train false
- build_model false
- fit_model false
- predict false
- evaluate false
- serialize_model false
- allowed metadata steps true
- serialization works

Baseline runner tests:

- training_executed false
- model_built false
- predictions_generated false
- evaluation_executed false
- serialized_model false
- blockers include Phase 12 training disabled policy
- JSON serialization works
- artifact writing creates both expected files
- no LightGBM import required

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 12:

- Baseline disabled runner added.
- Future training entry point exists but is blocked.
- CLI command:
  - `run_baseline_disabled.py`
- Artifact output.
- Manual push policy.
- Codex English-only policy.
- Training still disabled.
- No Qlib core changes/no trading.

Integration notes should add Phase 12:

- Baseline runner skeleton is now present.
- It performs preflight and contract checks but blocks before model creation.
- Phase 13 recommendation:
  - either add a fully explicit user-approved training enable switch while still no trading,
  - or first integrate a true Qlib DatasetH compatibility probe.

Data examples should add:

- Blocked-run artifacts do not contain raw rows.
- No model artifacts are produced.
- Prepared CSV labels remain strings.

## Task 10: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

If it finds `caixas/` typo paths, fix them in active docs/tasks if appropriate.

Do not rewrite old prompt history unless the typo causes current workflow confusion.

## Task 11: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/baseline/run_contract.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_runner.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/run_baseline_disabled.py
```

If added:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_artifacts.py
```

Run existing commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new disabled baseline command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact command:

```bash
rm -rf tmp/cajas/baseline_disabled_runs/phase12_baseline_disabled

./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/baseline_disabled_runs \
  --run-name phase12_baseline_disabled

find tmp/cajas/baseline_disabled_runs/phase12_baseline_disabled -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_baseline_preflight.py \
  cajas/tests/test_run_contract.py \
  cajas/tests/test_baseline_runner.py
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

### Commit 1: Phase 12 prompt and agent policy

```bash
git add tasks/phase_012_training_disabled_baseline_command_prompt.md AGENTS.md
git commit -m "docs: add phase 12 baseline command prompt and agent policy"
```

### Commit 2: run contract

```bash
git add cajas/baseline/run_contract.py cajas/tests/test_run_contract.py cajas/baseline/__init__.py
git commit -m "feat: add baseline run contract"
```

### Commit 3: disabled baseline runner

```bash
git add cajas/baseline/baseline_runner.py \
  cajas/scripts/run_baseline_disabled.py \
  cajas/tests/test_baseline_runner.py
git commit -m "feat: add training-disabled baseline runner"
```

If artifact helper was added:

```bash
git add cajas/baseline/baseline_artifacts.py cajas/tests/test_baseline_artifacts.py
```

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document training-disabled baseline command"
```

Do not run `git push`.

Report the manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly in English:

```text
Phase 12 completed.

Branch:
- cajas/market-recognition-phase-0

Agent policy:
- English-only Codex communication:
- Codex git push disabled:

Changed files:
- ...

Run contract:
- path:
- can_train:
- allowed metadata steps:
- forbidden model steps:
- training executed:

Disabled baseline runner:
- path:
- can_train:
- training enabled:
- phase policy allows training:
- training executed:
- model built:
- predictions generated:
- evaluation executed:
- serialized model:
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
- local commit(s):
- push: not run by Codex
- manual push command: git push origin cajas/market-recognition-phase-0

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
- Run `git push`.
