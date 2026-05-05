# 033 — Close EURUSD Candidate Audit Warnings and Hardening Roadmap Before Review Continues

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current state:
- EURUSD 15m GUI review workflow exists.
- CSV/JSONL persistence exists.
- Rejected-sample workflow exists.
- Review schema v2 exists.
- Full-range reset/rebuild exists.
- Segment-aware trend candidates exist.
- Candidate causality/explainability/multi-label/coverage audit exists from commit `e0d6b05b`.
- Active audit status is currently:
  ```text
  needs_rule_refinement
  ```
- User explicitly requested:
  - Do not push/advance until issues are improved and fixed.
  - Fully evaluate remaining improvement points.
  - Improve completeness and future extensibility.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- Do not train models.
- Do not produce trading signals/orders.
- Do not modify Qlib core.
- Do not delete completed/rejected CSV/JSONL.
- Do not reset/rebuild active batch unless explicitly needed and clearly reported.
- If reset/rebuild is needed to validate candidate rule improvements, run only after source fixes and with backup.

## Objective

Before continuing review, close the current candidate-audit `needs_rule_refinement` state or convert it into a clearly justified `watch`/`pass` state with documented non-blocking follow-ups.

This task must:

1. Inspect the actual candidate audit report.
2. Identify every warning/next action.
3. Classify warnings as:
   - must-fix-now,
   - should-fix-now,
   - acceptable-watch,
   - future-extension.
4. Implement must-fix and high-value should-fix items.
5. Add tests and metrics so regressions are caught.
6. Re-run candidate audit and validation.
7. Produce a durable hardening/extension roadmap.

## Required Inputs

Read these artifacts first:

```text
tmp/validation-eurusd-candidate-audit.json
tmp/validation-eurusd-candidate-audit.md
tmp/validation-eurusd-pattern-candidate-pack.json
tmp/validation-eurusd-pattern-candidate-pack.md
tmp/validation-eurusd-sampling-source-range.json
tmp/validation-eurusd-pattern-review-batch-001.json
tmp/validation-eurusd-completed-review-progress.json
```

Do not assume from summaries only. Inspect the actual reports.

## Task 1 — Audit Warning Inventory

Create a structured inventory of all candidate-audit warnings.

Output:

```text
tmp/validation-eurusd-candidate-audit-warning-inventory.json
tmp/validation-eurusd-candidate-audit-warning-inventory.md
```

For each warning include:
- `warning_id`
- `section`
- `description`
- `affected_count`
- `affected_sample_ids` or representative examples
- `severity`
- `classification`
- `recommended_action`
- `fix_now`
- `reason`

Classification:
```text
must_fix_now
should_fix_now
acceptable_watch
future_extension
```

Must-fix examples:
- candidate logic future leakage not clearly separated from review filters
- selected batch rows missing reason/explainability
- trend rows without segment metadata
- selected trend rows marked `excluded_late_reversal_anchor=true`
- selected trend rows with `preferred_review_candidate=false` without fallback explanation
- active batch still severely concentrated after full-range rebuild
- same timestamp appears multiple times in batch without primary/multilabel resolution
- report status blocked due missing required artifacts

Should-fix examples:
- some non-trend candidate types missing primary selection reason
- excessive multi-label conflicts without primary candidate type
- coverage overly concentrated in one session/volatility bucket
- duplicate region warnings above threshold

Acceptable watch:
- naturally high multi-label candidate pool but batch de-duplicates it
- future-aware review sampling filter clearly marked and isolated
- missing rejected file when no rejects exist

Future extension:
- multi-symbol support
- model training dataset conversion
- richer volatility/regime definitions
- UI visualizations

## Task 2 — Define Audit Gates

Add clear gates so `needs_rule_refinement` is deterministic, not vague.

Suggested candidate-audit status rules:

### pass
All must-fix gates pass:
- no batch row with `candidate_logic_uses_future_bars=true`
- no batch trend row with `excluded_late_reversal_anchor=true`
- no batch trend row with `preferred_review_candidate=false` unless `fallback_reason` exists
- batch rows have `primary_selection_reason`
- trend batch rows have segment metadata
- no exact duplicate sample IDs
- no same timestamp duplicate rows in active batch
- source range not truncated
- active batch year coverage spans multiple years
- GUI/review artifacts readable

### watch
Must-fix gates pass, but non-blocking issues remain:
- candidate pool has many multi-label timestamps
- some candidate types need future refinement
- session/volatility coverage imbalance exists but not severe
- duplicate region warnings below threshold

### needs_rule_refinement
At least one should-fix or quality gate is materially failing:
- many selected rows missing explainability
- selected batch has high duplicate/overlap concentration
- selected candidates have unclassified future usage
- trend selection quality warnings above threshold

### blocked
Required files missing/corrupt or causality leakage in candidate logic used for selected batch.

Implement or update these deterministic gates in:
```text
cajas/reports/validation_eurusd_candidate_audit.py
```

Add tests for status transitions.

## Task 3 — Fix Explainability Gaps

If audit shows missing reason fields, fix source generation.

Every candidate row should have:
```text
candidate_reason_codes
primary_selection_reason
```

Every review-selected batch row should have:
```text
selection_reason_codes
review_sampling_reason_codes
```

Trend rows should have:
```text
segment_reason_codes
segment_id
segment_position_fraction
representative_anchor
preferred_review_candidate
```

For non-trend candidate types, define primary selection reasons:

Examples:
- `lower_wick_rejection_candidate`
  - `primary_selection_reason=lower_wick_rejection_geometry`
- `upper_wick_rejection_candidate`
  - `primary_selection_reason=upper_wick_rejection_geometry`
- `possible_false_breakout_candidate`
  - `primary_selection_reason=false_breakout_structure`
- `compression`
  - `primary_selection_reason=range_compression`
- `expansion`
  - `primary_selection_reason=range_expansion`
- `doji_indecision`
  - `primary_selection_reason=doji_indecision_geometry`

Do not leave blank/NaN for selected rows.

## Task 4 — Fix Future-Usage Ambiguity

Ensure fields distinguish:

```text
candidate_logic_uses_future_bars
review_filter_uses_future_bars
label_uses_future_bars
not_for_live_signal
future_usage_role
```

Rules:
- `candidate_logic_uses_future_bars` should be false for causal candidate logic.
- If review filter uses next 4 bars, it must be marked as review filter, not candidate logic.
- Human review labels/follow-through are label/evaluation, not candidate-generation logic.
- Any row with ambiguous future usage should trigger warning.

Add tests:
- segment late/rebound filter is marked `review_filter_uses_future_bars=true`
- candidate logic remains `candidate_logic_uses_future_bars=false`
- no selected batch row has unclassified future usage.

## Task 5 — Fix Multi-Label / Same Timestamp Handling

If active batch has same timestamp duplicates:
- fix review batch generation to avoid selecting same timestamp twice by default.
- Preserve all candidate types in candidate pack.
- In batch selection, choose one primary candidate per timestamp unless explicitly configured.

Add candidate pack fields:
```text
same_timestamp_candidate_types
same_timestamp_candidate_type_count
primary_candidate_type
multi_candidate_timestamp
```

For batch rows:
- avoid duplicate timestamp rows.
- if duplicate allowed by fallback, set:
  ```text
  duplicate_timestamp_fallback=true
  fallback_reason=...
  ```

Add tests:
- same timestamp multiple candidate types detected.
- batch builder avoids same timestamp duplicates.
- primary candidate type deterministic.

## Task 6 — Fix Duplicate / Same-Region Batch Concentration

If audit shows high overlap/duplicate-region warnings in active batch:
- update batch diversification to reduce them.
- Apply thresholds:
  ```text
  anchor_duplicate_gap_bars=8
  same_region_cooldown_bars=48
  window_overlap_max_ratio=0.35
  ```
- Prefer not to select two samples with >35% visible-window overlap.
- Use graceful fallback only with explicit fallback reason.

Add batch report metrics:
```text
same_region_warning_count
window_overlap_duplicate_count
fallback_duplicate_region_count
first20_unique_days
first20_unique_years
first20_max_window_overlap
```

Add tests.

## Task 7 — Fix Coverage Imbalance Where Reasonable

Do not force perfect equal distribution, but avoid obvious concentration.

Audit coverage dimensions:
```text
year
month
weekday
hour_of_day_utc
session_bucket
volatility_bucket
candidate_type
```

If active batch coverage is concentrated:
- update template/batch sampling to stratify by:
  - candidate_type,
  - year or broad time bucket,
  - session bucket,
  - volatility bucket where possible.

Do not overfit. Use best-effort stratified sampling with fallback.

Add metrics:
```text
coverage_status
coverage_warnings
first20_coverage_summary
```

Add tests:
- synthetic candidates across years/sessions produce diversified batch.
- fallback works when pool lacks coverage.

## Task 8 — Rebuild Active Batch If Source Fixes Affect Sampling

If any source/batch-selection rules change, run explicit reset/rebuild with backup:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

Only do this after implementing fixes.

Then re-run:
```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Expected:
- active batch generated from improved rules
- completed progress fresh-start if reset performed
- audit status no worse than `watch`; ideally `pass`

If active batch is left unchanged, explain why.

## Task 9 — Long-Term Extensibility Assessment

Create a durable roadmap/report:

```text
tmp/validation-eurusd-candidate-hardening-roadmap.json
tmp/validation-eurusd-candidate-hardening-roadmap.md
```

Include sections:

### Architecture boundaries
- candidate generation
- review sampling filters
- human labels
- validation/audit reports
- GUI review
- future research dataset export

### Extensibility risks
- future leakage risk
- multi-label conflicts
- regime/session imbalance
- too many candidate-specific hard-coded rules
- reject feedback not feeding candidate generation
- scaling to more symbols/timeframes
- label schema drift
- batch reproducibility and random seeds
- data lineage/versioning
- active batch vs source-candidate version mismatch

### Recommended next phases
- candidate rule registry
- unified candidate metadata schema
- deterministic sampling manifest
- reject feedback loop into batch generation
- candidate quality dashboard
- second-batch generation from first-batch review findings
- research dataset export with strict feature/label window separation
- time-based train/validation/test split design
- multi-symbol/timeframe support only after EURUSD workflow stabilizes

### Must not do yet
- no model training from first 100 reviews
- no trading signal/execution system
- no random train/test split
- no using future-aware review filters as live candidate logic

## Task 10 — Documentation

Update:
```text
cajas/docs/eurusd_pattern_research_kickoff.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
cajas/README.md
```

Document:
- candidate causality gates
- future usage separation
- candidate explainability requirements
- active audit gates
- when review can continue
- when reset/rebuild is required
- why no push/advance until audit status is acceptable

## Tests Required

Add/update tests for:
1. deterministic audit gates
2. pass/watch/needs_rule_refinement/blocked status rules
3. explainability fields present for selected rows
4. future usage classified correctly
5. no selected trend late-reversal anchors
6. batch avoids duplicate timestamps
7. multi-label timestamp metadata
8. duplicate/same-region thresholds
9. coverage warning behavior
10. hardening roadmap report generation
11. active batch unchanged or reset behavior explicitly reported

## Validation Commands

Run candidate audit:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./scripts/validate_eurusd_candidate_audit.sh
```

Run source range/progress reports:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_sampling_source_range.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py
```

Run GUI/review tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py \
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

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: harden EURUSD candidate audit gates"
```

If reset/rebuild artifacts only changed under `tmp/`, do not commit `tmp` unless repo convention already tracks them.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Initial audit status and warning inventory
- Warnings fixed now
- Warnings left as watch with justification
- Audit gate definitions
- Final audit status
- Whether active batch was rebuilt
- If rebuilt: backup dir and new batch coverage
- Causality/future usage status
- Explainability status
- Multi-label conflict status
- Duplicate/same-region status
- Coverage status
- Hardening roadmap artifact paths
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
- use future-aware filters as live candidate logic
