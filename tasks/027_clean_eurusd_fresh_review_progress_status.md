# 027 — Clean Up EURUSD Fresh-Start Review Progress Status

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current state after explicit full-range reset/rebuild:
- Active review batch exists:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- Completed review files were intentionally removed to restart:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl`
- This is a valid fresh-start state.

Current completed review progress report output:

```json
{
  "batch_count": 100,
  "completed_count": 0,
  "pending_count": 100,
  "status": "awaiting_review_input",
  "reason": "completed_csv_missing",
  "blocking": false,
  "csv_schema_status": "blocked",
  "jsonl_audit_status": "blocked"
}
```

Problem:
- Top-level status is correct: `awaiting_review_input`.
- `blocking=false` is correct.
- But nested statuses `csv_schema_status=blocked` and `jsonl_audit_status=blocked` are misleading and messy in a normal fresh-start state.

Desired:
- Fresh start should be clean and non-blocking everywhere.
- Missing completed CSV/JSONL before any review exists should not be labeled blocked.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- Do not reset or regenerate batch.
- Do not delete completed CSV/JSONL.
- CSV/JSONL only; no SQLite.
- No model training, no trading signals/orders, no Qlib core changes.

## Objective

Clean up completed review progress report semantics for fresh-start state.

When batch exists but completed CSV/JSONL do not exist yet:
- status should be `awaiting_review_input`
- blocking should be `false`
- csv_schema_status should be `not_applicable` or `awaiting_review_input`
- jsonl_audit_status should be `not_applicable` or `awaiting_review_input`
- next_action should be `begin_human_review` or `continue_human_review`
- no nested field should imply corruption/blocking.

## Required Behavior

### 1. Fresh-start status semantics

If:
```text
batch CSV exists and is readable
completed CSV does not exist
events JSONL does not exist
```

Then output:

```json
{
  "status": "awaiting_review_input",
  "reason": "completed_csv_missing",
  "blocking": false,
  "batch_count": 100,
  "completed_count": 0,
  "pending_count": 100,
  "completion_ratio": 0.0,
  "csv_schema_status": "not_applicable",
  "jsonl_audit_status": "not_applicable",
  "csv_jsonl_value_compare": "not_applicable",
  "preliminary_summary_status": "not_applicable",
  "next_action": "begin_human_review"
}
```

Acceptable alternative:
```text
csv_schema_status = awaiting_review_input
jsonl_audit_status = awaiting_review_input
```

Choose one and keep it consistent across JSON/MD/tests.

Preferred:
```text
not_applicable
```

because no completed rows exist to validate.

### 2. Distinguish real missing batch from missing completed file

If batch CSV is missing:
- status can be `blocked`
- reason should be `batch_csv_missing`
- blocking should be `true`
- csv/jsonl statuses may be `not_evaluated` or `blocked`

If batch CSV exists but completed CSV is missing:
- status must not be blocked.

### 3. Markdown report cleanup

Update `tmp/validation-eurusd-completed-review-progress.md` generation so it reads cleanly.

Suggested text:

```text
Status: awaiting_review_input
Completed: 0 / 100
CSV schema: not_applicable (no completed review rows yet)
JSONL audit: not_applicable (no review events yet)
Next action: begin_human_review
```

Avoid scary wording like:
```text
blocked
corrupt
missing required fields
```
for fresh-start no-review state.

### 4. Readiness integration cleanup

If EURUSD research readiness consumes the progress report:
- make sure fresh-start `not_applicable` statuses do not make readiness blocked.
- readiness next action should remain:
  - `begin_human_review`
  - or `continue_human_review`

### 5. Tests

Update/add tests in:

```text
cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Required tests:
1. Batch exists, completed CSV missing, JSONL missing:
   - status `awaiting_review_input`
   - blocking false
   - completed_count 0
   - pending_count equals batch_count
   - csv_schema_status `not_applicable`
   - jsonl_audit_status `not_applicable`
   - next_action `begin_human_review` or documented equivalent

2. Batch missing:
   - status blocked
   - reason `batch_csv_missing`
   - blocking true

3. Completed CSV exists with rows:
   - existing validation behavior preserved
   - schema/jsonl statuses still validate normally

4. Readiness integration if applicable:
   - fresh-start progress does not block readiness
   - next action remains human review

## Validation Commands

Run report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Inspect JSON:

```bash
cat tmp/validation-eurusd-completed-review-progress.json
```

Expected fresh-start fields:
```text
status=awaiting_review_input
blocking=false
completed_count=0
pending_count=100
csv_schema_status=not_applicable
jsonl_audit_status=not_applicable
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Run readiness tests if touched:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_research_readiness.py
```

Run relevant GUI/review tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/reports/validation_eurusd_completed_review_progress.py cajas/scripts/build_eurusd_completed_review_progress_report.py
```

Compile any other changed Python files.

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

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas tasks
git commit -m "fix: clean EURUSD fresh review progress status"
```

Since task markdown files can be committed, include this prompt if saved under `tasks/`.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Fresh-start status behavior
- CSV schema status behavior
- JSONL audit status behavior
- Batch-missing behavior
- Readiness integration status if touched
- Generated report result
- Validation command results
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
- delete completed CSV/JSONL
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
