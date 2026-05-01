# Phase 40B Prompt: Fix Phase 36-40 Full Test Failure and Package Init Regression

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

Phase 36-40 was implemented and committed, but it is not fully closed because the final full test suite failed.

Phase 36-40 local commits:

```text
6bc1ca6e docs: add phase 36-40 holdout diagnosis prompt
d85e6c78 feat: add holdout benchmark and flat diagnosis
f954ca3c feat: add horizon and feature group analysis
12267542 feat: add research decision report
c1167c5c docs: document holdout diagnosis research workflow
```

Phase 36-40 focused tests passed, but full suite failed:

```text
./.venv-qlib313/bin/python -m pytest cajas/tests
1 failed, 158 passed
failing test:
cajas/tests/test_multi_model_baseline.py::MultiModelBaselineTests::test_runs_sklearn_models
```

Phase 36-40 report also listed suspicious package init paths:

```text
cajas/reports/init.py
cajas/baseline/init.py
cajas/datasets/init.py
```

This violates the repository policy:

```text
Python package initializer files must be named __init__.py, never init.py.
```

Phase 40B must fix these issues before any new feature work.

## Phase 40B Goal

1. Fix any `cajas/**/init.py` package init regression.
2. Fix the failing full-suite test:
   - `cajas/tests/test_multi_model_baseline.py::MultiModelBaselineTests::test_runs_sklearn_models`
3. Re-run path hygiene.
4. Re-run focused failing test.
5. Re-run full test suite.
6. Commit the cleanup fix locally only.
7. Do not push.

No new feature work unless required to fix the above.

## Absolute Boundaries

Do not:

- Modify `qlib/` core.
- Modify official upstream examples.
- Initialize Qlib.
- Execute Qlib workflow.
- Train new real-data models except tiny test fixtures required by tests.
- Run backtest/profit analysis.
- Calculate trading metrics.
- Add trading strategy.
- Add live trading/order execution.
- Treat `future_direction_*` as buy/sell signals.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Run `git push`.

## Task 1: Inspect Current State

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
```

Expected final state:

```bash
find cajas -path "*/init.py" -print
```

must produce no output.

If any of these exist:

```text
cajas/reports/init.py
cajas/baseline/init.py
cajas/datasets/init.py
```

fix with `git mv` if tracked:

```bash
git mv cajas/reports/init.py cajas/reports/__init__.py
git mv cajas/baseline/init.py cajas/baseline/__init__.py
git mv cajas/datasets/init.py cajas/datasets/__init__.py
```

If the destination already exists, merge useful exports into `__init__.py`, then remove `init.py`.

Do not lose exports added in Phase 36-40.

## Task 2: Reproduce the Failing Test

Run:

```bash
./.venv-qlib313/bin/python -m pytest -q cajas/tests/test_multi_model_baseline.py::MultiModelBaselineTests::test_runs_sklearn_models
```

Inspect the failure.

Likely areas to check:

```text
cajas/baseline/multi_model_baseline.py
cajas/baseline/local_baseline_trainer.py
cajas/tests/test_multi_model_baseline.py
```

Fix the production code if possible.

Only adjust the test if the expectation is outdated after Phase 27-40 changes.

Important likely cause:

- model family naming changed
- sanitizer changed output artifacts
- RandomForest / HistGradientBoosting status now recorded differently
- output directory layout changed
- test assumes exactly completed sklearn models while implementation reports status names differently

The fix should preserve robust multi-model behavior:

- model status should be clear: completed/skipped/failed
- at least one model should complete in tiny fixture tests
- failures should not crash all runs unless all models fail
- no trading metrics

## Task 3: Validate Package Init Policy

Run:

```bash
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- no `init.py`
- path hygiene 0 issues

If path hygiene does not catch `cajas/**/init.py`, update the checker/tests so it does.

## Task 4: Run Tests

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest -q cajas/tests/test_multi_model_baseline.py::MultiModelBaselineTests::test_runs_sklearn_models
./.venv-qlib313/bin/python -m pytest -q cajas/tests/test_multi_model_baseline.py
```

Run related tests:

```bash
./.venv-qlib313/bin/python -m pytest -q \
  cajas/tests/test_local_baseline_trainer.py \
  cajas/tests/test_multi_model_baseline.py \
  cajas/tests/test_feature_value_audit.py \
  cajas/tests/test_numeric_sanitizer.py
```

Run full suite:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Full suite must pass before committing.

## Task 5: Diff Review

Run:

```bash
git diff --check
git diff --stat
git status --short
```

Confirm:

- no `cajas/**/init.py`
- no `tmp/` artifacts staged
- raw CSV not staged
- `.codex/` not staged
- no unrelated `.agents/` files staged

## Suggested Commits

Prefer one focused fix commit after adding this prompt.

### Commit 1: Phase 40B prompt

```bash
git add tasks/phase_040b_fix_holdout_diagnosis_regressions_prompt.md
git commit -m "docs: add phase 40B regression fix prompt"
```

### Commit 2: regression fix

Stage only changed files required for the fix, for example:

```bash
git add -u cajas
git add cajas
git commit -m "fix: resolve holdout diagnosis regression failures"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 40B completed.

Branch:
- cajas/market-recognition-phase-0

Package init cleanup:
- incorrect init.py before:
- incorrect init.py after:
- path hygiene:

Test regression:
- failing test:
- root cause:
- fix:

Validation commands run:
- ...

Tests:
- focused failing test:
- related:
- full:

Git:
- local commit(s):
- push: not run by Codex
- manual push command: git push origin cajas/market-recognition-phase-0

Notes:
- ...
```
