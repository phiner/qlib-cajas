# 043 — Resolve EURUSD Completed Progress Block After Tail-Bias Hardening

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent committed work:
- Commit `7ab8234a`
- Selection standards report is ready.
- Tail-bias audit is pass:
  - `trend_batch_count=40`
  - `trend_near_tail_count=0`
  - `trend_near_tail_ratio=0.0`
  - `trend_ideal_mid_ratio=0.5`
- Candidate audit final status:
  - `watch`
  - `must_fix_failures=[]`
- Git status is clean.

Current problem:
- Completed progress report is unexpectedly blocked:
  ```text
  status=blocked
  blocking=true
  completed_count=15
  pending_count=85
  ```
- This differs from the expected fresh-start state because local completed-review artifacts already exist and were preserved.
- We need to determine whether those 15 completed rows are:
  1. valid reviews for the current active batch,
  2. stale reviews from a previous batch/reset,
  3. schema-invalid rows after label/schema changes,
  4. rows for sample IDs no longer present in the current batch,
  5. JSONL/CSV mismatch,
  6. or some other progress-report logic issue.

Important:
- Do not delete completed CSV/JSONL without explicit backup.
- Do not reset/rebuild active batch unless the diagnosis says it is necessary and the action is explicit.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training.
- No trading signals/orders.
- No Qlib core changes.

## Objective

Resolve the completed-progress `blocked` state cleanly before review continues.

Final acceptable states:

### Option A — keep current 15 completed reviews
If they are valid for current active batch:
```text
status=valid_in_progress
blocking=false
completed_count=15
pending_count=85
```

### Option B — archive stale completed reviews and restart fresh
If the 15 rows are stale/incompatible from a previous batch:
```text
status=awaiting_review_input
blocking=false
completed_count=0
pending_count=100
```

In either case:
- no blocked completed progress,
- no hidden stale review data,
- reports clearly explain what happened,
- data is backed up before removal or archival.

## Required Work

### 1. Inspect current files

Check:

```bash
ls -lh tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
ls -lh tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv || true
ls -lh tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl || true
cat tmp/validation-eurusd-completed-review-progress.json
```

Print key fields:
- `status`
- `reason`
- `blocking`
- `batch_count`
- `completed_count`
- `pending_count`
- `csv_schema_status`
- `jsonl_audit_status`
- `missing_required_fields`
- `invalid_review_rows`
- `completed_sample_ids`
- `completed_without_jsonl`
- `jsonl_without_completed`
- `jsonl_without_batch`

### 2. Compare completed rows to current batch

Run diagnostic:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd
from pathlib import Path

batch_p = Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv")
completed_p = Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv")

batch = pd.read_csv(batch_p)
completed = pd.read_csv(completed_p) if completed_p.exists() else pd.DataFrame()

print("batch rows:", len(batch))
print("completed rows:", len(completed))

if "sample_id" in batch and "sample_id" in completed:
    batch_ids = set(batch["sample_id"].astype(str))
    completed_ids = set(completed["sample_id"].astype(str))
    print("completed in batch:", len(completed_ids & batch_ids))
    print("completed not in batch:", sorted(completed_ids - batch_ids)[:50])
    print("batch pending count:", len(batch_ids - completed_ids))
    print("duplicate completed sample_ids:", completed["sample_id"][completed["sample_id"].duplicated()].astype(str).tolist())

cols = [c for c in [
    "sample_id", "timestamp", "candidate_type", "pattern_label",
    "market_context", "direction_context", "review_status",
    "structure_quality", "follow_through_quality", "review_confidence",
    "review_updated_at_utc"
] if c in completed.columns]
print("completed columns:", list(completed.columns))
if len(completed):
    print(completed[cols].to_string(index=False))
PY
```

### 3. Diagnose block reason

Inspect report implementation if needed:

```text
cajas/reports/validation_eurusd_completed_review_progress.py
```

Classify block reason:

```text
completed_rows_not_in_current_batch
missing_required_fields
invalid_enum_values
invalid_score_values
duplicate_sample_ids
jsonl_malformed
jsonl_missing_for_completed
completed_csv_unreadable
report_logic_bug
```

Output a concise diagnosis in final response.

### 4. Decide safe handling

Use these rules:

#### Keep reviews if:
- all completed sample IDs exist in current batch,
- required fields are valid,
- enum/schema is compatible,
- JSONL audit is acceptable or only warning,
- completed rows are clearly from current active batch.

Then fix report logic if it incorrectly blocks.

#### Archive stale reviews if:
- many/all completed sample IDs are not in current batch,
- completed timestamps/candidate types differ from current batch rows,
- completed file is from pre-reset batch,
- schema is incompatible and not worth migration.

Archive by moving completed artifacts to timestamped backup:

```text
tmp/eurusd/review_reset_backups/YYYYMMDD_HHMMSS_stale_completed_progress/
```

Backup:
```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl
tmp/validation-eurusd-completed-review-progress.json
tmp/validation-eurusd-completed-review-progress.md
```

Then remove active completed files only after backup.

Do not remove active batch.

### 5. Regenerate reports

After fixing or archiving:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_warning_inventory
```

Expected:
- completed progress not blocked.
- candidate audit remains watch/pass, not blocked.

### 6. If report logic needs improvement

If fresh/stale handling exposes report logic weakness, update:
```text
cajas/reports/validation_eurusd_completed_review_progress.py
cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Tests to add:
1. Completed rows all in current batch -> `valid_in_progress`, not blocked.
2. Completed rows not in current batch -> blocked or stale-review status with clear reason.
3. Missing JSONL with valid completed CSV -> warning or valid with audit warning, depending current intended semantics.
4. Stale completed CSV archived scenario produces fresh-start status.
5. Schema v2 values accepted.

### 7. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_candidate_selection_standards.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile if Python changed:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/reports/validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Run fast validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Run hygiene:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

### 8. Commit if code/docs/tasks changed

If only local `tmp/` completed artifacts were archived and no tracked files changed:
- no commit required.

If report logic/tests/docs/task prompt changed:
```bash
git add cajas tasks
git commit -m "fix: resolve EURUSD completed progress blocking state"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash if any
- Completed progress initial status
- Exact block reason
- Whether 15 completed rows were kept or archived
- Backup directory if archived
- Final completed progress status
- Completed count
- Pending count
- Candidate audit status after fix
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command if commit created:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- push automatically
- create branches
- reset/rebuild batch unless explicitly diagnosed and necessary
- delete completed/rejected CSV/JSONL without backup
- add SQLite
- train models
- produce trading signals/orders
- modify Qlib core
