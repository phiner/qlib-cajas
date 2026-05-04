# 032 — Audit EURUSD Candidate Causality, Selection Explainability, Multi-Label Conflicts, and Coverage

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m research/review workflow:
- Raw EURUSD 15m data is available across 2020–2025.
- GUI review workflow is implemented with CSV/JSONL persistence.
- Full-range reset/rebuild exists.
- Rejected/bad-sample registry exists.
- Review schema v2 exists.
- Candidate generation was improved with segment-aware trend candidates.
- Segment-aware logic avoids selecting trend-end anchors followed by immediate reversal.
- User wants to think deeper before continuing large-scale review.

Important concern:
Some candidate filters / review sampling filters may use future bars. That can be acceptable for selecting better human-review samples or evaluating follow-through, but it must never be confused with causal candidate logic or future live signal logic.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- Do not reset active review data unless explicitly requested separately.
- Do not regenerate active batch destructively in this task.
- Do not delete completed/rejected CSV/JSONL.
- Do not train models.
- Do not create trading signals/orders.
- Do not modify Qlib core.

## Objective

Add an audit layer that makes EURUSD candidate/review sampling safer and more explainable before the user continues reviewing many samples.

The audit should cover:

1. Candidate causality and future-bar usage.
2. Candidate selection explainability.
3. Multi-label / same-timestamp candidate conflicts.
4. Review batch duplicate/multi-candidate overlap.
5. Coverage across year/month/day/hour/session/volatility buckets.
6. Clear separation between:
   - causal candidate logic,
   - non-causal review-sampling quality filters,
   - human label/follow-through evaluation.

This task should produce reports and tests. It should not reset/rebuild the active batch unless the user separately asks.

## Core Definitions

### 1. Candidate generation

Candidate generation should ideally be causal unless explicitly marked otherwise:

```text
causal_candidate=true
uses_future_bars=false
future_bars_used=0
```

Example:
- slope-based candidate using only bars up to sample timestamp can be causal.
- rule using post-sample rebound/selloff is not causal.

### 2. Review sampling quality filter

A review sampling quality filter may use future bars to avoid low-quality human-review examples.

Example:
- excluding a short-trend-down anchor if the next 4 bars rebound strongly.

This is acceptable only if clearly marked:

```text
used_for_review_sampling=true
causal_candidate=false or candidate_filter_uses_future_bars=true
uses_future_bars=true
future_bars_used=4
not_for_live_signal=true
```

### 3. Human labels / follow-through

Human review labels may look at future bars. That is label/evaluation information, not candidate signal input.

Example:
```text
follow_through_quality=4
```

This is non-causal label/evaluation metadata.

## Required Work

## Task 1 — Add Causality Metadata to Candidate Outputs

Extend candidate pack output with explicit causality metadata columns where applicable:

```text
causal_candidate
uses_future_bars
future_bars_used
future_usage_role
not_for_live_signal
candidate_logic_window
review_filter_window
label_window
```

Suggested semantics:

```text
causal_candidate: bool
uses_future_bars: bool
future_bars_used: int
future_usage_role: none | review_sampling_filter | label_evaluation | audit_only
not_for_live_signal: bool
candidate_logic_window: e.g. "past_only"
review_filter_window: e.g. "next_4_bars" or ""
label_window: e.g. "human_visible_forward_context" or ""
```

For current segment-aware late/rebound filtering:
- If rebound filter uses next bars to exclude/downrank candidates:
  - mark the resulting metadata/report clearly as review sampling / quality filter.
  - Do not present it as causal signal logic.

If candidate rows retained are causal but filtered by future-aware review filter, use separate fields:

```text
causal_candidate=true
candidate_logic_uses_future_bars=false
review_filter_uses_future_bars=true
review_filter_future_bars_used=4
```

If this split is clearer, implement it instead of a single `uses_future_bars`.

Preferred explicit columns:

```text
candidate_logic_uses_future_bars
candidate_logic_future_bars_used
review_filter_uses_future_bars
review_filter_future_bars_used
label_uses_future_bars
not_for_live_signal
```

## Task 2 — Add Candidate Selection Explainability

Every candidate selected into the candidate pack/review template should have enough metadata to answer:

```text
Why this candle?
```

Add or standardize fields:

```text
candidate_reason_codes
selection_reason_codes
exclusion_reason_codes
segment_reason_codes
review_sampling_reason_codes
primary_selection_reason
```

For segment-aware trend candidates:
- `segment_representative`
- `segment_midpoint_anchor`
- `same_segment_duplicate_suppressed`
- `late_segment_anchor`
- `rebound_after_anchor`
- `excluded_late_reversal_anchor`
- `preferred_review_candidate`

For non-trend candidates:
- keep existing reason codes, but add `primary_selection_reason`.

Report missing explainability fields:
- candidate rows without reason codes
- selected review samples without selection reason
- trend samples without segment metadata

## Task 3 — Audit Multi-Label / Same-Timestamp Conflicts

Detect when multiple candidate types fire on the same timestamp or near the same anchor.

Create fields/report:

```text
same_timestamp_candidate_type_count
same_timestamp_candidate_types
primary_candidate_type
multi_candidate_timestamp
```

Rules:
- Same timestamp with multiple candidate types is not automatically bad.
- It should be visible and explainable.
- Review batch should avoid showing the same timestamp multiple times unless intentionally allowed.

Report:
- count of timestamps with multiple candidate types
- max candidate types on one timestamp
- top multi-candidate timestamps
- how many review batch rows are from multi-candidate timestamps
- whether any same timestamp appears multiple times in active batch

Optional future behavior:
- choose primary candidate type per timestamp for review batch
- preserve all types in `candidate_type_list`

Do not destructively rewrite active batch in this task.

## Task 4 — Audit Near-Duplicate and Same-Region Sampling

Build on duplicate detection if task 024 exists; otherwise implement minimal audit.

Report:
- exact duplicate sample IDs
- same timestamp duplicates
- anchor-near duplicates
- same-region duplicates
- high window-overlap duplicate groups

Use default thresholds:
```text
anchor_duplicate_gap_bars = 8
same_region_cooldown_bars = 48
window_overlap_max_ratio = 0.35
window_bars = 120
pre_context_ratio = 0.6
```

For active batch:
- report duplicates, but do not reset or modify batch.

## Task 5 — Audit Coverage Across Time and Market Conditions

Add coverage metrics for candidate pack, review template, and active batch.

Coverage dimensions:
```text
year
month
weekday
hour_of_day_utc
session_bucket
volatility_bucket
candidate_type
```

Session buckets for UTC:
- `asia`
- `london`
- `new_york`
- `overlap`
- `off_hours`

Use a simple deterministic definition. Example:
```text
asia: 00:00–07:00 UTC
london: 07:00–12:00 UTC
overlap: 12:00–16:00 UTC
new_york: 16:00–21:00 UTC
off_hours: 21:00–24:00 UTC
```

Volatility bucket:
- derive from local candle range or rolling range.
- simple quantile buckets are fine:
  - `low`
  - `medium`
  - `high`

Report:
- counts by year/month/session/volatility/candidate_type
- missing coverage warnings
- first20/first30 coverage for active batch
- whether active batch is over-concentrated in one year/session/volatility bucket

## Task 6 — Add Audit Report

Create report module/CLI:

```text
cajas/reports/validation_eurusd_candidate_audit.py
cajas/scripts/build_eurusd_candidate_audit_report.py
cajas/tests/test_validation_eurusd_candidate_audit.py
```

Inputs default:

```text
candidate_csv=tmp/eurusd/EURUSD_15m_pattern_candidates.csv
template_csv=tmp/eurusd/EURUSD_15m_pattern_review_template.csv
batch_csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
clean_view_csv=tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
rejected_csv=tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples.csv
```

Outputs:

```text
tmp/validation-eurusd-candidate-audit.json
tmp/validation-eurusd-candidate-audit.md
```

Report sections:
1. `causality_summary`
2. `future_usage_summary`
3. `selection_explainability_summary`
4. `multi_label_summary`
5. `duplicate_region_summary`
6. `coverage_summary`
7. `active_batch_warnings`
8. `next_actions`

Suggested statuses:
- `pass`: no major audit risks.
- `watch`: non-blocking issues found.
- `needs_rule_refinement`: candidate quality rules need improvement.
- `blocked`: severe missing files/corrupt candidate data.

## Task 7 — Integrate With Reset/Review Validation Scripts

Update read-only validation scripts so the audit can be run easily:

```text
scripts/validate_eurusd_review_progress.sh
```

or create:

```text
scripts/validate_eurusd_candidate_audit.sh
```

Command:

```bash
./scripts/validate_eurusd_candidate_audit.sh
```

Should:
- run candidate audit report,
- print concise status,
- be read-only,
- not reset/rebuild batch.

## Task 8 — Documentation

Update:
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/README.md` if relevant

Document:
- causal candidate logic vs review sampling filters vs human labels
- future bar usage flags
- multi-label candidate interpretation
- session/volatility coverage audit
- how to run the audit
- warning that future-aware filters are not live trading rules

## Tests Required

Add tests for:

### Causality metadata
1. Candidate rows include causality/future usage fields.
2. Future-aware review filters are marked as review filters, not causal signal.
3. Candidate logic remains marked past-only when appropriate.

### Explainability
4. Candidate rows have reason codes.
5. Review-selected rows have selection reasons.
6. Trend candidates have segment reason/metadata.

### Multi-label conflicts
7. Same timestamp with multiple candidate types is detected.
8. Batch duplicates by same timestamp are flagged.

### Coverage
9. Year/month/hour/session coverage computed correctly.
10. Volatility buckets computed deterministically.
11. Coverage warnings trigger for concentrated batch.

### Duplicates
12. Same-region/window-overlap duplicate groups detected.

### Report
13. Candidate audit report emits all expected sections.
14. Missing optional rejected file does not block report.
15. Missing required candidate file blocks/returns clear status.

### Non-destructive behavior
16. Audit report does not modify candidate/template/batch/completed/rejected files.

## Validation Commands

Run candidate audit report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
```

Run audit script if added:

```bash
./scripts/validate_eurusd_candidate_audit.sh
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_sampling_source_range.py
```

Run GUI/review tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_rejected_samples.py
```

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

## Manual Review

Open the generated markdown:

```text
tmp/validation-eurusd-candidate-audit.md
```

Confirm it answers:
- Are any candidate rules using future bars?
- Which future usage is only for review sampling?
- Are there same-timestamp multi-label conflicts?
- Does active batch cover years/sessions/volatility reasonably?
- Are selected candles explainable?
- Are trend samples segment representatives, not trend-end reversals?

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: audit EURUSD candidate causality and coverage"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Causality metadata behavior
- Future-bar usage audit
- Selection explainability audit
- Multi-label conflict audit
- Duplicate/same-region audit
- Coverage audit
- Report artifact paths
- Validation command results
- Whether active batch/review data was left unchanged
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- reset active review data
- regenerate active batch destructively
- delete completed/rejected CSV/JSONL
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
