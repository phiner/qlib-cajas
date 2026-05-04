# 029 — Validate and Close EURUSD Rejected Sample Workflow

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Previous task:
- Task 028 implemented rejected/bad-sample workflow:
  - rejected sample CSV
  - rejected sample JSONL events
  - GUI reject controls
  - skip-by-default navigation
  - rejected-aware progress metrics
  - rejected-samples report + CLI
  - batch-builder exclusion support

Issue:
- Implementation summary reported pytest failure because it ran the wrong Python environment:
  ```text
  python3 -m pytest ... -> No module named pytest
  ```
- The project validation environment is:
  ```bash
  ./.venv-qlib313/bin/python
  ```
- Previous successful validations consistently used:
  ```bash
  ./.venv-qlib313/bin/python -m pytest ...
  ```

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only.
- No SQLite.
- Do not reset active batch.
- Do not regenerate active batch.
- Do not delete completed/rejected CSV/JSONL.
- No model training, no trading signals/orders, no Qlib core changes.

## Objective

Finish task 028 properly by validating the rejected-sample workflow in the correct virtual environment and fixing any issues found.

This is a validation/closure task, not a redesign task.

## Required Work

### 1. Confirm git state and commit status

Run:

```bash
git status --short
git log --oneline -5
```

If task 028 changes are not committed:
- commit them after validation.

If they are committed:
- report commit hash.

### 2. Use the correct project Python

Confirm:

```bash
./.venv-qlib313/bin/python --version
./.venv-qlib313/bin/python -m pytest --version
```

If pytest is missing in `.venv-qlib313`, report clearly and do not pretend validation passed.

Do not use system `python3` for project validation.

### 3. Run focused rejected workflow tests

Run:

```bash
./.venv-qlib313/bin/python -m pytest -q \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_rejected_samples.py
```

If failures occur:
- fix them.
- rerun the same command until pass or report remaining issue clearly.

### 4. Run report/CLI smoke

Run:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_rejected_samples_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Expected with no rejected samples yet:
- rejected report should be `no_rejections` or equivalent valid empty state.
- completed progress should remain fresh-start or current valid progress depending current review state.
- no destructive changes.

### 5. Run py_compile

Run:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/research/eurusd_pattern_review_gui.py \
  cajas/apps/eurusd_pattern_review_app.py \
  cajas/reports/validation_eurusd_completed_review_progress.py \
  cajas/reports/validation_eurusd_pattern_review_batch.py \
  cajas/reports/validation_eurusd_rejected_samples.py \
  cajas/scripts/build_eurusd_pattern_review_batch.py \
  cajas/scripts/build_eurusd_rejected_samples_report.py \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_rejected_samples.py
```

### 6. Run full fast validation

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

### 7. Run hygiene

Run:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

### 8. Optional manual GUI smoke

If environment supports browser interaction:

```bash
./scripts/run_eurusd_review_gui.sh
```

Manual checks:
1. GUI starts.
2. Reject controls are visible but safe.
3. Reject button requires confirmation.
4. Rejecting a sample writes rejected CSV/JSONL.
5. Rejected sample is skipped by Next.
6. Go to Sample can still view rejected sample with warning.
7. Save / Save and Next still work.
8. No stale toast replay.

If manual GUI cannot be run, report not run.

## Commit Requirements

If task 028 changes were already committed:
- create a new commit only if fixes are needed.

If task 028 changes are uncommitted:
- after validation passes, commit:

```bash
git add cajas scripts tasks
git commit -m "feat: add EURUSD rejected sample workflow"
```

If only test/validation fixes are added:

```bash
git add cajas scripts tasks
git commit -m "test: validate EURUSD rejected sample workflow"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash(es)
- Whether previous pytest failure was environment-related
- Correct Python used
- Rejected workflow test results
- Report/CLI smoke results
- py_compile result
- fast validation result
- hygiene result
- Manual GUI smoke result if run
- Rejected CSV/JSONL behavior confirmation
- Progress report rejected-aware behavior confirmation
- Batch builder exclusion support confirmation
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- reset review data
- regenerate active batch
- delete completed/rejected CSV/JSONL
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
