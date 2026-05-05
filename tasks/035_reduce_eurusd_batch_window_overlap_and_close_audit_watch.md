# 035 — Reduce EURUSD Batch Window Overlap and Close Candidate Audit Watch Item

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current status after commit:
- `fd4d9433cf316b01f8330e5078bf7c90cab5f5c9`
- Candidate audit moved from `blocked` to `watch`.
- Must-fix gate failures are empty.
- Remaining should-fix watch item:
  ```text
  window_overlap_max_ratio_above_threshold
  ```
- Active batch was rebuilt and currently has:
  - 100 rows
  - years `[2020, 2021, 2022, 2023, 2024, 2025]`
  - first20 unique days = 19
  - trend rows with `excluded_late_reversal_anchor=true`: 0
- Exact duplicate IDs and same-timestamp duplicate rows are 0.
- Remaining issue is visual/window overlap concentration above the threshold.

Known risk:
- `./scripts/reset_eurusd_review_batch.sh --backup-old` did not complete cleanly in the previous run.
- Equivalent rebuild was completed manually.
- Reset script should be fixed so future rebuilds are one-command and reliable.

Untracked task prompt files:
```text
tasks/033_close_eurusd_candidate_audit_warnings_and_hardening.md
tasks/034_rebuild_artifacts_to_close_candidate_audit_gates.md
```

User preference:
- Task markdown under `tasks/` can be committed.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training, no trading signals/orders, no Qlib core changes.

## Objective

Close or reduce the remaining candidate-audit `watch` item related to excessive window overlap in the active batch, and harden the reset script so future rebuilds do not require manual equivalent steps.

Target outcome:
- candidate audit status becomes `pass` if realistic,
- or remains `watch` only with a documented, justified non-blocking overlap item below an agreed severity threshold.
- reset script completes cleanly.
- active batch remains full-range and trend-quality gates remain clean.

## Required Work

### 1. Inspect current overlap warning

Read:

```text
tmp/validation-eurusd-candidate-audit.json
tmp/validation-eurusd-candidate-audit-warning-inventory.json
tmp/validation-eurusd-pattern-review-batch-001.json
tmp/validation-eurusd-pattern-review-batch-001.md
```

Identify:
- exact warning id(s)
- current max window overlap
- affected sample pairs/groups
- affected candidate types
- whether overlap occurs mostly within same candidate_type or cross-type
- whether affected rows are in first20/first30 or later
- current threshold value

Create/update a concise diagnostic section in the audit markdown if not present.

### 2. Strengthen batch diversification for visible-window overlap

The batch builder should avoid high-overlap samples when enough alternatives exist.

Use/confirm defaults:

```text
window_bars = 120
pre_context_ratio = 0.6
window_overlap_max_ratio = 0.35
same_region_cooldown_bars = 48
anchor_duplicate_gap_bars = 8
```

Enhance selection logic so candidate acceptance checks:
- exact sample_id not already selected
- timestamp not already selected
- anchor distance >= min gap where possible
- same-region cooldown respected where possible
- visible-window overlap with selected samples <= threshold where possible
- candidate_type balance still respected
- full-range/year coverage still respected

If constraints conflict, fallback is allowed only with explicit metadata:
```text
fallback_reason
fallback_window_overlap=true
fallback_overlap_ratio
```

### 3. Add deterministic overlap diagnostics to batch report

Ensure batch report includes:

```text
window_overlap_max_ratio_threshold
max_window_overlap_ratio
window_overlap_warning_count
window_overlap_duplicate_groups
fallback_window_overlap_count
first20_max_window_overlap
first30_max_window_overlap
```

For each flagged overlap group:
```text
sample_id_a
sample_id_b
timestamp_a
timestamp_b
candidate_type_a
candidate_type_b
overlap_ratio
anchor_gap_bars
```

### 4. Fix reset script reliability

Investigate why:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

did not complete cleanly previously.

Run it in a controlled way after code fixes.

The script must:
- backup old active artifacts
- rebuild candidate pack
- rebuild review template
- rebuild active batch
- run/report source range
- run completed progress
- run rejected report
- write reset report
- exit nonzero on real failure
- not be tied to GUI startup

If the failure was due to missing args, wrong CLI call style, stale path, or report status handling, fix it.

Add/adjust tests or shell `bash -n` checks as appropriate.

### 5. Rebuild active batch if batch selection logic changed

If batch builder logic changes, explicitly rebuild:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

This is allowed because the user is currently before restarting review and wants audit issues fixed first.

After rebuild:
- completed progress should be fresh:
  ```text
  status=awaiting_review_input
  completed_count=0
  pending_count=100
  blocking=false
  ```

### 6. Re-run audit reports

Run:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_warning_inventory
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_hardening_roadmap
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Expected:
- no must-fix gate failures
- causality/explainability columns present
- selected-row explainability passes
- trend-quality gates pass
- source range full-range/non-truncated
- overlap warning improved or resolved

### 7. Acceptance criteria

Preferred final status:
```text
candidate_audit_status=pass
```

Acceptable final status:
```text
candidate_audit_status=watch
```

only if:
- overlap issue is reduced,
- affected pairs are documented,
- no first20/first30 severe overlap,
- fallback reasons are explicit,
- no must-fix gates fail,
- docs state it is non-blocking.

Not acceptable:
```text
blocked
needs_rule_refinement
```

unless a clear source-level issue remains and a new prompt is generated.

### 8. Tests Required

Add/update tests for:

1. Window overlap calculation:
   - overlapping windows above threshold detected.
   - non-overlapping windows pass.

2. Batch builder avoids overlap:
   - synthetic candidate pool has enough alternatives.
   - selected batch max overlap <= threshold.

3. Graceful fallback:
   - when pool is too small, batch fills with fallback metadata.

4. Batch report metrics:
   - emits max overlap, group details, first20/first30 metrics.

5. Candidate audit status:
   - overlap above threshold triggers `watch` or should-fix gate.
   - overlap within threshold allows `pass` if other gates pass.

6. Reset script reliability:
   - at minimum `bash -n scripts/reset_eurusd_review_batch.sh`.
   - if test framework supports subprocess smoke, add dry-run test.

7. Existing tests still pass:
   - candidate audit
   - hardening reports
   - candidate pack
   - trend segments
   - review batch
   - GUI/review
   - rejected samples
   - completed progress

### 9. Validation Commands

Run reset script syntax:

```bash
bash -n scripts/reset_eurusd_review_batch.sh
```

Run explicit reset/rebuild if selection logic changed:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_candidate_hardening_reports.py \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_sampling_source_range.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_rejected_samples.py
```

Run GUI tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py
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

### 10. Commit Requirements

Commit all source/test/docs/task changes on `main`.

Include untracked task prompt files as allowed:

```text
tasks/033_close_eurusd_candidate_audit_warnings_and_hardening.md
tasks/034_rebuild_artifacts_to_close_candidate_audit_gates.md
tasks/035_reduce_eurusd_batch_window_overlap_and_close_audit_watch.md
```

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "fix: reduce EURUSD batch overlap audit warning"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Initial overlap warning details
- Batch overlap changes
- Reset script fix
- Whether active batch was rebuilt
- Backup directory if rebuilt
- Final candidate audit status
- Remaining warning inventory
- Source range status
- Completed progress status
- New batch coverage
- Window overlap metrics
- Trend candidate quality status
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- push automatically
- create branches
- add SQLite
- train models
- produce trading signals/orders
- modify Qlib core
- use future-aware review filters as live candidate logic
- reset automatically on GUI startup
