# 030 — Fix EURUSD Candidate Generation at Source With Segment-Level Representative Samples

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review workflow:
- GUI, CSV/JSONL persistence, rejected samples, full-range batch generation, and validation reports are implemented.
- User is actively reviewing samples.
- User noticed a recurring source-quality issue:
  - For `short_trend_down_candidate`, many adjacent candles in the same local move could qualify.
  - The system sometimes selects a candle near the end of a down move / near rebound, which is not a good representative sample.
  - Human question: “Why this candle? Many previous candles could also be marked.”
- Example reason codes:
  - `negative_short_slopes`
  - `low_range_position`
- This suggests candidate generation is too candle-level and not segment-aware.

Goal:
- Fix this at source, not only with review labels or rejection.
- Candidate generation should produce fewer, more representative samples.
- This is offline research infrastructure only.
- Do not create trading signals/orders.
- Do not train models.
- Do not modify Qlib core.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.

## Problem Statement

Current candidate logic likely does something like:

```text
for each candle:
    if short slopes are negative and price is low in range:
        emit short_trend_down_candidate
```

This creates too many near-duplicate candidate anchors in the same trend segment.

It can also pick weak/late points:
- sample is already near local low,
- immediate rebound follows,
- many earlier candles in the move would be equally or more representative,
- review sample is not useful.

## Objective

Refactor / enhance EURUSD pattern candidate generation so trend candidates are segment-level and representative.

For trend candidates:
- detect continuous trend segments,
- emit only representative candidate(s) per segment,
- avoid late/exhausted/rebound points,
- record segment metadata and rejection/selection reason codes.

Initial focus:
- `short_trend_down_candidate`
- `short_trend_up_candidate`
- possibly `mid_trend_down`
- possibly `mid_trend_up`

Do not overfit only to one screenshot; implement general segment-aware candidate quality controls.

## Required Behavior

### 1. Add segment detection for trend candidates

For short trend down:
- Use existing slope signals / reason codes as input.
- Identify contiguous runs where short-term trend condition is true.
- A segment begins when trend condition turns true.
- A segment ends when trend condition turns false or a max gap is exceeded.

Segment metadata:
```text
segment_id
segment_start_timestamp
segment_end_timestamp
segment_length_bars
segment_direction
segment_start_index
segment_end_index
segment_price_change
segment_return
segment_low_index
segment_high_index
```

For down segment:
- price generally moves down.
- segment low and rebound behavior should be known.

For up segment:
- mirror logic.

### 2. Emit representative candidates, not every candle

For each segment:
- default max candidates per segment:
  ```text
  max_candidates_per_segment = 1
  ```
- optionally allow:
  ```text
  max_candidates_per_segment = 2
  ```
  for long segments.

Representative selection for down segment:
- Prefer a candle around early/mid segment, not the final low/reversal.
- Suggested candidate position:
  ```text
  target_fraction = 0.4 to 0.6 of segment progress
  ```
- Avoid segment end:
  ```text
  avoid_last_n_bars = 3 or 4
  ```
- Avoid candles immediately followed by strong rebound.

Representative selection for up segment:
- mirror the logic.

### 3. Add late/exhaustion/rebound filter

For `short_trend_down_candidate`, mark or drop candidate if:
- candidate is at or near segment low,
- next 1–4 candles rebound strongly,
- follow-through after candidate is opposite direction,
- candidate occurs in last X% of segment.

Suggested defaults:
```text
avoid_last_n_bars = 4
max_segment_position_fraction = 0.75
rebound_lookahead_bars = 4
rebound_threshold_atr_multiple = 0.5
```

If ATR is not available, use local range or candle body percentile.

If dropping is too aggressive:
- do not emit as `short_trend_down_candidate`;
- or emit with lower confidence and reason code:
  ```text
  late_segment_candidate
  rebound_after_anchor
  weak_representative_anchor
  ```

Preferred for review batch:
- exclude weak representative anchors by default.

### 4. Add candidate reason codes

New reason codes to include where applicable:

Positive selection reasons:
```text
segment_representative
segment_midpoint_anchor
trend_continuation_context
sufficient_pre_context
```

Exclusion / downgrade reasons:
```text
same_segment_duplicate_suppressed
late_segment_anchor
near_segment_low
near_segment_high
rebound_after_anchor
weak_follow_through_after_anchor
```

Do not clutter GUI too much, but keep these in candidate CSV/reports.

### 5. Add candidate-level metadata columns

Extend candidate pack output with optional columns:

```text
segment_id
segment_direction
segment_start_timestamp
segment_end_timestamp
segment_length_bars
segment_position_fraction
segment_anchor_rank
segment_duplicate_suppressed_count
representative_anchor
late_segment_anchor
rebound_after_anchor
```

Compatibility:
- Existing consumers should tolerate missing/extra columns.
- Do not break GUI if extra columns exist.

### 6. Update candidate pack report

The candidate pack report should summarize:
- candidate counts before/after segment de-duplication
- suppressed same-segment duplicates
- segment counts by direction/type
- average candidates per segment
- late/rebound filtered count
- trend candidate quality distribution

Suggested fields:
```text
raw_trend_trigger_count
segment_count
representative_candidate_count
same_segment_duplicate_suppressed_count
late_segment_filtered_count
rebound_filtered_count
```

### 7. Update review template/batch generation

Future review template/batch generation should prefer:
```text
representative_anchor == true
late_segment_anchor == false
rebound_after_anchor == false
```

For trend candidate types.

Do not automatically reset current active batch unless user explicitly asks.

But if the user asks to rebuild later, reset script should use the improved candidate pack.

### 8. Add audit report for current source issue

Add a report that can answer:

```text
For short_trend_down_candidate, how many adjacent/segment duplicate triggers existed?
How many were suppressed?
How many emitted anchors are near segment end?
```

This can be integrated into candidate pack report or separate.

### 9. Tests

Add tests for pure segment logic.

Suggested tests:

#### Segment detection
Input synthetic series:
- 10 bars down condition true
- 3 bars false
- 8 bars down condition true
Expect:
- 2 segments.

#### Representative selection
Given a 10-bar down segment:
- representative anchor should be around middle, not final bar.
- segment_position_fraction between 0.3 and 0.7.

#### Suppress duplicates
Given every bar in a 10-bar segment triggers:
- emitted candidates <= 1 or configured max.
- suppressed count = raw triggers - emitted.

#### Late anchor filter
Given candidate at last bar and rebound follows:
- mark `late_segment_anchor=true`
- mark `rebound_after_anchor=true`
- do not emit as preferred representative candidate.

#### Up/down symmetry
Test up segment behavior mirrors down segment behavior.

#### Candidate pack integration
Build candidate pack from small synthetic data:
- output includes segment metadata.
- duplicate suppression metrics are populated.

#### Backward compatibility
Existing GUI/review tests still pass when candidate CSV has extra segment columns.

## Validation Commands

Run candidate tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py
```

If new tests added:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_trend_segment_candidates.py
```

Run GUI/review tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run candidate pack build on real data:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old --dry-run
```

Do not run destructive reset unless explicitly requested.

If there is a safe candidate-pack-only build command, run it and write to temporary non-active output paths, e.g.:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_pattern_candidate_pack \
  --output-candidates-csv tmp/eurusd/EURUSD_15m_pattern_candidates_segment_audit.csv \
  --output-json tmp/validation-eurusd-pattern-candidate-pack-segment-audit.json \
  --output-md tmp/validation-eurusd-pattern-candidate-pack-segment-audit.md
```

Adjust actual CLI args to existing script.

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

## Manual Review Check

After implementation, inspect a few candidate examples:
- `short_trend_down_candidate`
- `short_trend_up_candidate`

Confirm:
- candidates are not emitted on every adjacent candle in the same segment.
- representative anchor is not at obvious final reversal point.
- reason codes explain representative selection.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: add segment-aware EURUSD trend candidates"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Segment detection behavior
- Representative candidate behavior
- Duplicate suppression behavior
- Late/rebound filter behavior
- New metadata columns
- Candidate pack/report metrics
- Review batch integration behavior
- Validation command results
- Whether active batch was left unchanged
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
