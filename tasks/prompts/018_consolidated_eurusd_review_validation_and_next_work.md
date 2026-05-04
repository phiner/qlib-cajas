# 018 — Consolidated EURUSD Review Validation, Summary, and Next-Step Closure

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m GUI/review state:
- GUI review app is functional.
- CSV/JSONL persistence is the durable storage.
- SQLite is explicitly deferred.
- Save / Save and Next / Previous / Next are implemented.
- Reset is explicit only through `./scripts/reset_eurusd_review_batch.sh`; GUI startup must never reset review data.
- Review batch diversification is implemented.
- Chart gap compression, improved framing, horizontal x labels, visible wick-safe sample marker, and adjacent guide line are implemented.
- User has manually reviewed about 21 samples and wants the remaining near-term checks/tasks bundled together.

Important user instruction:
- Do not ask the user to manually run many individual commands.
- Automate what can be automated.
- Do a consolidated pass over the remaining review/validation/reporting tasks.
- Do not reset or regenerate samples unless explicitly requested.
- Do not delete completed review CSV/JSONL.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- Do not merge automatically.
- Do not add SQLite.
- Do not train models.
- Do not create trading signals/orders.
- Do not modify Qlib core.
- Do not delete completed review data.
- Do not reset batch.
- Do not regenerate review batch.

## Objective

Perform a consolidated post-review progress and workflow-health pass covering validation, reporting, GUI sanity, documentation, and next-action readiness.

This should replace a dozen small follow-up tasks with one focused implementation/review cycle.

## Scope Summary

Complete the following task bundle:

1. Validate completed review progress.
2. Validate completed CSV schema.
3. Validate JSONL audit history.
4. Compare completed CSV and JSONL sample coverage.
5. Produce current review progress report artifacts.
6. Produce preliminary human-review summary from completed rows.
7. Summarize candidate-type coverage in reviewed vs pending samples.
8. Summarize note/status/score distributions.
9. Integrate review progress into EURUSD research readiness.
10. Run GUI non-destructive smoke / source checks.
11. Clean and update task prompt/roadmap docs.
12. Run validations and leave repo clean.

## Required Data Files

Default paths:

```text
batch_csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
completed_csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
events_jsonl=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl
```

Do not alter these files except by reading them for reports.

## Task 1 — Completed Review Progress Validation

Create or reuse a read-only report that checks:

- `batch_count`
- `completed_count`
- `pending_count`
- `completion_ratio`
- `completed_sample_ids`
- `pending_sample_ids`
- `latest_review_updated_at_utc`
- `next_action`

Expected current state:
- `completed_count` should be around 21.
- If actual count differs, report actual count, do not fail automatically.

Output artifacts:

```text
tmp/validation-eurusd-completed-review-progress.json
tmp/validation-eurusd-completed-review-progress.md
```

Suggested status:
- `valid_in_progress` if completed rows are valid and pending rows remain.
- `valid_ready_for_summary` if all rows are complete and valid.
- `warning` if usable but JSONL/minor gaps exist.
- `blocked` only for severe corruption.

Expected next action for partial progress:
```text
continue_human_review
```

## Task 2 — Completed CSV Schema Validation

Validate completed CSV includes required identity fields:

```text
sample_id
timestamp
candidate_type
```

Validate current review fields, using actual schema names in repo. Likely fields include:

```text
pattern_label
market_context
direction_context
review_status
structure_quality
follow_through_quality
review_confidence
review_notes
review_updated_at_utc
```

Notes may be blank.

Check:
- no duplicate `sample_id`
- every completed `sample_id` exists in batch
- no forbidden trading/action columns
- score fields within allowed range
- enum fields valid if enum schema exists
- no unreadable rows

## Task 3 — JSONL Audit Validation

Validate events JSONL line by line.

Report:
- `jsonl_event_count`
- `jsonl_valid_event_count`
- `jsonl_malformed_line_count`
- `jsonl_unique_sample_count`
- `completed_without_jsonl`
- `jsonl_without_completed`
- `jsonl_without_batch`

Allow multiple JSONL events per sample.

If JSONL exists but has extra historical events for samples not currently completed, report as warning, not destructive error.

## Task 4 — CSV vs JSONL Consistency

If JSONL event payload includes current review values:
- compare latest event per sample against completed CSV for key review fields.
- report mismatches as warnings.

If payload shape is not stable enough:
- report `csv_jsonl_value_compare=skipped_payload_shape_not_stable`.

Do not rewrite either file.

## Task 5 — Preliminary Human Review Summary

Create a read-only preliminary summary from completed rows.

Output artifacts:

```text
tmp/validation-eurusd-review-summary-current.json
tmp/validation-eurusd-review-summary-current.md
```

Include:
- reviewed count
- counts by `candidate_type`
- counts by `pattern_label`
- counts by `market_context`
- counts by `direction_context`
- counts by `review_status`
- score summaries for structure/follow-through/confidence
- note coverage:
  - blank notes count
  - nonblank notes count
  - simple keyword counts if easy:
    - `weekend gap`
    - `market closed`
    - `unclear`
    - `bad sample`
    - `good wick`
    - Chinese terms if present:
      - `周末`
      - `跳空`
      - `不清楚`
      - `趋势`
      - `影线`

This is for human QA only, not model training.

## Task 6 — Reviewed vs Pending Coverage

Produce coverage summary comparing completed vs pending batch samples.

Include:
- completed candidate_type distribution
- pending candidate_type distribution
- completed date coverage
- pending date coverage
- completed unique days
- pending unique days
- completed first/last timestamp
- pending first/last timestamp

Flag if reviewed samples are too concentrated:
- `coverage_status=ok` if reviewed rows span multiple days/types.
- `coverage_status=watch` if they are still concentrated.

Do not reorder or regenerate batch.

## Task 7 — EURUSD Research Readiness Integration

Update existing readiness report integration so it can include current completed-review progress.

Readiness should summarize:
- review progress status
- completed_count
- pending_count
- completion_ratio
- csv_schema_status
- jsonl_audit_status
- preliminary_summary_status
- next recommended action

For partial review:
```text
next_action=continue_human_review
```

If all rows are completed and valid:
```text
next_action=run_full_review_summary
```

## Task 8 — GUI Non-Destructive Smoke / Source Checks

Do not automate destructive GUI actions.

Run static/non-destructive checks:
- GUI launcher does not call reset.
- GUI app default batch path points to batch_001.
- reset script is explicit only.
- Save/status code still references CSV/JSONL.
- chart marker/framing/gap helpers remain imported and tested.

Command examples:

```bash
rg -n "reset_eurusd_review_batch" scripts/run_eurusd_review_gui.sh cajas/apps/eurusd_pattern_review_app.py
rg -n "EURUSD_15m_pattern_review_batch_001" scripts/run_eurusd_review_gui.sh cajas/apps/eurusd_pattern_review_app.py
```

Only run browser GUI manually if environment supports it; otherwise report not run.

## Task 9 — Prompt and Docs Cleanup

Ensure prompt numbering remains simple:

```text
tasks/prompts/001_*.md
tasks/prompts/002_*.md
...
```

Check:
- no stray root-level `tasks/phase_*.md`
- no stale root-level `tasks/00*.md` outside `tasks/prompts/`
- current prompt `018_...` should be stored under `tasks/prompts/` if committed

Update:
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/README.md` if needed

Docs should state:
- normal GUI launch is non-destructive
- explicit reset is destructive and user-triggered
- completed review validation command
- summary/report artifact paths
- current next action

## Task 10 — Add One-Command Validation Script If Useful

If not already present, add a convenience script:

```text
scripts/validate_eurusd_review_progress.sh
```

Behavior:
- read-only
- runs completed progress report
- runs current review summary report
- runs readiness report
- prints concise terminal summary
- does not modify completed CSV/JSONL
- does not reset or regenerate batch

Expected user command:

```bash
./scripts/validate_eurusd_review_progress.sh
```

Optional flags:
```text
--skip-fast-validation
--json-only
```

Keep it simple.

## Task 11 — Tests

Add or update tests for any new report/script.

Suggested new tests:
- `test_validation_eurusd_completed_review_progress.py`
- `test_validation_eurusd_review_summary_current.py`
- or extend existing completion/summary tests if they already exist.

Test cases:
1. Missing completed CSV -> `awaiting_review_input` or warning.
2. Valid partial completed CSV -> `valid_in_progress`.
3. Duplicate sample IDs -> blocked or warning according to severity.
4. Completed sample not in batch -> blocked/warning.
5. Valid JSONL with multiple events per sample -> pass.
6. Malformed JSONL line -> warning/blocking according to severity.
7. Completed CSV sample without JSONL -> warning.
8. Summary distributions are deterministic.
9. Readiness integration reflects `continue_human_review`.
10. Convenience script dry/static behavior if script added.

## Task 12 — Validation Commands

Run focused report tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Run summary tests if added:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_review_summary_current.py
```

Run relevant existing tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_research_readiness.py
```

Run report generation:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_review_summary_current_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_research_readiness_report
```

Adjust names if existing scripts use different names.

Run py_compile for changed Python:

```bash
./.venv-qlib313/bin/python -m py_compile <changed-python-files>
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

Run quick data print:

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

If new source/tests/docs/scripts are added, commit them.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: validate EURUSD review progress"
```

If only generated `tmp/` reports changed:
- no commit required.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash if any
- Files changed
- Report artifacts created
- Completed count
- Pending count
- Completion ratio
- CSV schema status
- JSONL audit status
- CSV/JSONL consistency status
- Duplicate sample IDs
- Missing required fields
- Invalid rows/events
- Candidate type coverage
- Note/status/score summary
- Readiness status
- Next action
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command if commit created:

```bash
git push origin main
```

## Hard Boundaries Reminder

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
