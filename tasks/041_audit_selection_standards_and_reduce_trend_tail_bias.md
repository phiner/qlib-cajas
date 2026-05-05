# 041 — Audit EURUSD Candidate Selection Standards and Reduce Trend-Tail Bias

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review workflow:
- Candidate generation, review GUI, CSV/JSONL persistence, rejected samples, candidate audit, and full-range rebuild are implemented.
- Segment-aware trend candidates were added to avoid choosing obvious trend-end reversal anchors.
- Review batch audit currently has no must-fix failures, but user observes during manual review:
  - many selected trend samples still feel like they are near the tail/end of a move,
  - even after rules intended to avoid trend-end/late-rebound anchors.
- User asks:
  - what standards are used to choose these Qlib/Cajas pattern samples?
  - what exactly determines selected shapes/patterns?
  - why do many still look like tail-end samples?

Important:
- The system is not a trading/execution system.
- This is offline candidate QA and human review infrastructure.
- Do not train models.
- Do not produce trading signals/orders.
- Do not modify Qlib core.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.

## Objective

Make the pattern candidate selection standards explicit, auditable, and stricter against trend-tail bias.

This task should answer and improve:
1. What rules select each candidate type?
2. What data window does each rule use?
3. Why was each selected sample chosen?
4. Are trend candidates still too often near segment tails?
5. Are current anti-tail filters too weak or not applied to review batch selection?
6. How should candidate selection be tightened before more human review?

## Required Work

### Task 1 — Document Current Candidate Selection Standards

Create or update a report:

```text
tmp/validation-eurusd-candidate-selection-standards.json
tmp/validation-eurusd-candidate-selection-standards.md
```

Also add/maintain source module if useful:

```text
cajas/reports/validation_eurusd_candidate_selection_standards.py
cajas/scripts/build_eurusd_candidate_selection_standards_report.py
cajas/tests/test_validation_eurusd_candidate_selection_standards.py
```

The report must list each candidate type and its rule basis, including at least:

```text
short_trend_up_candidate
short_trend_down_candidate
mid_trend_up_candidate
mid_trend_down_candidate
lower_wick_rejection_candidate
upper_wick_rejection_candidate
possible_false_breakout_candidate
doji_indecision_candidate
compression_candidate
expansion_candidate
```

For each type include:
- `candidate_type`
- `rule_family`
- `primary_inputs`
- `lookback_window`
- `future_window_used_by_candidate_logic`
- `future_window_used_by_review_filter`
- `reason_codes`
- `selection_reason_codes`
- `primary_selection_reason`
- `known_failure_modes`
- `current_tail_risk`
- `review_guidance`

Example descriptions:
- trend candidates:
  - selected from short/mid slope conditions plus segment representative logic.
- wick candidates:
  - selected from wick/body geometry and local context.
- false breakout:
  - selected from break beyond local level then close back inside.
- compression:
  - selected from low current range vs longer recent range.
- expansion:
  - selected from current range vs recent ATR/range expansion.
- doji:
  - selected from small body ratio.

### Task 2 — Add Tail-Bias Audit Metrics

For all trend candidates in candidate pack/template/batch, compute:

```text
segment_position_fraction
distance_to_segment_end_bars
distance_to_segment_start_bars
near_segment_tail
near_segment_head
near_segment_mid
post_anchor_reversal_strength
post_anchor_followthrough_strength
tail_bias_score
```

Suggested definitions:
- `near_segment_tail=true` if:
  ```text
  segment_position_fraction >= 0.65
  OR distance_to_segment_end_bars <= 4
  ```
- stricter than current 0.75 threshold to catch visually late samples.
- `ideal_mid_segment_anchor=true` if:
  ```text
  0.25 <= segment_position_fraction <= 0.60
  ```
- For downtrend:
  - reversal means upward rebound after anchor.
- For uptrend:
  - reversal means downward selloff after anchor.

Add summary metrics:
```text
trend_batch_count
trend_near_tail_count
trend_near_tail_ratio
trend_ideal_mid_count
trend_ideal_mid_ratio
trend_post_reversal_count
trend_post_reversal_ratio
tail_bias_status
```

Status:
- `pass`: trend_near_tail_ratio <= 0.10
- `watch`: trend_near_tail_ratio <= 0.25
- `needs_rule_refinement`: trend_near_tail_ratio > 0.25
- `blocked`: selected trend rows include excluded late reversal anchors

### Task 3 — Tighten Anti-Tail Selection Defaults

Current defaults may be too lenient:
```text
max_segment_position_fraction = 0.75
avoid_last_n_bars = 4
```

Tighten for review selection:
```text
preferred_max_segment_position_fraction = 0.60
watch_max_segment_position_fraction = 0.65
avoid_last_n_bars = 5 or 6
target_fraction = 0.40
```

Important distinction:
- Candidate pack may retain more rows for audit.
- Review template/batch should prefer stricter preferred rows.

Add or update fields:
```text
preferred_review_candidate
preferred_review_candidate_reason
tail_risk_level
tail_risk_reason_codes
```

Suggested values:
```text
tail_risk_level = low | medium | high
```

High tail risk should not enter review batch unless fallback is explicit.

### Task 4 — Verify Batch Builder Actually Uses Preferred Rows

The user suspects tail rows still appear. Check whether:
- candidate pack marks tail rows correctly,
- template builder filters/prefers correctly,
- batch builder preserves preferred candidate selection,
- old artifacts were regenerated,
- row joins lose metadata,
- booleans are parsed correctly from CSV strings.

Add tests for:
- string booleans `"True"` / `"False"` are parsed correctly.
- `preferred_review_candidate=false` rows are avoided when alternatives exist.
- high tail-risk rows are avoided when alternatives exist.
- fallback reasons are written if high tail-risk row is selected.

### Task 5 — Add “Why This Sample” Debug for GUI/Report

For each active batch row, make sure there is a concise explanation available:

```text
why_selected_summary
```

Example:
```text
segment representative at 0.42 of down segment; duplicate triggers suppressed=8; causal slope rule; no late rebound filter triggered
```

For non-trend:
```text
false breakout: broke below local low then closed inside; selected for type balance and full-range coverage
```

This should appear in:
- batch CSV
- batch report
- optional `Sample Details` expander in GUI if low-risk

Do not clutter main view.

### Task 6 — Rebuild Artifacts If Rules Change

If selection defaults or metadata are changed:
- run explicit reset/rebuild with backup:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

Then re-run:
```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_warning_inventory
```

Expected:
- no must-fix failures
- tail-bias status pass or watch
- selected trend rows mostly mid-segment
- no selected trend rows with high tail risk unless explicit fallback

### Task 7 — Review Guidance Update

Update docs:
```text
cajas/docs/eurusd_pattern_research_kickoff.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
cajas/README.md
```

Add clear review guidance:
- Trend candidate is not always “entry point”; it is currently a representative pattern sample.
- If anchor still appears near tail, mark weak/false positive and note `late trend anchor`.
- Use Reject Sample for repeated low-value tail samples.
- Tail-bias audit will track whether source rule needs further tightening.

## Tests Required

Add/update tests:
1. selection standards report covers all candidate types.
2. trend tail-bias metrics classify near-tail rows.
3. stricter preferred candidate threshold avoids segment_position_fraction > 0.60 where alternatives exist.
4. batch builder avoids high tail-risk trend candidates.
5. fallback high-tail rows include explicit fallback reason.
6. `why_selected_summary` is present for batch rows.
7. candidate audit incorporates tail-bias summary.
8. existing GUI/review/rejected/candidate audit tests still pass.

## Validation Commands

Run new standards/tail audit:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_selection_standards_report
```

Run candidate audit:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_warning_inventory
```

Run reset/rebuild if rules changed:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_candidate_selection_standards.py \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
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

## Commit Requirements

Work directly on `main`.

Suggested commit:
```bash
git add cajas scripts tasks
git commit -m "feat: audit EURUSD candidate selection standards"
```

If rules are tightened:
```bash
git commit -m "fix: reduce EURUSD trend tail candidate bias"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Current selection standards by candidate type
- Tail-bias audit result
- Anti-tail threshold changes
- Whether batch/template/candidates were rebuilt
- New batch trend tail metrics
- Why-this-sample summary behavior
- Final candidate audit status
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
