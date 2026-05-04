# 017 — Validate EURUSD Completed Review Progress

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current user status:
- The user has manually reviewed about 21 EURUSD 15m samples in the GUI.
- GUI persistence uses CSV/JSONL only.
- Completed review data should be stored in:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl`
- Batch input should be:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- The user wants to validate the review progress now.

Important:
- Do not delete review data.
- Do not reset batch.
- Do not regenerate review samples.
- Do not alter completed CSV/JSONL.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.

## Objective

Validate current completed EURUSD review progress and produce a clear report:
1. reviewed count / pending count / completion ratio
2. completed CSV schema validity
3. JSONL audit validity and alignment with completed CSV
4. duplicates / malformed rows / missing fields
5. whether it is safe to continue review
6. next action

## Required Checks

### 1. Confirm files exist

Check:
```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl
```

### 2. Count progress

Read batch CSV and completed CSV. Report:
- `batch_count`
- `completed_count`
- `pending_count`
- `completion_ratio`
- `completed_sample_ids`
- `pending_sample_ids`

Expected now: completed count should be around 21. If not, report actual count.

### 3. Validate completed CSV schema

Required identity fields:
- `sample_id`
- `timestamp`
- `candidate_type`

Required review fields should match current schema. Include:
- pattern label field
- market context field
- direction context field
- review status field
- structure quality score
- follow-through quality score
- review confidence score
- `review_updated_at_utc`

Validate:
- no duplicate `sample_id`
- completed sample IDs exist in batch
- no forbidden trading/action columns
- score values are in allowed range
- enum values are allowed if schema enumerations are available
- notes may be blank

### 4. Validate JSONL audit history

Read completed events JSONL line by line. Report:
- `jsonl_event_count`
- `jsonl_valid_event_count`
- `jsonl_malformed_line_count`
- `jsonl_unique_sample_count`
- completed CSV samples without JSONL event
- JSONL sample IDs not present in batch
- JSONL sample IDs not present in completed CSV

Allow multiple JSONL events per sample.

### 5. Report artifacts

Create or reuse report outputs:
```text
tmp/validation-eurusd-completed-review-progress.json
tmp/validation-eurusd-completed-review-progress.md
```

If an equivalent completion report already exists, extend or run it instead of duplicating.

Suggested status:
- `valid_in_progress`: completed rows valid, pending remains.
- `valid_ready_for_summary`: all batch rows completed and valid.
- `warning`: usable but JSONL gaps/minor issues.
- `blocked`: corrupted completed CSV, missing sample IDs, invalid required fields, severe schema errors.

For 21 reviewed samples, expected:
```text
status=valid_in_progress
next_action=continue_human_review
```

## Implementation Options

Search first:
```bash
grep -R "completed review" -n cajas/reports cajas/scripts cajas/tests
grep -R "review.*completion" -n cajas/reports cajas/scripts cajas/tests
```

If no adequate report exists, add:
```text
cajas/reports/validation_eurusd_completed_review_progress.py
cajas/scripts/build_eurusd_completed_review_progress_report.py
cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Keep implementation read-only.

## Commands

Run report:
```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

If new script is added, defaults should work without long args.

Run tests:
```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_completed_review_progress.py
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_batch.py
```

Run py_compile:
```bash
./.venv-qlib313/bin/python -m py_compile cajas/reports/validation_eurusd_completed_review_progress.py cajas/scripts/build_eurusd_completed_review_progress_report.py
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

Quick manual data check:
```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd
p = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"
df = pd.read_csv(p)
print("completed rows:", len(df))
cols = [c for c in ["sample_id", "timestamp", "candidate_type", "review_status", "pattern_label", "market_context", "direction_context", "review_updated_at_utc"] if c in df.columns]
print(df[cols].tail(10).to_string(index=False))
PY
```

## Commit Requirements

If only `tmp/` reports changed:
- no commit required.

If new report code/tests/docs are added:
```bash
git add cajas/reports/validation_eurusd_completed_review_progress.py cajas/scripts/build_eurusd_completed_review_progress_report.py cajas/tests/test_validation_eurusd_completed_review_progress.py tasks/prompts/017_validate_eurusd_completed_review_progress.md
git commit -m "feat: validate EURUSD completed review progress"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash if any
- Files changed
- Completed count
- Pending count
- Completion ratio
- CSV schema status
- JSONL audit status
- Duplicate sample IDs
- Missing required fields
- Invalid rows/events
- Latest review timestamp
- Report artifact paths
- Next action
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command if commit created

## Hard Boundaries

Do not:
- reset review data
- regenerate review batch
- delete completed CSV/JSONL
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
