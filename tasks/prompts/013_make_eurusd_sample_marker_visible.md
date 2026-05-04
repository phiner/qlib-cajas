# 013 — Make EURUSD GUI Sample Marker Visible Without Obscuring Wicks

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent chart marker changes:
- Intrusive full-height sample-center line was removed.
- Wick-sensitive candidates use annotation-only marker to avoid covering the candle wick.
- Default candidates use offset marker + arrow annotation.

User now reports:
- Some charts appear to have no sample marker.
- In the screenshot, there may be only a tiny top annotation text such as:
  `Sample (2020-01-02 05:00:00+00:00)`
- The marker is not visually obvious enough for review.

Requirement:
- The sample marker must be clearly visible.
- It must not obscure the candle body/wick.
- Especially for wick-sensitive candidates, do not draw a vertical line through the candle.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.

## Objective

Improve the sample marker so every chart clearly indicates the sample candle without hiding the sample candle’s wick/body.

## Desired Visual Behavior

For all candidate types:
- The sample candle should be easy to identify at a glance.
- The marker should not cover the candle.
- The marker should remain visible even in dark theme.

For wick-sensitive candidate types:
- Do not use a full-height vertical line through the candle.
- Prefer a small non-obstructive marker, such as:
  - top arrow annotation pointing down to the candle,
  - small ring/dot above or below the candle,
  - subtle background band behind the candle but not over the wick,
  - bracket/triangle marker at the top of chart.

Recommended approach:
- Add a **small marker symbol** above the candle high, for example:
  - triangle-down marker,
  - small open circle,
  - small star,
  - label “Sample” with arrow.
- Keep the marker offset from the wick:
  - y position should be slightly above candle high by a small padding.
- For wick-sensitive samples:
  - use symbol + arrow only, no full-height line.
- For non-wick samples:
  - offset vertical marker is okay, but also include a visible symbol/arrow.

## Required Implementation

### 1. Build explicit marker trace or annotation

Avoid relying only on tiny annotation text.

Add a marker trace or annotation that is reliably visible.

Example marker trace:
```python
fig.add_trace(
    go.Scatter(
        x=[sample_display_x],
        y=[sample_marker_y],
        mode="markers+text",
        marker={...},
        text=["Sample"],
        textposition="top center",
        hoverinfo="skip",
        showlegend=False,
    )
)
```

Or Plotly annotation:
```python
fig.add_annotation(
    x=sample_display_x,
    y=sample_marker_y,
    text="Sample",
    showarrow=True,
    ax=0,
    ay=-30,
)
```

Important:
- The marker should point to the sample candle.
- The marker y should be calculated from visible price range:
  - above sample high, or
  - a fixed fraction below top of y-axis.
- Do not place text so high that it gets clipped.
- Increase top margin if needed.

### 2. Compute marker y safely

Add helper if needed:
```python
def compute_sample_marker_y(sample_high, visible_high, visible_low, offset_ratio=0.04) -> float:
    ...
```

Behavior:
- place marker above sample high by a small amount
- clamp so it remains inside chart range
- if too close to top, expand y-axis range or place marker slightly below top

### 3. Ensure annotation is not clipped

If using top annotation:
- increase top margin slightly
- or expand y-axis range by a small padding
- ensure marker is visible for high-of-window sample candles

### 4. Keep timestamp available but compact visually

Main visible label can be short:
```text
Sample
```

Full timestamp should remain in:
- hover/customdata
- debug details
- optional annotation hover if supported

Do not put long full timestamp as the only visible marker label if it causes clutter.

### 5. Preserve wick-safe behavior

For:
- `lower_wick_rejection_candidate`
- `upper_wick_rejection_candidate`

Do:
- visible marker above/beside candle
- arrow or symbol pointing to candle
- no full-height line through candle

### 6. Preserve existing behavior

Do not change:
- Save / Save and Next / Previous / Next
- CSV/JSONL persistence
- batch diversification
- compressed gap markers
- chart framing/window logic except marker padding if needed

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. Sample marker config always includes a visible element:
   - marker trace or annotation present
   - label contains `Sample`

2. Wick-sensitive marker mode:
   - no full-height line through candle
   - visible symbol/annotation exists

3. Marker y helper:
   - marker y is above sample high where possible
   - marker y remains within/near expanded visible range
   - high-near-top sample does not produce clipped marker

4. Visual label compactness:
   - visible marker text is short, e.g. `Sample`
   - full timestamp remains in metadata/debug/hover

5. Regression:
   - gap compression markers still exist
   - sample anchor maps to correct display x
   - chart framing helper still passes
   - Save / Save and Next / Previous / Next tests still pass

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
2. Confirm the sample marker is clearly visible.
3. Confirm the sample wick/body is not covered.
4. Confirm the marker is not clipped at top.
5. Confirm timestamp remains available in hover/debug.
6. Confirm Save / Save and Next / Previous / Next still work.
7. Confirm gap compression markers still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:
```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/013_make_eurusd_sample_marker_visible.md
git commit -m "fix: make EURUSD GUI sample marker visible"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Marker visibility behavior
- Wick obstruction status
- Timestamp/debug preservation
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

## Hard Boundaries

Do not:
- add SQLite
- create branches
- push automatically
- merge automatically
- train models
- produce trading signals/orders
- modify Qlib core
- delete completed review CSV/JSONL data
- reintroduce an intrusive full-height line through wick-sensitive sample candles
