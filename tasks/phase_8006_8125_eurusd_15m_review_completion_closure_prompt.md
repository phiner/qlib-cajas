# Phase 8006-8125 — EURUSD 15m Review Completion Closure After GUI Persistence Fix

## Context

We are working directly on `main` for the Qlib Base / `qlib-cajas` project.

Recent completed fixes:
- Commit `141f344d`: hardened CSV/JSONL review persistence.
- Commit `eb8d40cc`: fixed GUI Save-and-Next runtime regression.
- Save and Save-and-Next now use canonical CSV-first + JSONL-audit persistence path.
- CSV remains authoritative latest state by `sample_id`.
- JSONL remains append-friendly audit history.
- SQLite remains explicitly deferred.
- Work is directly on `main`.
- Do not create branches, do not push automatically, do not merge automatically.

Current `git status --short` from prior report:
```text
?? tasks/phase_7646_7765_eurusd_15m_csv_jsonl_persistence_hardening_prompt.md
?? tasks/phase_7886_8005_eurusd_15m_gui_persistence_runtime_fix_prompt.md
```

These prompt files should either be committed as phase archive prompts or intentionally removed if they are local-only duplicates. Prefer committing them if they are useful roadmap/task history.

## Objective

Resume the interrupted review completion closure work, now that GUI persistence runtime behavior is fixed.

Build a robust closure validation/report layer that answers:

1. How many EURUSD 15m review samples are completed?
2. Which samples are still pending?
3. Are completed CSV rows schema-valid?
4. Does JSONL audit history exist and match completed CSV expectations?
5. Are there duplicate or conflicting audit events?
6. Is the current batch ready for summary/analysis?
7. What exact next action should the reviewer take?

## Required Scope

Inspect/update as needed:

- `cajas/research/eurusd_pattern_review_gui.py`
- existing EURUSD review completion/feedback/summary modules
- `cajas/reports/*eurusd*review*completion*.py` if present
- `cajas/scripts/*eurusd*review*completion*.py` if present
- `cajas/tests/test_eurusd_pattern_review_gui.py`
- EURUSD review readiness tests
- docs:
  - `cajas/docs/eurusd_pattern_research_kickoff.md`
  - `cajas/README.md`
  - `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Do not introduce SQLite.

## Implementation Requirements

### 1. Commit or clean prompt archive files

Handle:

```text
tasks/phase_7646_7765_eurusd_15m_csv_jsonl_persistence_hardening_prompt.md
tasks/phase_7886_8005_eurusd_15m_gui_persistence_runtime_fix_prompt.md
```

Preferred:
- Add them to git as task archive prompts if they are meaningful and not duplicates.
- If they are generated duplicates with no value, remove them and report why.

Do not leave unrelated untracked files at final status.

### 2. Add or harden review completion closure report

The report should read:
- batch CSV path, usually `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- completed CSV path, usually `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- audit JSONL path, if available

Output artifacts should follow existing project conventions, for example:

```text
tmp/validation-eurusd-pattern-review-completion-closure.json
tmp/validation-eurusd-pattern-review-completion-closure.md
```

If an equivalent report already exists, extend it rather than duplicating.

Report fields should include:
- `status`
- `review_state`
- `blocking`
- `batch_path`
- `completed_csv_path`
- `audit_jsonl_path`
- `batch_count`
- `completed_count`
- `pending_count`
- `completion_ratio`
- `completed_sample_ids`
- `pending_sample_ids`
- `duplicate_completed_sample_ids`
- `missing_required_review_fields`
- `invalid_review_rows`
- `jsonl_event_count`
- `jsonl_unique_sample_count`
- `jsonl_samples_without_completed_csv`
- `completed_csv_samples_without_jsonl`
- `latest_review_updated_at_utc`
- `next_action`

Suggested status semantics:
- `awaiting_review_input`: no completed rows yet.
- `in_progress`: some completed, some pending.
- `ready_for_summary`: all required batch rows completed and schema-valid.
- `warning`: CSV is usable but JSONL audit has gaps or append warnings.
- `blocked`: completed CSV is unreadable, missing required identity fields, or has severe schema errors.

### 3. Schema and required-field validation

Validate completed CSV has:
- `sample_id`
- required review fields from the current review schema
- `review_updated_at_utc`

Do not require optional notes to be non-empty.

Reject or warn on:
- missing `sample_id`
- duplicate `sample_id` rows in completed CSV
- missing required review fields
- forbidden trading/action columns
- invalid score values outside allowed ranges
- invalid enum values if enumerations already exist

### 4. JSONL audit comparison

If JSONL exists:
- parse line by line
- count valid events
- capture malformed lines as warnings/errors
- compare JSONL sample ids to completed CSV sample ids
- confirm each completed sample has at least one audit event where possible
- allow multiple events per sample because updates are append-friendly

If JSONL is missing:
- if completed CSV exists from older flow, report warning, not automatic failure, unless current docs say JSONL is mandatory.
- next action should be to continue using fixed GUI so future saves append audit events.

### 5. Integrate into EURUSD research readiness

Update readiness report so it summarizes:
- GUI status
- persistence status
- completion closure status
- completed/pending counts
- next recommended action

If not all samples are complete:
- readiness should remain suitable for pattern research / review, but next action should be `continue_human_review`.

If all samples are complete and valid:
- next action should be `run_review_summary`.

### 6. Tests

Add/update tests for:
1. Empty/missing completed CSV -> `awaiting_review_input`
2. Partial completed CSV -> `in_progress`
3. Full completed CSV with valid JSONL -> `ready_for_summary`
4. Full completed CSV with missing JSONL -> `warning` or documented non-blocking warning
5. Duplicate completed sample ids -> warning/blocking depending on severity
6. Missing required field -> blocked
7. Malformed JSONL line -> warning/blocking depending on severity
8. Completed sample without JSONL audit -> warning
9. JSONL sample not in batch/completed -> warning
10. Readiness integration reflects closure next action

Keep tests deterministic and small.

## Validation Commands

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run any new report-specific tests, for example:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_pattern_review_completion_closure.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py
```

Compile any new/changed report/script/test files.

Run report generation commands for real artifacts, adjusting names to actual scripts:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_eurusd_pattern_review_completion_closure.py
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py
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

## Commit Requirements

Work directly on `main`.

Create one or more commits as appropriate, for example:

```bash
git add cajas tests tasks
git commit -m "add EURUSD review completion closure"
```

If committing prompt archive files separately:

```bash
git add tasks/phase_7646_7765_eurusd_15m_csv_jsonl_persistence_hardening_prompt.md tasks/phase_7886_8005_eurusd_15m_gui_persistence_runtime_fix_prompt.md
git commit -m "docs: archive EURUSD GUI persistence prompts"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash(es)
- Files changed
- What happened to the two untracked prompt files
- Completion closure status
- Completed count
- Pending count
- JSONL audit status
- Readiness next action
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries

Do not:
- add SQLite
- create branches
- push automatically
- merge automatically
- train models
- produce trading signals/orders
- modify Qlib core
- delete completed review data
