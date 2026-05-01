# Phase 17 Prompt: Fix Qlib Compat Init and Add Qlib Workflow Config Probe Without Training

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
- Codex may add this Phase 17 prompt under `tasks/`.
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

Phase 16 completed with local commits only. User will push manually.

Phase 16 commits:

```text
9c5d893e docs: add phase 16 qlib dataset adapter prompt
746e6c5a feat: add qlib DatasetH adapter probe
110bb80c docs: document qlib DatasetH adapter probe
```

Phase 16 added:

- `cajas/qlib_compat/prepared_dataset_h_adapter.py`
- `cajas/qlib_compat/adapter_comparison_probe.py`
- `cajas/scripts/probe_qlib_dataset_h_adapter.py`
- adapter tests
- docs/config updates

Phase 16 validation:

```text
qlib available: true
true Qlib subclass: false
qlib initialized: false
adapter comparison compatible: true
training executed: false
pytest: 98 passed
```

Known issue from Phase 16 report:

The package init file was reported as:

```text
cajas/qlib_compat/init.py
```

It should be:

```text
cajas/qlib_compat/__init__.py
```

Also, Phase 16 still had typo command attempts using `caixas/...`. Phase 17 must use only `cajas/...` in all commands, tests, docs, and completion report.

## Phase 17 Goal

Phase 17 should add a Qlib workflow config probe without training.

Main objectives:

1. Fix `cajas/qlib_compat/init.py` to `cajas/qlib_compat/__init__.py`.
2. Add a Qlib workflow config builder/probe that creates a training-disabled, inspection-only workflow config shape.
3. Add a config compatibility report comparing current `cajas` YAML fields with Qlib-style workflow expectations.
4. Add CLI and artifacts for the workflow config probe.
5. Add tests and docs/config updates.
6. Keep all training disabled.

This phase still does not initialize Qlib.

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
6. Do not commit `.agents/`.
7. Do not add `tasks/` to `.gitignore`.
8. Do not create new task prompt directories.
9. Do not describe `future_direction_8` as a buy/sell signal.
10. Do not train LightGBM or any other model.
11. Do not build, fit, predict, evaluate, or serialize any model.
12. Do not create predictions.
13. Do not calculate model metrics from predictions.
14. Do not run backtest/profit/return analysis.
15. Do not add trading strategy, live execution, auto order, or position sizing logic.
16. Do not install new runtime dependencies automatically.
17. Do not enable training in YAML.
18. Do not run `git push`.
19. Do not call `qlib.init()`.
20. Do not run Qlib workflow execution.
21. Do not claim the workflow config is runnable unless it has actually been run successfully in a later approved phase.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_016_qlib_dataset_h_adapter_probe_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- `.agents/` may be untracked. Do not add it.
- Working tree should be clean or only contain this Phase 17 prompt if already added.

## Task 2: Fix Qlib Compat Package Init

Inspect:

```bash
find cajas/qlib_compat -maxdepth 1 -type f -print | sort
```

If this exists:

```text
cajas/qlib_compat/init.py
```

rename it with Git:

```bash
git mv cajas/qlib_compat/init.py cajas/qlib_compat/__init__.py
```

If destination file already exists, inspect both and preserve useful exports/comments.

Recommended `cajas/qlib_compat/__init__.py` exports:

```python
from .adapter_comparison_probe import AdapterComparisonReport, run_adapter_comparison_probe
from .dataset_shape_probe import DatasetHShapeProbeReport, run_dataset_h_shape_probe
from .prepared_dataset_h_adapter import PreparedQlibDatasetHAdapter
from .prepared_dataset_h_like import PreparedDatasetHLike
from .qlib_probe import QlibDatasetApiStatus, QlibImportStatus, probe_qlib_dataset_api

__all__ = [
    "AdapterComparisonReport",
    "DatasetHShapeProbeReport",
    "PreparedDatasetHLike",
    "PreparedQlibDatasetHAdapter",
    "QlibDatasetApiStatus",
    "QlibImportStatus",
    "probe_qlib_dataset_api",
    "run_adapter_comparison_probe",
    "run_dataset_h_shape_probe",
]
```

After adding Phase 17 modules, update exports if useful.

Verify import:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.qlib_compat import (
    PreparedDatasetHLike,
    PreparedQlibDatasetHAdapter,
    probe_qlib_dataset_api,
    run_adapter_comparison_probe,
)
print(PreparedDatasetHLike.__name__)
print(PreparedQlibDatasetHAdapter.__name__)
print(probe_qlib_dataset_api.__name__)
print(run_adapter_comparison_probe.__name__)
PY
```

## Task 3: Add Qlib Workflow Config Builder

Add:

```text
cajas/qlib_compat/workflow_config_probe.py
```

Purpose:

- Build a Qlib-style workflow config dictionary for inspection only.
- Compare current `cajas` config to a Qlib-style workflow shape.
- Keep training disabled.
- Do not execute the workflow.
- Do not initialize Qlib.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class QlibWorkflowConfigIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class QlibWorkflowConfigProbeReport:
    config_name: str
    qlib_available: bool
    workflow_config_built: bool
    training_enabled: bool
    training_executed: bool
    qlib_initialized: bool
    qlib_workflow_executed: bool
    workflow_config: dict
    issues: list[QlibWorkflowConfigIssue]
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict: ...
```

Suggested functions:

```python
def build_training_disabled_qlib_workflow_config(
    *,
    config_path: str,
    input_override: str | None = None,
) -> dict:
    ...

def probe_qlib_workflow_config(
    *,
    config_path: str,
    input_override: str | None = None,
) -> QlibWorkflowConfigProbeReport:
    ...
```

Expected workflow config dictionary shape:

```python
{
    "experiment": {
        "name": "...",
        "phase": "phase17",
        "training_enabled": False,
        "training_executed": False,
    },
    "dataset": {
        "class": "cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter",
        "label_col": "future_direction_8",
        "segments": {...},
        "feature_count": 24,
        "leakage_columns": ["future_close_8", "future_return_8"],
    },
    "model": {
        "family": "LightGBM",
        "enabled": False,
        "constructed": False,
    },
    "workflow": {
        "qlib_init_required": False,
        "qlib_initialized": False,
        "execute_workflow": False,
    },
}
```

Rules:

- This is not necessarily a Qlib-native YAML yet.
- It is a Qlib-style config probe.
- Mark unsupported or unresolved fields as warnings/TODOs, not fake runnable fields.
- Do not call Qlib workflow APIs.
- Do not instantiate LightGBM.
- Do not train.

## Task 4: Add Workflow Config Compatibility CLI

Add:

```text
cajas/scripts/probe_qlib_workflow_config.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--json
--write-artifacts
--output-dir tmp/cajas/qlib_workflow_config
--run-name phase17_qlib_workflow_config
```

Behavior:

- Text mode prints:
  - config name
  - qlib available
  - workflow config built
  - training enabled false
  - training executed false
  - qlib initialized false
  - qlib workflow executed false
  - dataset class
  - model family
  - feature count
  - warnings/blockers
- JSON mode prints `QlibWorkflowConfigProbeReport.to_dict()`.
- If `--write-artifacts`, write:
  - `qlib_workflow_config_probe_report.json`
  - `qlib_workflow_config_draft.json`
- Do not execute the workflow.
- Do not train.

## Task 5: Add Qlib Workflow Config Schema Checks

Add a lightweight validation helper in `workflow_config_probe.py` or separate file:

```text
cajas/qlib_compat/workflow_config_schema.py
```

Optional; keep it simple.

Checks:

- `training_enabled` is false.
- `model.enabled` is false.
- `model.constructed` is false.
- `workflow.execute_workflow` is false.
- `workflow.qlib_initialized` is false.
- dataset label exists.
- segments exist.
- leakage columns declared.
- feature count > 0.

Return structured issues.

Do not over-engineer.

## Task 6: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
qlib_workflow_config_probe:
  enabled: true
  phase: phase17
  initialize_qlib: false
  execute_qlib_workflow: false
  training_enabled: false
  training_executed: false
  dataset_adapter_class: cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter
  model_family: LightGBM
  model_enabled: false
  model_constructed: false
  artifacts:
    default_output_dir: tmp/cajas/qlib_workflow_config
    default_run_name: phase17_qlib_workflow_config
    generated_files:
      - qlib_workflow_config_probe_report.json
      - qlib_workflow_config_draft.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is a config probe only.
- It does not initialize Qlib.
- It does not execute Qlib workflow.
- It does not train.
- It does not produce trading signals.

## Task 7: Add Tests

Add:

```text
cajas/tests/test_qlib_workflow_config_probe.py
```

Tests should use temporary CSV/YAML data where needed.

Test cases:

- workflow config builds for a valid temporary config
- report serializes to dict
- training_enabled false
- training_executed false
- qlib_initialized false
- qlib_workflow_executed false
- model.enabled false
- model.constructed false
- feature count > 0
- missing segments or label produce issue
- artifact writing creates both expected files through CLI helper if available

Do not require Qlib workflow execution.

Do not call `qlib.init()`.

## Task 8: Update Existing Qlib Compatibility Docs/CLI

Update if useful:

```text
cajas/scripts/probe_qlib_dataset_compat.py
cajas/scripts/probe_qlib_dataset_h_adapter.py
```

Only add short references to the new workflow config probe; do not break existing CLI behavior.

Update docs:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 17:

- Qlib workflow config probe added.
- CLI command:
  - `probe_qlib_workflow_config.py`
- Training still disabled.
- Qlib is not initialized.
- Qlib workflow is not executed.
- No Qlib core changes/no trading.

Integration notes should add Phase 17:

- Phase 15 proved Qlib imports.
- Phase 16 proved adapter shape comparison.
- Phase 17 creates an inspection-only Qlib-style workflow config.
- Phase 18 recommendation:
  - add a true Qlib workflow dry-run loader without execution, or
  - if explicitly approved, add controlled baseline training outside Qlib first.

Data examples should add:

- Workflow config artifacts live under `tmp/`.
- Draft workflow config does not contain raw rows.
- It is not a training output.

## Task 9: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/qlib_compat/workflow_config_probe.py \
  cajas/scripts/probe_qlib_workflow_config.py
```

If added:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/qlib_compat/workflow_config_schema.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run existing Qlib probes:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new workflow config probe:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact probe:

```bash
rm -rf tmp/cajas/qlib_workflow_config/phase17_qlib_workflow_config

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/qlib_workflow_config \
  --run-name phase17_qlib_workflow_config

find tmp/cajas/qlib_workflow_config/phase17_qlib_workflow_config -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_future_training_skeleton.py \
  cajas/tests/test_baseline_artifacts.py \
  cajas/tests/test_label_encoding.py \
  cajas/tests/test_metric_plan.py \
  cajas/tests/test_training_input_materialization.py \
  cajas/tests/test_qlib_probe.py \
  cajas/tests/test_dataset_shape_probe.py \
  cajas/tests/test_prepared_dataset_h_like.py \
  cajas/tests/test_prepared_dataset_h_adapter.py \
  cajas/tests/test_adapter_comparison_probe.py \
  cajas/tests/test_qlib_workflow_config_probe.py
```

Check Git:

```bash
git status --short
git diff --stat
git diff
```

Confirm:

- `.agents/` is not staged.
- `tmp/` artifacts are not staged.
- raw CSV is not staged.

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 17 prompt and qlib compat init fix

```bash
git add tasks/phase_017_qlib_workflow_config_probe_prompt.md \
  cajas/qlib_compat/__init__.py
git add -u cajas/qlib_compat
git commit -m "fix: use standard qlib compat package init"
```

If prompt and init fix should be separate, split them.

### Commit 2: workflow config probe

```bash
git add cajas/qlib_compat/workflow_config_probe.py \
  cajas/scripts/probe_qlib_workflow_config.py \
  cajas/tests/test_qlib_workflow_config_probe.py \
  cajas/qlib_compat/__init__.py
```

If schema helper was added:

```bash
git add cajas/qlib_compat/workflow_config_schema.py
```

Then:

```bash
git commit -m "feat: add qlib workflow config probe"
```

### Commit 3: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document qlib workflow config probe"
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
Phase 17 completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- qlib_compat init:
- old init.py removed:

Changed files:
- ...

Qlib workflow config probe:
- path:
- workflow config built:
- qlib available:
- qlib initialized:
- qlib workflow executed:
- training enabled:
- training executed:
- model enabled:
- model constructed:
- feature count:
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

Untracked intentionally left:
- .agents/ if present

Notes:
- ...
```

## Forbidden Work

Do not:

- Modify `qlib/` core.
- Modify official examples.
- Initialize Qlib.
- Execute Qlib workflow.
- Train any model.
- Build/fit/predict/evaluate/serialize any model.
- Create predictions.
- Calculate model metrics from predictions.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Commit `.agents/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
- Run `git push`.
