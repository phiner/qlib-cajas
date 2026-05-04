# 014 — Fix EURUSD GUI Sample Framing So Marker Is Not at Left Edge

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent chart marker work:
- `f81a5c62` added visible diamond-open marker + Sample arrow.
- It fixed marker visibility/wick obstruction.
- However, user reports the sample marker still appears at the far left edge of the chart in some cases.

Current screenshot:
- The marker is visible, but it is located near the far-left side of the chart.
- This means the reviewer cannot see enough pre-sample trend context.
- The intended framing from prior work was sample around center or slightly right-of-center, but runtime chart still shows sample too far left.

Root issue:
- This is likely not a marker style problem.
- The chart window extraction / target index / sample index mapping is placing the sample near the left edge.
- Need to fix the actual sample framing logic used by the app.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only.
- No SQLite.
- Do not train models.
- Do not modify Qlib core.
- Do not delete completed review CSV/JSONL data.

## Objective

Ensure the sample candle is displayed near the center or slightly right-of-center of the visible chart window, so pre-sample trend context is visible.

The visible sample marker must not appear at the far left except when the sample truly occurs near the beginning of the available source data and there is no prior data to show.

## Required Behavior

### 1. Fix runtime chart window extraction

Inspect the actual path in:

```text
cajas/apps/eurusd_pattern_review_app.py
cajas/research/eurusd_pattern_review_gui.py
```

Find where:
- chart source data is loaded,
- sample timestamp/index is matched,
- visible chart window is sliced,
- target index / sample display x is computed.

Search:

```bash
grep -R "target_index" -n cajas/apps cajas/research
grep -R "lookback" -n cajas/apps cajas/research
grep -R "forward" -n cajas/apps cajas/research
grep -R "compute_sample_window_bounds" -n cajas
```

The app should use a single deterministic helper for window bounds.

### 2. Define intended framing

Use a default:

```text
window_bars = 120
pre_context_ratio = 0.6
```

Meaning:
- about 60% of visible candles before the sample,
- about 40% after the sample,
- sample should appear around 60% from the left side of the visible x-axis,
- not at far left.

For example:
- If `window_bars=120`, sample should be around display index `72`, not `0`, `5`, or `10`.
- Acceptable range for non-boundary samples: roughly 45%–70% of the visible window width.

### 3. Correct helper behavior

If `compute_sample_window_bounds(...)` exists, verify and fix:

```python
def compute_sample_window_bounds(
    target_index: int,
    total_rows: int,
    window_bars: int,
    pre_context_ratio: float = 0.6,
) -> tuple[int, int]:
    ...
```

Expected:
- `pre_count = round(window_bars * pre_context_ratio)`
- `start = target_index - pre_count`
- `end = start + window_bars`
- clamp start/end to `[0, total_rows]`
- if clamped at end, shift start back to keep window size
- return stable bounds

For non-boundary sample:
- `target_index - start` should be close to `pre_count`.

### 4. Fix app usage

The app must actually use this helper when building the chart window.

Avoid patterns like:
```python
window = rows[target_index : target_index + window_bars]
```

or:
```python
window_start = max(0, target_index - small_lookback)
```

if they put sample near left.

Make sure:
- `target_index` is the index of sample timestamp in the full chart source data,
- not the row index inside already sliced candidate batch,
- not the review batch row number,
- not a reset/renumbered index that causes wrong slicing.

### 5. Validate sample display x

After slicing:
- `sample_display_x = target_index - window_start`
- should be near `pre_count` for normal samples.
- Add debug metadata:
  - `window_start`
  - `window_end`
  - `source_target_index`
  - `sample_display_index`
  - `window_bars`
  - `pre_context_ratio`
  - `sample_position_ratio`

Compact diagnostic line can stay compact, but full debug should show these.

### 6. Handle boundary cases

If the sample is near start of the full source data:
- it is acceptable for marker to be left because no earlier candles exist.
- debug should indicate boundary clamp.

If sample is not near start:
- marker should not be left.

### 7. Preserve marker style

Do not revert:
- diamond-open marker
- annotation arrow
- wick-safe mode
- no full-height line through wick-sensitive candle

### 8. Preserve all existing behavior

Do not change:
- Save / Save and Next / Previous / Next
- CSV/JSONL persistence
- batch diversification
- compressed gap behavior
- review schema

## Tests Required

Add/update tests in `cajas/tests/test_eurusd_pattern_review_gui.py`.

Required tests:

### 1. Window bounds normal case
Given:
- `total_rows=1000`
- `target_index=500`
- `window_bars=120`
- `pre_context_ratio=0.6`

Expect:
- `start` around 428
- `end` around 548
- `sample_display_index` around 72
- sample position ratio around 0.6

### 2. Near-start clamp
Given:
- `target_index=10`
- `window_bars=120`

Expect:
- `start=0`
- sample display index = 10
- boundary clamp recognized

### 3. Near-end clamp
Given:
- `total_rows=1000`
- `target_index=980`
- `window_bars=120`

Expect:
- `end=1000`
- `start=880`
- sample display index = 100
- valid bounds

### 4. App/chart payload uses helper result
Add a pure function if needed that returns chart payload metadata.
Assert:
- non-boundary sample has `sample_position_ratio` not near 0.
- e.g. ratio > 0.4.

### 5. Regression for sample marker
For wick-sensitive sample:
- marker visible
- no full-height line through candle
- sample display x not far left for non-boundary sample

### 6. Existing regression tests still pass
- gap compression
- tick labels
- Save / Save and Next / Previous / Next helpers
- CSV/JSONL persistence

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
1. Open the sample that previously showed marker at far left.
2. Confirm marker is near center or slightly right-of-center.
3. Confirm enough pre-sample trend is visible.
4. Confirm marker remains visible and does not cover wick.
5. Confirm compressed gap markers still work.
6. Confirm Save / Save and Next / Previous / Next still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/014_fix_eurusd_sample_framing_left_edge.md
git commit -m "fix: center EURUSD GUI sample framing"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- Window/framing fix
- Sample position ratio behavior
- Marker visibility/wick status
- Debug metadata added
- Gap compression regression status
- Save/navigation regression status
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```
