# Phase 17B Prompt: Clean Qlib Workflow Probe Path Hygiene and Package Init

## Codex Communication Rules

- Communicate with the user in English only.
- All progress updates, questions, command summaries, and completion reports must be written in English.
- Do not use Chinese in Codex-facing interaction unless the user explicitly asks.
- Do not run `git push`.
- Stop after local commits and report the exact `git push` command for the user to run manually.

## Repository

Repository working directory:

```text
/home/phiner/projects/research/qlib-cajas/
```

Current branch:

```text
cajas/market-recognition-phase-0
```

## Context

Phase 17 completed, but the completion report contains inconsistent path information that must be cleaned up before Phase 18.

Reported issues:

1. Changed files included:

```text
cajas/qlib_compat/init.py
```

But package init should be:

```text
cajas/qlib_compat/__init__.py
```

2. Changed files included:

```text
caixas/scripts/probe_qlib_workflow_config.py
```

But the correct project path is:

```text
cajas/scripts/probe_qlib_workflow_config.py
```

3. The report also said one pytest command had a `caixas/...` typo before a corrected run passed.

Phase 17 also reported:

```text
pytest: 102 passed
qlib initialized: false
qlib workflow executed: false
training executed: false
```

## Phase 17B Goal

Phase 17B is a cleanup/finalization phase.

Main objectives:

1. Ensure there is no tracked or untracked `caixas/` path.
2. Ensure there is no tracked or untracked `cajas/qlib_compat/init.py`.
3. Ensure `cajas/qlib_compat/__init__.py` exists and exports Phase 17 modules.
4. Fix any active docs/tasks/config references to typo path `caixas/`.
5. Re-run path hygiene.
6. Re-run Qlib workflow config probe.
7. Re-run the full test suite.
8. Create local cleanup commit(s) only.
9. Do not push.

No new feature work unless required to fix the above.

## Absolute Boundaries

Do not:

- Modify `qlib/` core.
- Modify official upstream examples.
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

## Task 1: Inspect Git State and Problem Paths

Run:

```bash
git status --short
git branch --show-current
find . -path "./.git" -prune -o -path "./tmp" -prune -o -path "./.venv*" -prune -o -path "./.codex" -prune -o -path "./.agents" -prune -o -print | grep -E '(^|/)caixas(/|$)|cajas/qlib_compat/init\.py' || true
git ls-files | grep -E '(^|/)caixas(/|$)|cajas/qlib_compat/init\.py' || true
```

Expected:

- Branch is `cajas/market-recognition-phase-0`.
- `.agents/` may be untracked. Do not add it.
- There should be no tracked `caixas/...`.
- There should be no tracked `cajas/qlib_compat/init.py`.

If any tracked typo paths exist, fix with `git mv` or remove as appropriate.

## Task 2: Fix qlib_compat Package Init

Inspect:

```bash
find cajas/qlib_compat -maxdepth 1 -type f -print | sort
```

If this exists:

```text
cajas/qlib_compat/init.py
```

and this does not exist:

```text
cajas/qlib_compat/__init__.py
```

then run:

```bash
git mv cajas/qlib_compat/init.py cajas/qlib_compat/__init__.py
```

If both exist, inspect both and preserve useful exports/comments in `__init__.py`, then remove `init.py`.

Recommended exports:

```python
from .adapter_comparison_probe import AdapterComparisonReport, run_adapter_comparison_probe
from .dataset_shape_probe import DatasetHShapeProbeReport, run_dataset_h_shape_probe
from .prepared_dataset_h_adapter import PreparedQlibDatasetHAdapter
from .prepared_dataset_h_like import PreparedDatasetHLike
from .qlib_probe import QlibDatasetApiStatus, QlibImportStatus, probe_qlib_dataset_api
from .workflow_config_probe import (
    QlibWorkflowConfigIssue,
    QlibWorkflowConfigProbeReport,
    build_training_disabled_qlib_workflow_config,
    probe_qlib_workflow_config,
)

__all__ = [
    "AdapterComparisonReport",
    "DatasetHShapeProbeReport",
    "PreparedDatasetHLike",
    "PreparedQlibDatasetHAdapter",
    "QlibDatasetApiStatus",
    "QlibImportStatus",
    "QlibWorkflowConfigIssue",
    "QlibWorkflowConfigProbeReport",
    "build_training_disabled_qlib_workflow_config",
    "probe_qlib_dataset_api",
    "probe_qlib_workflow_config",
    "run_adapter_comparison_probe",
    "run_dataset_h_shape_probe",
]
```

Verify imports:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.qlib_compat import (
    PreparedDatasetHLike,
    PreparedQlibDatasetHAdapter,
    build_training_disabled_qlib_workflow_config,
    probe_qlib_dataset_api,
    probe_qlib_workflow_config,
    run_adapter_comparison_probe,
)
print(PreparedDatasetHLike.__name__)
print(PreparedQlibDatasetHAdapter.__name__)
print(build_training_disabled_qlib_workflow_config.__name__)
print(probe_qlib_dataset_api.__name__)
print(probe_qlib_workflow_config.__name__)
print(run_adapter_comparison_probe.__name__)
PY
```

## Task 3: Remove Any `caixas/` References From Active Files

Run:

```bash
grep -RIn --exclude-dir=.git --exclude-dir=tmp --exclude-dir=.venv-qlib313 --exclude-dir=.codex --exclude-dir=.agents 'caixas/' . || true
```

Fix typo references in active docs/tasks/config/scripts/tests.

Use `cajas/`, not `caixas/`.

Do not rewrite old prompt history unless the typo can cause current/future workflow confusion. If the typo exists in recent Phase 16/17 prompt or docs, fix it.

## Task 4: Run Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If there are issues, fix them and rerun.

## Task 5: Compile and Probe Validation

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/qlib_compat/__init__.py \
  cajas/qlib_compat/workflow_config_probe.py \
  cajas/scripts/probe_qlib_workflow_config.py \
  cajas/scripts/probe_qlib_dataset_h_adapter.py \
  cajas/scripts/probe_qlib_dataset_compat.py
```

Run Qlib probes:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Confirm:

- `qlib.init()` is not called.
- Qlib workflow is not executed.
- Training is not executed.
- Model is not constructed.

## Task 6: Artifact Smoke

Run:

```bash
rm -rf tmp/cajas/qlib_workflow_config/phase17b_qlib_workflow_config_cleanup

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/qlib_workflow_config \
  --run-name phase17b_qlib_workflow_config_cleanup

find tmp/cajas/qlib_workflow_config/phase17b_qlib_workflow_config_cleanup -maxdepth 1 -type f -print | sort
```

Do not stage `tmp/`.

## Task 7: Full Test Suite

Run the full suite with only `cajas/...` paths:

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

## Task 8: Diff Review and Commit

Run:

```bash
git diff --check
git diff --stat
git status --short
```

Confirm:

- `.agents/` is not staged.
- `tmp/` artifacts are not staged.
- raw CSV is not staged.
- no `caixas/` path is tracked or active.
- no `cajas/qlib_compat/init.py` remains.

Suggested commits:

### Commit 1: Phase 17B prompt

```bash
git add tasks/phase_017b_cleanup_qlib_workflow_probe_prompt.md
git commit -m "docs: add phase 17B qlib workflow cleanup prompt"
```

### Commit 2: cleanup

If files changed:

```bash
git add cajas/qlib_compat/__init__.py \
  cajas/scripts/probe_qlib_workflow_config.py \
  cajas/scripts/probe_qlib_dataset_h_adapter.py \
  cajas/scripts/probe_qlib_dataset_compat.py \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md \
  tasks/
git add -u cajas/qlib_compat
git commit -m "fix: clean qlib workflow probe paths"
```

Only include files that actually changed.

Do not run `git push`.

Report:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 17B completed.

Branch:
- cajas/market-recognition-phase-0

Cleanup:
- qlib_compat init path:
- old init.py present:
- caixas paths present:
- path hygiene status:

Changed files:
- ...

Qlib workflow probe:
- qlib initialized:
- qlib workflow executed:
- training executed:
- model constructed:
- artifact smoke:

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
