# 028 — Add EURUSD Bad Sample Rejection and Permanent Exclude Workflow

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review workflow:
- GUI review app works.
- CSV/JSONL persistence works.
- Review batch was reset/rebuilt from full-range sampling.
- User is actively reviewing the first full-range batch of 100.
- Some samples are clearly unsuitable or low-value.
- User wants a way to delete/remove/mark a sample as unsuitable and permanently avoid it.

User request:
- Add functionality so the reviewer can mark a sample as inappropriate / unsuitable / permanently abandoned.
- The system should remember this and avoid showing/selecting the sample again.
- Do not require the user to manually edit CSV files.
- Do not hard-delete raw data or candidate data.

Important:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- Do not train models.
- Do not create trading signals/orders.
- Do not modify Qlib core.
- Do not delete raw/clean/candidate files.
- Do not reset or regenerate active batch unless explicitly requested later.

## Objective

Implement a safe bad-sample rejection workflow:

1. User can mark current sample as unsuitable from the GUI.
2. Rejection is persisted durably in CSV/JSONL.
3. Rejected samples are skipped by default in GUI navigation/review.
4. Rejected samples are excluded from future batch/replacement generation.
5. Reports summarize rejection counts and reasons.
6. No raw data is deleted.

## Design Principles

Do not physically delete rows from:
- raw data
- clean view
- candidate pack
- active batch CSV

Instead maintain an explicit reject/exclude registry.

Default files:

```text
tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples.csv
tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples_events.jsonl
```

Optional report:

```text
tmp/validation-eurusd-rejected-samples.json
tmp/validation-eurusd-rejected-samples.md
```

## Required GUI Behavior

### 1. Add “Reject / Exclude Sample” action

Add a visible but safe control near review buttons or in an “Advanced”/“Bad Sample” area.

Suggested button text:

```text
Reject Sample
```

or:

```text
Mark Bad Sample
```

Behavior:
- Writes current sample to reject registry.
- Does not delete raw data.
- Does not delete completed CSV/JSONL.
- After successful reject, automatically navigates to next non-rejected sample.
- Shows a one-shot toast/notice:
  `Rejected eurusd15m_xxxxxx → skipped from future review`

### 2. Add rejection reason dropdown

Add required or optional reason field.

Recommended reasons:

```text
bad_context
duplicate_region
weekend_gap
market_closed_gap
unclear_chart
bad_candidate
too_close_to_existing_sample
data_quality_issue
not_useful_for_research
other
```

Definitions:
- `bad_context`: Chart window/context not suitable for review.
- `duplicate_region`: Same local region already reviewed or too repetitive.
- `weekend_gap`: Weekend gap makes structure unsuitable.
- `market_closed_gap`: Market-closed gap / discontinuity.
- `unclear_chart`: Too hard to judge visually.
- `bad_candidate`: Candidate is not meaningful enough to spend review time.
- `too_close_to_existing_sample`: Near duplicate of an already reviewed sample.
- `data_quality_issue`: Suspicious data/anomaly.
- `not_useful_for_research`: Low research value.
- `other`: Reviewer notes explain.

### 3. Add rejection notes

Add small optional notes text for rejection:

```text
Reject Notes
```

This can be Chinese, English, or mixed.

### 4. Confirmation safety

Because rejection is persistent, either:
- use a checkbox:
  `Confirm reject current sample`
or
- use a two-step button/expander area.

Keep it simple but avoid accidental rejects.

Suggested:
```text
[ ] Confirm reject current sample
[Reject Sample]
```

The button is disabled unless confirmed.

### 5. Default navigation skips rejected samples

Once a sample is rejected:
- `Next Sample` skips rejected samples by default.
- `Save and Next` after saving should also skip rejected samples.
- `Previous Sample` may either skip rejected samples or include them depending on UX; preferred default:
  - skip rejected samples
  - add optional “Include rejected samples” checkbox if feasible.

Direct `Go to Sample`:
- If user jumps directly to a rejected sample, show warning:
  `This sample is rejected/excluded.`
- Do not block direct viewing; direct jump should still be possible for audit.

### 6. Filter option

Add optional sidebar checkbox:

```text
Show rejected samples
```

Default:
```text
False
```

When false:
- navigation skips rejected samples.
- counts show rejected count.

When true:
- user can inspect rejected samples.

### 7. Interaction with completed review

If a sample has already been reviewed and then rejected:
- keep completed row unchanged for audit.
- reject registry marks it excluded.
- progress reports should count it separately:
  - reviewed_count may include it historically,
  - usable_reviewed_count should exclude it.

If rejected before review:
- completed CSV remains absent for that sample.
- pending count should exclude rejected if using “active pending” semantics.

## Persistence Requirements

### 1. Rejected samples CSV

Schema:

```text
sample_id
timestamp
candidate_type
rejection_reason
rejection_notes
rejected_at_utc
review_batch_id
source_batch_csv
reviewer_id_optional
schema_version
```

Use latest row by `sample_id` if re-rejected.

### 2. Rejected samples JSONL

Append one event per reject action:

```json
{
  "event_type": "sample_rejected",
  "sample_id": "...",
  "timestamp": "...",
  "candidate_type": "...",
  "rejection_reason": "...",
  "rejection_notes": "...",
  "rejected_at_utc": "...",
  "review_batch_id": "batch_001",
  "source_batch_csv": "...",
  "schema_version": "eurusd_15m_rejected_sample_v1"
}
```

### 3. Undo / restore

Add optional low-risk support:

```text
Unreject Sample
```

If implemented:
- append JSONL event `sample_unrejected`
- remove or mark inactive in CSV
- update navigation.

If this is too much for this phase, document manual recovery and skip undo.

Preferred for usability:
- implement `Unreject Sample` only when `Show rejected samples` is enabled or current sample is already rejected.

## Report Requirements

Create report:

```text
cajas/reports/validation_eurusd_rejected_samples.py
cajas/scripts/build_eurusd_rejected_samples_report.py
cajas/tests/test_validation_eurusd_rejected_samples.py
```

Output:
```text
tmp/validation-eurusd-rejected-samples.json
tmp/validation-eurusd-rejected-samples.md
```

Report fields:
- `status`
- `batch_count`
- `rejected_count`
- `active_rejected_count`
- `rejected_sample_ids`
- `counts_by_reason`
- `counts_by_candidate_type`
- `rejected_reviewed_count`
- `rejected_pending_count`
- `csv_status`
- `jsonl_status`
- `duplicate_reject_events`
- `malformed_event_count`
- `next_action`

Status:
- `no_rejections`
- `valid`
- `warning`
- `blocked` only for corrupt reject registry.

## Progress Report Integration

Update completed review progress report to account for rejected samples.

Add:
- `rejected_count`
- `active_reviewable_count`
- `usable_completed_count`
- `usable_pending_count`
- `rejected_sample_ids`
- `excluded_from_progress_sample_ids`

Fresh-start with rejects:
- still non-blocking.

When all non-rejected samples are reviewed:
- status can become `valid_ready_for_summary`
even if some rejected samples were skipped.

## Batch/Replacement Generation Integration

Future batch/replacement generation should exclude rejected sample IDs.

Update batch builder/diversification logic to accept:

```text
--exclude-samples-csv tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples.csv
```

Default reset/rebuild should use rejected registry if present, unless user explicitly asks to ignore it:

```text
--ignore-rejected-samples
```

For current phase:
- do not regenerate active batch.
- just wire future generation support and tests.

## Tests Required

Add/update tests.

### GUI/helper tests
1. Reject row builder:
   - creates required fields.
2. Save/update rejected CSV:
   - duplicate-safe by `sample_id`.
3. JSONL reject event append:
   - one event per reject action.
4. Navigation skips rejected samples:
   - next from index 1 skips rejected index 2.
5. Direct jump to rejected sample:
   - allowed, returns rejected status/warning.
6. Show rejected flag:
   - controls whether navigation includes rejected.

### Report tests
1. Missing reject registry:
   - `status=no_rejections`, rejected_count=0.
2. Valid rejected CSV/JSONL:
   - counts by reason/type.
3. Malformed JSONL:
   - warning.
4. Duplicate reject events:
   - latest CSV row wins, event count tracked.
5. Completed progress integration:
   - active_reviewable_count excludes rejects.
   - usable_pending_count excludes rejects.

### Batch builder tests
1. Exclude rejected sample IDs from generated batch when exclude file supplied.
2. Ignore flag includes them only if explicitly requested.

## Validation Commands

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_rejected_samples.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py
```

Run report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_rejected_samples_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Run py_compile:

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

Manual GUI smoke:

```bash
./scripts/run_eurusd_review_gui.sh
```

Manual checks:
1. Open a clearly bad sample.
2. Select rejection reason.
3. Add reject note.
4. Confirm reject checkbox.
5. Click Reject Sample.
6. Confirm toast appears once.
7. Confirm app moves to next non-rejected sample.
8. Confirm rejected CSV/JSONL updated.
9. Click Go to Sample for rejected sample.
10. Confirm warning shows it is rejected.
11. Confirm Save/Save and Next still works for normal samples.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: add EURUSD rejected sample workflow"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Reject Sample GUI behavior
- Rejection reason options
- Rejected CSV/JSONL behavior
- Navigation skip behavior
- Direct jump behavior for rejected samples
- Progress report integration
- Batch builder exclusion support
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- physically delete raw/clean/candidate data
- reset active batch
- regenerate active batch
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
