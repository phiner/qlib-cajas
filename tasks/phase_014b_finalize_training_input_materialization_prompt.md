# Phase 14B Prompt: Finalize Training Input Materialization Preview

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

Phase 14 implementation work appears mostly done, but it was not finalized.

Reported changed files:

```text
cajas/baseline/label_encoding.py
cajas/baseline/metric_plan.py
cajas/baseline/training_input_materialization.py
cajas/scripts/materialize_training_inputs_preview.py
cajas/tests/test_label_encoding.py
cajas/tests/test_metric_plan.py
cajas/tests/test_training_input_materialization.py
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
cajas/baseline/future_training_skeleton.py
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

Known cleanup items:

- `tasks/phase_014_training_input_materialization_prompt.md` is untracked and should be added.
- `.agents/` is untracked and should not be committed unless explicitly intended. Leave it untracked.
- A real-data materialization smoke run was not run.
- A previous test command string included typo path `caixas/tests/...`; use only `cajas/tests/...`.
- `python` is not available in this shell; use `./.venv-qlib313/bin/python`.

## Phase 14B Goal

Finalize Phase 14 by:

1. Checking the current working tree.
2. Running full validation with correct `cajas/...` paths.
3. Running real-data materialization smoke tests into `tmp/`.
4. Confirming generated artifacts are not staged.
5. Adding the Phase 14 prompt under `tasks/`.
6. Creating local commits only.
7. Reporting the manual push command.

No training. No model build/fit/predict/evaluate/serialize. No Qlib core changes. No trading logic.

## Absolute Boundaries

Do not:

- Modify `qlib/` core.
- Modify official upstream examples.
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

## Task 1: Inspect Current State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_014_training_input_materialization_prompt.md || true
```

Expected:

- Branch is `cajas/market-recognition-phase-0`.
- `tasks/` is not ignored.
- `.agents/` may be untracked; do not add it.
- `tasks/phase_014_training_input_materialization_prompt.md` should be untracked or modified and should be added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

If `caixas/` typo paths are found in active docs/tasks, fix them.

Do not rewrite old prompt history unless the typo causes current workflow confusion.

## Task 3: Compile Checks

Run:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/baseline/label_encoding.py \
  cajas/baseline/metric_plan.py \
  cajas/baseline/training_input_materialization.py \
  cajas/scripts/materialize_training_inputs_preview.py \
  cajas/baseline/future_training_skeleton.py
```

If `cajas/baseline/__init__.py` exports new Phase 14 objects, compile/import-check it too.

Run import check:

```bash
./.venv-qlib313/bin/python - <<'PY'
from cajas.baseline.label_encoding import default_future_direction_8_encoding, preview_label_encoding
from cajas.baseline.metric_plan import build_multiclass_metric_plan
from cajas.baseline.training_input_materialization import materialize_training_inputs_preview
print(default_future_direction_8_encoding.__name__)
print(preview_label_encoding.__name__)
print(build_multiclass_metric_plan.__name__)
print(materialize_training_inputs_preview.__name__)
PY
```

## Task 4: Real-Data Materialization Smoke Runs

Run CSV-writing smoke:

```bash
rm -rf tmp/cajas/training_input_previews/phase14_training_inputs_preview

./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/training_input_previews \
  --run-name phase14_training_inputs_preview
```

Inspect artifacts:

```bash
find tmp/cajas/training_input_previews/phase14_training_inputs_preview -maxdepth 1 -type f -print | sort
```

Run JSON/no-csv smoke:

```bash
rm -rf tmp/cajas/training_input_previews/phase14_training_inputs_preview_json

./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/training_input_previews \
  --run-name phase14_training_inputs_preview_json \
  --json \
  --no-csv
```

Inspect JSON/no-csv artifacts:

```bash
find tmp/cajas/training_input_previews/phase14_training_inputs_preview_json -maxdepth 1 -type f -print | sort
```

Confirm:

- Training is not executed.
- Model is not built.
- No predictions are generated.
- No model metrics are calculated.
- Output is under `tmp/` only.
- Nothing under `tmp/` is staged.

## Task 5: Full Test Run

Run with correct `cajas/...` paths only:

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
  cajas/tests/test_training_input_materialization.py
```

## Task 6: Diff and Staging Review

Run:

```bash
git diff --check
git diff --stat
git status --short
```

Confirm:

- No raw CSV is staged.
- No `tmp/` artifacts are staged.
- `.agents/` is not staged.
- `.codex/` is not staged.
- `tasks/phase_014_training_input_materialization_prompt.md` is staged/committed.
- All intended Phase 14 source, test, config, and docs changes are included.

## Task 7: Local Commits Only

Prefer focused commits.

### Commit 1: Phase 14 prompt

```bash
git add tasks/phase_014_training_input_materialization_prompt.md
git commit -m "docs: add phase 14 training input materialization prompt"
```

### Commit 2: label encoding and metric plan

```bash
git add cajas/baseline/label_encoding.py \
  cajas/baseline/metric_plan.py \
  cajas/tests/test_label_encoding.py \
  cajas/tests/test_metric_plan.py \
  cajas/baseline/__init__.py
git commit -m "feat: add label encoding and metric plans"
```

Only include `cajas/baseline/__init__.py` if it changed.

### Commit 3: training input materialization

```bash
git add cajas/baseline/training_input_materialization.py \
  cajas/scripts/materialize_training_inputs_preview.py \
  cajas/tests/test_training_input_materialization.py \
  cajas/baseline/future_training_skeleton.py
git commit -m "feat: add training input materialization preview"
```

Only include `future_training_skeleton.py` if it changed.

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document training input materialization preview"
```

Do not run `git push`.

## Completion Report Format

Report exactly in English:

```text
Phase 14B completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Real-data smoke:
- csv artifact mode:
- json/no-csv mode:
- output directories:
- training executed:
- model built:
- predictions generated:
- model metrics calculated:

Label encoding:
- mapping:
- source labels mutated:
- unknown label policy:

Metric plan:
- task type:
- primary metric:
- trading metrics present:

Materialization:
- feature count:
- segments:
- csv artifacts:
- json artifacts:

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
