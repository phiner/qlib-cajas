# 011 — Improve EURUSD GUI Chart Framing and X-Axis Labels

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review GUI status:
- Save / Save and Next / Previous / Next work.
- CSV/JSONL persistence works.
- Review batch diversification works.
- Market-closed/weekend gaps are compressed and marked.
- The user is now reporting a chart UX issue.

Observed problems from manual GUI use:
1. X-axis datetime labels sometimes appear slanted/rotated.
2. Candle spacing can feel too wide, so too few visible candles are shown.
3. The sample marker is not centered well.
4. There is sometimes too little pre-sample context, so the prior trend is hard to see.

User request:
- Improve chart framing/layout.
- Make the sample marker placement better.
- Show more useful trend context before the sample.
- Reduce or eliminate slanted x-axis datetime labels.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only, no SQLite.

## Objective

Polish the EURUSD chart display so it is more useful for review:

1. Keep x-axis labels readable and preferably horizontal.
2. Show a denser/more useful candle window.
3. Place the sample marker in a better position within the visible window.
4. Preserve compressed gap behavior and raw timestamp hover/debug info.

## Required Behavior

### 1. Improve sample framing / visible context

Adjust the chart window logic so the sample candle is no longer too close to the left edge.

Preferred default:
- Put the sample candle around the middle of the visible window, or slightly right of center if that gives better pre-trend context.
- A good default is something like:
  - `pre_context_ratio = 0.6`
  - meaning about 60% of visible candles are before the sample and 40% after,
  - or another deterministic ratio if it produces better review UX.

Acceptable target:
- sample marker visible near center area, not jammed to the far left.
- enough earlier candles are visible to understand the lead-in trend.

Add a small helper if needed, for example:

```python
def compute_sample_window_bounds(
    target_index: int,
    total_rows: int,
    window_bars: int,
    pre_context_ratio: float = 0.6,
) -> tuple[int, int]:
    ...
```

Requirements:
- clamp correctly at dataset boundaries
- keep window size stable where possible
- preserve sample anchor mapping

### 2. Show a denser candle view

Review whether compressed-axis plotting is leaving too much spacing between candles.

Improve the Plotly layout so more candles fit visually without feeling sparse.

Possible adjustments:
- slightly reduce figure width padding/margins
- reduce tick count
- use better x-axis tick handling for compressed axis
- ensure candle positions are sequential and compact
- avoid excessive label density that forces awkward spacing

Do not change the underlying OHLC data.

### 3. Fix / reduce slanted datetime labels

The datetime labels on the x-axis should preferably stay horizontal.

Suggested behavior:
- set tick angle to `0`
- reduce tick count
- shorten visible tick label format

For compressed candle axis, use shorter visible labels such as:
- `01-01 22:00`
- `01-02 03:15`

Keep full timestamp in:
- hover
- chart debug info
- sample marker annotation

If horizontal labels still overlap badly, use fewer ticks rather than rotating labels.

### 4. Preserve gap compression behavior

Do not revert:
- compressed market-closed/weekend gaps
- gap markers / annotations
- raw timestamp in hover/debug

### 5. Preserve persistence and review behavior

Do not change:
- Save / Save and Next / Previous / Next behavior
- completed CSV schema
- JSONL event schema
- review labels/scores
- batch diversification logic

## Suggested Implementation Notes

Likely files:
- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/tests/test_eurusd_pattern_review_gui.py`

Potential helper additions:
- `compute_sample_window_bounds(...)`
- `format_compact_tick_labels(...)`
- `build_chart_tick_config(...)`

Potential chart adjustments:
- set x-axis tickangle = 0
- set fewer tickvals/ticktext for compressed axis
- shorten visible tick labels
- adjust window framing so sample marker is centered or slightly right-of-center
- keep annotation timestamp full-length or mostly full-length

## Tests Required

Add/update tests in `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. Window framing helper:
   - middle sample gives near-centered placement
   - near-start sample clamps correctly
   - near-end sample clamps correctly
   - window size stays stable where possible

2. Pre-context ratio:
   - verify more pre-context than post-context when configured
   - sample index appears around desired position in the visible window

3. Tick formatting:
   - compact tick labels are shorter than full timestamps
   - tick labels have no newline and are suitable for horizontal display

4. Static/config regression:
   - chart config uses horizontal tick angle or helper producing equivalent behavior
   - compressed axis and gap marker behavior still present

5. Existing regression tests still pass:
   - Save helper
   - Save and Next helper
   - navigation helper tests
   - gap compression tests
   - persistence tests

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
1. Open several samples.
2. Confirm x-axis labels are horizontal or much less likely to rotate.
3. Confirm visible candles are framed more usefully.
4. Confirm the sample marker is near the center area (or slightly right-of-center).
5. Confirm more pre-sample trend is visible.
6. Confirm gap markers still work.
7. Confirm Save / Save and Next / Previous / Next still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/011_improve_eurusd_gui_chart_framing.md
git commit -m "feat: improve EURUSD GUI chart framing"
```

Only add files that changed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- X-axis label behavior
- Sample framing behavior
- Pre-context visibility behavior
- Candle density / spacing behavior
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
