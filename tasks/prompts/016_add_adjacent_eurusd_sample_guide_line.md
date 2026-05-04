# 016 — Add Adjacent EURUSD Sample Guide Line Without Covering Candle

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent fixes:
- `c9373ddc`: chart framing now uses full OHLC source and places sample around the intended window position.
- `f81a5c62`: sample marker uses diamond-open + annotation to avoid covering wick.
- Wick-sensitive candidates avoid a full-height vertical line through the candle.

User retest:
- Sample is now better positioned in the chart.
- But some charts still look like there is “no line.”
- The diamond/text marker alone is too subtle.
- User wants a clearer line marker, but previous full-height line through the candle obscured wick/body.

Current issue:
- Need a visible vertical reference line.
- It must not overlap the sample candle/wick.
- The line should be adjacent/offset beside the sample candle, not drawn through its center.

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

Make the sample marker clearly visible by adding an adjacent vertical guide line that does not cover the sample candle.

The reviewer should immediately see which candle is the sample, while the candle body/wicks remain readable.

## Required Visual Behavior

For all candidate types:
- Show a visible sample guide line near the sample candle.
- The line must be offset to the side, not centered on the candle.
- Keep the diamond-open marker and/or arrow label if useful.
- The marker should not obscure the sample candle body or wick.

For wick-sensitive candidate types:
- `lower_wick_rejection_candidate`
- `upper_wick_rejection_candidate`

Do not draw a line through the candle center.
Use:
- adjacent offset vertical line, e.g. at `sample_x - 0.45` or `sample_x + 0.45`, plus
- diamond/open marker near sample high, plus
- short label `Sample`.

## Suggested Implementation

### 1. Add adjacent guide line metadata/helper

In `cajas/research/eurusd_pattern_review_gui.py`, add or update helper:

```python
def compute_sample_guide_line_x(
    sample_display_x: float,
    *,
    direction: str = "left",
    offset: float = 0.45,
    min_x: float = 0.0,
    max_x: float | None = None,
) -> float:
    ...
```

Behavior:
- Default line position is just left of sample candle:
  - `sample_x - 0.45`
- If sample is near left edge and left offset would fall outside chart:
  - use right side: `sample_x + 0.45`
- Clamp to visible display axis.
- Ensure it is visually adjacent to the sample.

### 2. Render adjacent vertical line

In chart rendering:
- add a vertical dashed/dotted shape at `guide_line_x`
- line should span chart y-axis, but it is offset so it does not cover the sample candle
- annotation/arrow should point to sample candle or marker symbol

Suggested Plotly shape:
```python
fig.add_shape(
    type="line",
    x0=guide_line_x,
    x1=guide_line_x,
    y0=visible_low,
    y1=visible_high,
    line={... "dash": "dot", "width": 1},
)
```

Important:
- Since the line is offset, full-height is acceptable.
- Do not place it at exactly `sample_display_x`.

### 3. Keep visible marker symbol

Keep:
- diamond-open marker above sample high
- compact `Sample` label

The line provides immediate vertical reference; the marker/arrow confirms exact sample candle.

### 4. Improve label readability

If current `Sample` text is too small or overlaps candles:
- position label above the marker
- keep it short
- optionally use `Sample` only, not full timestamp
- full timestamp remains in hover/debug

### 5. Add debug metadata

Add to chart debug:
- `sample_display_x`
- `sample_guide_line_x`
- `sample_guide_line_offset`
- `sample_guide_line_side`
- `sample_marker_mode`

This helps verify the line is adjacent, not overlapping the candle.

### 6. Preserve existing behavior

Do not change:
- chart window/framing source logic
- sample position ratio logic
- compressed gap markers
- save/navigation behavior
- CSV/JSONL persistence
- review batch diversification

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Required tests:

### 1. Guide line offset
Given sample x = 72:
- guide line x should not equal 72
- guide line x should be within about 0.3–0.6 bars of sample
- default side should be left or documented side

### 2. Left boundary fallback
Given sample x close to 0:
- guide line should switch to right side or clamp safely
- guide line remains visible

### 3. Wick-sensitive behavior
For `lower_wick_rejection_candidate`:
- marker mode includes adjacent guide line
- no line is drawn through sample center
- guide line x != sample x

### 4. Debug metadata
Assert chart metadata includes:
- `sample_display_x`
- `sample_guide_line_x`
- `sample_guide_line_side`
- `sample_marker_mode`

### 5. Regression
Existing tests still pass:
- full-source framing
- marker diamond/annotation
- gap compression
- save/navigation
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
1. Open the sample that previously looked like it had no line.
2. Confirm a vertical guide line is visible beside the sample candle.
3. Confirm the guide line does not cover the candle/wick.
4. Confirm diamond/label still identifies the exact sample.
5. Confirm lower/upper wick samples remain readable.
6. Confirm Save / Save and Next / Previous / Next still work.
7. Confirm compressed gap markers still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/016_add_adjacent_eurusd_sample_guide_line.md
git commit -m "fix: add adjacent EURUSD sample guide line"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Adjacent guide line behavior
- Wick obstruction status
- Diamond/label status
- Debug metadata status
- Full-source framing regression status
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
- draw a vertical line exactly through the sample candle center
