# Phase 13 Prompt: Add Explicit Training Enable Gate and Future Baseline Training Skeleton

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
- Codex may add this Phase 13 prompt under `tasks/`.
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

Phase 12 completed with local commits only. User will push manually.

Phase 12 commits:

```text
01d87281 docs: add phase 12 baseline command prompt and agent policy
ea500349 feat: add baseline run contract
ea05af6a feat: add training-disabled baseline runner
a6d193cd docs: document training-disabled baseline command
```

Phase 12 added:

- AGENTS.md English-only Codex policy
- AGENTS.md no-push policy
- `cajas/baseline/run_contract.py`
- `cajas/baseline/baseline_runner.py`
- `cajas/scripts/run_baseline_disabled.py`
- tests for run contract and disabled baseline runner
- docs/config updates

Phase 12 validation:

```text
can_train: false
training enabled: false
phase policy allows training: false
training executed: false
model built: false
predictions generated: false
evaluation executed: false
serialized model: false
pytest: 65 passed
git status --short: clean
```

## Phase 13 Goal

Phase 13 should add the final explicit future training enable gate and a future baseline training skeleton, while keeping actual training disabled.

Main objectives:

1. Add an explicit training enable request contract.
2. Add a future baseline training skeleton that can only run if multiple gates are explicitly enabled.
3. Keep all training gates disabled in config and phase policy.
4. Add a CLI that demonstrates the future training path is blocked before model construction.
5. Add artifact output for the blocked future-training attempt.
6. Add tests proving training cannot run unless every gate is enabled.
7. Update docs/config.

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
git check-ignore -v tasks/phase_012_training_disabled_baseline_command_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- Working tree should be clean or only contain this Phase 13 prompt if already added.

## Task 2: Add Explicit Training Enable Contract

Add:

```text
cajas/baseline/training_enable_contract.py
```

Purpose:

- Define exactly what would be required to enable training in a future phase.
- Keep Phase 13 training disabled.
- Make accidental training impossible unless all gates are true.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class TrainingEnableGate:
    name: str
    enabled: bool
    required: bool
    reason: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class TrainingEnableContract:
    phase: str
    config_name: str
    target_label: str
    model_family: str
    gates: list[TrainingEnableGate]
    can_enable_training: bool
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...

    def gate_map(self) -> dict[str, bool]: ...
```

Suggested function:

```python
def build_phase13_training_enable_contract(
    *,
    config_path: str,
    model_family: str = "LightGBM",
    user_training_approval: bool = False,
    phase_policy_allows_training: bool = False,
    config_training_enabled: bool | None = None,
    strict_readiness_required: bool = False,
) -> TrainingEnableContract:
    ...
```

Required gates:

```text
user_training_approval
phase_policy_allows_training
config_training_enabled
training_guard_allows_training
strict_readiness_accepted_or_passed
no_feature_leakage
label_encoding_plan_present
dependency_probe_complete
artifact_output_configured
no_trading_or_backtest_scope
```

Phase 13 expected values:

- `user_training_approval: false`
- `phase_policy_allows_training: false`
- `config_training_enabled: false`
- `can_enable_training: false`

Do not train.

## Task 3: Add Future Baseline Training Skeleton

Add:

```text
cajas/baseline/future_training_skeleton.py
```

Purpose:

- Represent the future baseline training command flow.
- In Phase 13, stop before model construction.
- Provide a single place where a future phase could add training code after explicit approval.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class FutureTrainingSkeletonStep:
    name: str
    planned: bool
    allowed_now: bool
    executed: bool
    reason: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class FutureTrainingSkeletonReport:
    config_name: str
    phase: str
    model_family: str
    target_label: str
    can_enable_training: bool
    can_train_now: bool
    training_executed: bool
    model_built: bool
    fit_executed: bool
    prediction_executed: bool
    evaluation_executed: bool
    serialization_executed: bool
    enable_contract: dict
    steps: list[dict]
    blockers: list[str]
    warnings: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_future_training_skeleton(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    user_training_approval: bool = False,
    phase_policy_allows_training: bool = False,
) -> FutureTrainingSkeletonReport:
    ...
```

Behavior:

1. Build Phase 13 training enable contract.
2. Build Phase 12 disabled baseline report.
3. Build Phase 11 preflight report.
4. Return skeleton report.
5. `can_train_now` must be false in Phase 13.
6. `training_executed` must be false.
7. All model/training/evaluation/serialization executed flags must be false.
8. Do not import LightGBM.
9. Do not instantiate any model.
10. Do not call fit/predict/evaluate.
11. Do not write model files.

Planned steps:

```text
load_config
run_preflight
build_dataset
apply_label_encoding
construct_model
fit_model
predict_valid
evaluate_valid
write_model_artifact
write_training_report
```

Phase 13 allowed now:

- load_config
- run_preflight
- build_dataset metadata only
- label encoding plan only
- write blocked-training report

Phase 13 not allowed:

- construct_model
- fit_model
- predict_valid
- evaluate_valid
- write_model_artifact

## Task 4: Add Future Training Skeleton CLI

Add:

```text
cajas/scripts/build_future_training_skeleton.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_future_training_skeleton.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--model-family LightGBM
--json
--write-artifacts
--output-dir tmp/cajas/future_training_skeletons
--run-name phase13_future_training_skeleton
```

Intentionally do not add flags such as `--enable-training` in Phase 13.

Behavior:

- Text mode prints:
  - config name
  - phase
  - model family
  - target label
  - can enable training false
  - can train now false
  - training executed false
  - model built false
  - fit executed false
  - prediction executed false
  - evaluation executed false
  - serialization executed false
  - blockers
  - next steps
- JSON mode prints `FutureTrainingSkeletonReport.to_dict()`.
- If `--write-artifacts`, write:
  - `future_training_skeleton_report.json`
  - `training_enable_contract.json`
- Exit zero if blocked due Phase 13 policy.
- Exit non-zero for config/data/path hygiene errors.

## Task 5: Add Baseline Artifact Helper If Not Already Present

If no shared helper exists yet, add:

```text
cajas/baseline/baseline_artifacts.py
```

Purpose:

- Write local JSON reports for baseline-related commands.
- Avoid duplicating artifact writing logic across baseline disabled runner, scaffold, and future skeleton.
- Keep this small.

Suggested function:

```python
def write_baseline_reports(
    *,
    output_dir: str | Path,
    run_name: str,
    reports: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    ...
```

Rules:

- Create `<output_dir>/<run_name>/`.
- Refuse to overwrite existing run directory.
- Write each report as `<report_name>.json`.
- Return file paths.
- Use standard library only.
- Do not write raw data rows.

Use it in the new skeleton CLI. Do not refactor older CLIs unless the change is very safe and tests remain simple.

## Task 6: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
future_training_skeleton:
  enabled: true
  phase: phase13
  user_training_approval: false
  phase_policy_allows_training: false
  can_enable_training: false
  can_train_now: false
  training_executed: false
  model_built: false
  fit_executed: false
  prediction_executed: false
  evaluation_executed: false
  serialization_executed: false
  artifacts:
    default_output_dir: tmp/cajas/future_training_skeletons
    default_run_name: phase13_future_training_skeleton
    generated_files:
      - future_training_skeleton_report.json
      - training_enable_contract.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is a future training skeleton only.
- Phase 13 intentionally does not expose an enable-training CLI flag.
- No model is built.
- No predictions/evaluation/model artifacts are produced.
- No trading signal is produced.

## Task 7: Add Tests

Add:

```text
cajas/tests/test_training_enable_contract.py
cajas/tests/test_future_training_skeleton.py
```

If artifact helper was added:

```text
cajas/tests/test_baseline_artifacts.py
```

Tests should use temporary CSV/YAML data.

Training enable contract tests:

- all Phase 13 default gates false where expected
- `can_enable_training` false
- config training false blocks
- phase policy false blocks
- user approval false blocks
- gate map works
- serialization works

Future training skeleton tests:

- `can_train_now` false
- `training_executed` false
- `model_built` false
- `fit_executed` false
- `prediction_executed` false
- `evaluation_executed` false
- `serialization_executed` false
- model construction step is not allowed
- artifact writing creates expected reports
- no LightGBM import required

## Task 8: Update AGENTS.md

Ensure `AGENTS.md` includes and preserves:

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

Do not duplicate the section if already present.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 13:

- Training enable contract added.
- Future training skeleton added.
- CLI command:
  - `build_future_training_skeleton.py`
- Artifact output.
- Training still disabled.
- No model construction/no fit/no predict/no evaluate/no serialize.
- No Qlib core changes/no trading.
- Manual push policy remains active.

Integration notes should add Phase 13:

- The project now has a future training skeleton.
- It is blocked by explicit gates.
- Phase 14 recommendation:
  - only if user explicitly approves, add a controlled baseline training implementation with artifacts only and no trading;
  - otherwise add a true Qlib DatasetH compatibility probe.

Data examples should add:

- Future skeleton artifacts do not contain raw rows.
- Labels remain strings until a future approved training phase.
- Label encoding plan remains metadata-only.

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
./.venv-qlib313/bin/python -m py_compile cajas/baseline/training_enable_contract.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/future_training_skeleton.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/build_future_training_skeleton.py
```

If added:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_artifacts.py
```

Run existing commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new skeleton command:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_future_training_skeleton.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_future_training_skeleton.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact command:

```bash
rm -rf tmp/cajas/future_training_skeletons/phase13_future_training_skeleton

./.venv-qlib313/bin/python cajas/scripts/build_future_training_skeleton.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/future_training_skeletons \
  --run-name phase13_future_training_skeleton

find tmp/cajas/future_training_skeletons/phase13_future_training_skeleton -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_baseline_runner.py \
  cajas/tests/test_training_enable_contract.py \
  cajas/tests/test_future_training_skeleton.py
```

If `test_baseline_artifacts.py` was added, include it.

Check Git:

```bash
git status --short
git diff --stat
git diff
```

Confirm no raw CSV or `tmp/` generated outputs are staged.

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 13 prompt and policy check

```bash
git add tasks/phase_013_future_training_skeleton_prompt.md AGENTS.md
git commit -m "docs: add phase 13 future training skeleton prompt"
```

Only include `AGENTS.md` if changed.

### Commit 2: training enable contract

```bash
git add cajas/baseline/training_enable_contract.py \
  cajas/tests/test_training_enable_contract.py \
  cajas/baseline/__init__.py
git commit -m "feat: add explicit training enable contract"
```

### Commit 3: future training skeleton

```bash
git add cajas/baseline/future_training_skeleton.py \
  cajas/scripts/build_future_training_skeleton.py \
  cajas/tests/test_future_training_skeleton.py
git commit -m "feat: add future baseline training skeleton"
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
git commit -m "docs: document future training skeleton gates"
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
Phase 13 completed.

Branch:
- cajas/market-recognition-phase-0

Agent policy:
- English-only Codex communication:
- Codex git push disabled:

Changed files:
- ...

Training enable contract:
- path:
- can_enable_training:
- gates:
- blockers:
- warnings:

Future training skeleton:
- path:
- can_train_now:
- training executed:
- model built:
- fit executed:
- prediction executed:
- evaluation executed:
- serialization executed:
- blocked steps:
- next steps:

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
