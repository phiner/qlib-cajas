# 021 — Refine EURUSD Pattern Review Label Schema Options

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m GUI review fields include:
- Pattern Label
- Market Context
- Direction Context
- Review Status
- Structure Quality
- Follow-through Quality
- Review Confidence
- Review Notes

Current issue:
- Some dropdown options are too coarse.
- Example: `Market Context` lacks `pullback`, so a sample can be in a downtrend background but sample candle is already rebounding/retracing.
- User wants to know what should be added to each dropdown.
- We should refine the schema/options now so future human review labels are more consistent.

Important:
- Do not reset or regenerate review batch.
- Do not delete completed CSV/JSONL.
- Existing reviewed rows may contain old enum values; compatibility must be preserved.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training and no trading signals/orders.

## Objective

Refine EURUSD pattern review schema options and GUI dropdowns so labels better capture:
1. whether the candidate pattern is valid,
2. what market environment the sample is in,
3. what directional context exists around the sample,
4. whether the review row is done / uncertain / skipped,
5. how quality/confidence scores should be interpreted.

## Required Schema Design

Update the label schema and GUI options to support the following.

### 1. Pattern Label

Purpose:
```text
Does the candidate pattern itself visually/structurally hold up?
```

Recommended options:

```text
valid_pattern
weak_pattern
false_positive
unclear
skip_bad_context
```

Keep these current options.

Definitions:
- `valid_pattern`: Candidate is visually valid and sample area supports the pattern.
- `weak_pattern`: Some evidence exists, but structure/follow-through/sample placement is weak.
- `false_positive`: Candidate is basically wrong; not the claimed pattern.
- `unclear`: Not enough evidence to decide.
- `skip_bad_context`: Data/window/context problem makes sample unsuitable, e.g. weekend gap, bad chart, missing bars.

No extra pattern-label options are required yet. Avoid making this too granular.

### 2. Market Context

Purpose:
```text
What broad market environment surrounds the sample?
```

Current options are too limited.

Recommended options:

```text
trend
range
pullback
transition
breakout
reversal_attempt
high_volatility
low_volatility
unclear
```

Definitions:
- `trend`: Clear directional trend context, sample aligns with broader move.
- `range`: Sideways/ranging context; no clean directional trend.
- `pullback`: A trend exists, but sample is in a retracement/counter-move/pullback phase.
- `transition`: Market is shifting between regimes, e.g. trend to range, range to trend, or direction losing clarity.
- `breakout`: Price is breaking out of a local range/level/structure.
- `reversal_attempt`: Visible attempt to reverse prior direction, but not necessarily confirmed.
- `high_volatility`: Wide candles/unstable price action dominate context.
- `low_volatility`: Compressed/small candles/low movement dominate context.
- `unclear`: Context cannot be judged confidently.

Important distinction:
- `pullback`: trend still exists, but sample is in a retracement.
- `transition`: regime itself is changing or unclear.
- `reversal_attempt`: stronger reversal behavior than normal pullback.

### 3. Direction Context

Purpose:
```text
What is the directional bias around the sample?
```

Current options like `down` are useful but need more nuance.

Recommended options:

```text
up
down
neutral
mixed
up_pullback
down_pullback
reversal_up
reversal_down
unclear
```

Definitions:
- `up`: Local/broader direction is upward.
- `down`: Local/broader direction is downward.
- `neutral`: No strong directional bias.
- `mixed`: Conflicting directions across short/mid context.
- `up_pullback`: Uptrend context, but sample area is pulling back downward.
- `down_pullback`: Downtrend context, but sample area is rebounding upward.
- `reversal_up`: Evidence of a shift from down/sideways toward upward.
- `reversal_down`: Evidence of a shift from up/sideways toward downward.
- `unclear`: Direction cannot be judged.

Example:
- `short_trend_down_candidate` but sample candle is beginning to rebound:
  - Pattern Label: `weak_pattern`
  - Market Context: `pullback`
  - Direction Context: `down_pullback` or `mixed`
  - Follow-through Quality: low/mid

### 4. Review Status

Purpose:
```text
Workflow state of this human review row.
```

Recommended options:

```text
pending
reviewed
needs_recheck
skip
```

Optional additional option:
```text
reviewed_uncertain
```

Preferred minimal set:
- `pending`: Not reviewed yet.
- `reviewed`: Reviewed and acceptable as final human input.
- `needs_recheck`: Reviewer is unsure or wants to revisit.
- `skip`: Deliberately skipped due to bad context / unusable sample.

If adding `reviewed_uncertain`, define it:
- `reviewed_uncertain`: Reviewed, but final confidence is low; include in summary separately.

If simpler, do not add `reviewed_uncertain`; use:
- `Review Status=reviewed`
- `Review Confidence=1/2`
- `Pattern Label=unclear/weak_pattern`

### 5. Scores

Keep score fields numeric, but document meaning:

#### Structure Quality
```text
How clearly the pattern/structure exists around the sample.
```

Suggested scale:
- `1`: no clear structure
- `2`: weak structure
- `3`: acceptable/moderate
- `4`: clear
- `5`: very clear/strong

#### Follow-through Quality
```text
How well price action after/around the sample supports the candidate idea.
```

Scale:
- `1`: no follow-through or opposite move
- `2`: weak/poor follow-through
- `3`: moderate/unclear follow-through
- `4`: good follow-through
- `5`: strong follow-through

#### Review Confidence
```text
Human reviewer confidence in their own choices, not system confidence.
```

Scale:
- `1`: very uncertain
- `2`: somewhat uncertain
- `3`: moderate confidence
- `4`: confident
- `5`: very confident

### 6. Notes

Notes may be Chinese, English, or mixed.

Recommended fixed keywords for future search:
```text
weekend gap
market closed gap
bad context
unclear structure
weak follow-through
good wick rejection
pullback
reversal attempt
```

Chinese terms are allowed:
```text
周末跳空
停盘跳空
结构不清楚
弱延续
回调
反转尝试
```

Program should not depend on free-text notes for core validation.

## Compatibility Requirements

Existing completed CSV rows may already contain old values.

Do not break loading existing rows.

Add compatibility logic:
- Old values remain valid.
- New options are added to dropdowns.
- Validation should accept old and new enum values at least during transition.
- Reports should not mark older completed rows invalid just because they used old values.

If schema versioning exists:
- bump schema version, e.g.
  `eurusd_15m_pattern_review_v2`
- keep v1 compatibility.

If schema versioning is simple:
- update label schema report and docs.

## Implementation Requirements

Likely files:
- `cajas/reports/validation_eurusd_pattern_label_schema.py`
- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- tests under `cajas/tests/`
- docs:
  - `cajas/docs/eurusd_pattern_research_kickoff.md`
  - `tasks/eurusd_15m_research_end_to_end_roadmap.md`
  - `cajas/README.md` if appropriate

Tasks:
1. Update label schema options.
2. Update GUI dropdown option lists.
3. Update validation/report code to accept new options.
4. Preserve old values.
5. Update docs with definitions.
6. Add tests.

## Tests Required

Add/update tests for:

1. Schema contains new Market Context options:
   - `pullback`
   - `breakout`
   - `reversal_attempt`
   - `unclear`

2. Schema contains new Direction Context options:
   - `up_pullback`
   - `down_pullback`
   - `reversal_up`
   - `reversal_down`
   - `mixed`
   - `unclear`

3. Existing values remain valid:
   - `trend`
   - `range`
   - `transition`
   - `up`
   - `down`
   - `neutral`
   - existing completed rows pass validation

4. GUI dropdown options include new values.

5. Completed review progress validation accepts new schema.

6. Review summary reports include new option buckets if present.

7. No completed CSV/JSONL is modified by schema update.

## Validation Commands

Run focused schema tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_pattern_label_schema.py
```

Run GUI/review tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_review_summary_current.py
```

Regenerate schema/report artifacts if applicable:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_pattern_label_schema_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_review_summary_current_report
```

Adjust script names to actual repo.

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

Manual GUI smoke:

```bash
./scripts/run_eurusd_review_gui.sh
```

Manual checks:
1. Open GUI.
2. Confirm Market Context includes:
   - `pullback`
   - `breakout`
   - `reversal_attempt`
   - `unclear`
3. Confirm Direction Context includes:
   - `up_pullback`
   - `down_pullback`
   - `reversal_up`
   - `reversal_down`
   - `mixed`
   - `unclear`
4. Confirm existing reviewed rows still load.
5. Save one row using a new option.
6. Validate progress report still passes.
7. Confirm JSONL event writes new option.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas tasks
git commit -m "feat: refine EURUSD review label schema"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Schema version behavior
- Pattern Label options
- Market Context options
- Direction Context options
- Review Status options
- Compatibility behavior for old completed rows
- GUI dropdown confirmation
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

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
