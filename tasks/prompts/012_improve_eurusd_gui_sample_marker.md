# 012 — Improve EURUSD GUI Sample Marker So It Does Not Obscure Candle Wicks

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review GUI status:
- Save / Save and Next / Previous / Next work.
- CSV/JSONL persistence works.
- Review batch diversification works.
- Market-closed/weekend gaps are compressed and marked.
- Chart framing was improved, but one more chart UX issue remains.

User-reported issue:
- The current sample marker is an orange vertical line.
- In some cases, that line overlaps the candle body / wick of the sample candle.
- This is especially bad for wick-sensitive candidate types such as:
  - `lower_wick_rejection_candidate`
  - `upper_wick_rejection_candidate`
- When the marker sits directly on the candle, it can partially hide the wick that the reviewer needs to judge.
- The user wants the marker improved so the candle remains clearly visible.

Example concern:
- For `lower_wick_rejection_candidate`, the lower wick is the key visual evidence.
- The current orange dashed marker can obscure the wick and reduce review quality.

User preference:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only.
- No SQLite.

## Objective

Improve the chart sample marker so it identifies the sample position clearly without covering the sample candle or its wick.

## Required Behavior

### 1. Do not let the sample marker obscure the sample candle

Replace or adjust the current sample marker behavior so the marker does not sit directly on top of the candle/wick in a visually intrusive way.

Preferred options (choose one or combine them):

#### Option A — Offset vertical marker slightly beside the sample candle
- Keep a vertical dashed marker, but place it slightly to the left or right of the sample candle center.
- Add a label such as:
  - `Sample`
  - `Sample @ 2020-01-01 22:30`
- The offset should be small enough to clearly indicate the sample candle, but large enough to avoid covering the wick.

For compressed axis:
- if sample display x is `x`,
- marker could be drawn at `x - 0.35` or `x + 0.35`,
- and a small annotation arrow can point back to the actual sample candle.

#### Option B — Use top annotation / arrow without full-height line
- Remove the full-height vertical line.
- Use a top annotation with arrow pointing to the candle.
- Example:
  - label above chart: `Sample`
  - arrow points toward the candle high area or candle center.
- This is often better because it does not cover the wick at all.

#### Option C — Use subtle background highlight around candle
- Add a narrow translucent highlight band behind the sample candle instead of a strong vertical line on top.
- If using a band, it must be subtle and not hide wick/body.
- Keep a small annotation above.

Best outcome:
- the sample candle remains fully readable,
- the reviewer can still instantly see which candle is the sample.

### 2. Wick-sensitive candidate types should remain especially clear

For candidate types involving wick interpretation:
- `lower_wick_rejection_candidate`
- `upper_wick_rejection_candidate`

Prefer the least obstructive marker style.

Acceptable logic:
- use a general improved marker for all candidates, OR
- use an extra-safe marker mode for wick-sensitive candidate types.

If conditional behavior is added:
- it must be simple and deterministic,
- and covered by tests.

### 3. Preserve raw timestamp visibility

The marker/annotation should still expose or preserve:
- sample timestamp
- sample identity meaning

The full timestamp can remain in:
- annotation text
- hover
- chart debug info

### 4. Preserve chart gap compression behavior

Do not revert:
- compressed market-closed/weekend gaps
- gap markers / annotations
- raw timestamp hover/debug
- improved chart framing/window logic

### 5. Preserve persistence and review behavior

Do not change:
- Save / Save and Next / Previous / Next behavior
- completed CSV schema
- JSONL event schema
- batch diversification logic
- review labels/scores

## Suggested Implementation Notes

Likely files:
- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/tests/test_eurusd_pattern_review_gui.py`

Potential helper additions:
- `build_sample_marker_config(...)`
- `compute_sample_marker_x(...)`
- `build_sample_annotation(...)`

Suggested direction:
- prefer annotation + small offset marker or annotation-only approach
- avoid drawing a strong line exactly through the sample candle center if it reduces readability

## Tests Required

Add/update tests in `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. Marker positioning helper:
   - sample marker x is not exactly the same intrusive position if offset mode is used
   - marker remains close enough to identify sample candle

2. Annotation behavior:
   - annotation text contains sample label and timestamp or compact sample text
   - annotation points to correct sample x position

3. Wick-safe behavior:
   - for wick-sensitive candidate type, selected marker mode is non-obstructive
   - or if one universal mode is used, verify it does not rely on full-height line directly over candle

4. Regression:
   - gap compression still present
   - chart framing still present
   - Save / Save and Next / Previous / Next tests still pass

5. Static/config regression:
   - app/source no longer uses the old intrusive full-height sample line directly through the candle, if practical to assert
   - or asserts the new helper/mode is used

## Validation Commands

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py
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
1. Open wick-sensitive samples.
2. Confirm the sample candle wick is fully visible.
3. Confirm the sample is still easy to identify.
4. Confirm annotation/timestamp is still clear.
5. Confirm Save / Save and Next / Previous / Next still work.
6. Confirm compressed gap markers still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/012_improve_eurusd_gui_sample_marker.md
git commit -m "feat: improve EURUSD GUI sample marker clarity"
```

Only add files that changed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Sample marker behavior
- Wick visibility improvement
- Timestamp/annotation behavior
- Chart framing regression status
- Gap compression regression status
- Save / Save and Next / Previous / Next regression status
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
- add SQLite
- create branches
- push automatically
- merge automatically
- train models
- produce trading signals/orders
- modify Qlib core
- revert compressed chart gap behavior
- delete completed review CSV/JSONL data
