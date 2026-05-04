# 004 — Compress EURUSD GUI Weekend/Holiday Chart Gaps With Marker

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review GUI chart behavior:
- Candlestick chart uses real timestamp x-axis.
- Around weekends/market-closed intervals, the chart leaves a very large blank horizontal space.
- The user does not want the blank space preserved at full real-time length.
- The user also does not want to lose the fact that a gap exists.

Desired behavior:
- Do not leave huge empty chart space proportional to weekend/holiday duration.
- Compress weekend/holiday/market-closed gaps visually.
- Add a vertical marker/label at the compressed gap position.
- Label should explain this is a previous-week to current-week or holiday/market-closed gap.
- Keep real timestamps available in hover/debug metadata.

User preference:
- CSV/JSONL only for persistence.
- No SQLite.
- Work directly on `main`.
- Use simple sequential task prompt numbering.
- Do not create branches.
- Do not push automatically.

## Objective

Implement a chart rendering mode for EURUSD review GUI that compresses large non-trading time gaps while preserving a clear gap marker.

This is a review UX feature, not a data transformation for training or trading.

## Required Behavior

### 1. Detect large time gaps

Reuse or add helper logic in:

```text
cajas/research/eurusd_pattern_review_gui.py
```

Detect gaps between consecutive candle timestamps.

For EURUSD 15m:
- expected interval: 15 minutes
- large gap threshold: default `> 60 minutes` or `> expected_interval_minutes * 4`

For each gap, capture:
- previous candle timestamp
- next candle timestamp
- gap duration minutes/hours
- classification:
  - `weekend_or_market_closed_gap`
  - `holiday_or_market_closed_gap`
  - `missing_bars_or_data_gap`
- display label, for example:
  - `Weekend / market closed`
  - `Previous week → current week`
  - `Holiday / market closed`
  - `Large time gap`

Do not treat weekend/holiday/market-closed gaps as data corruption.

### 2. Render chart on compressed display axis

Do not use raw timestamp as the Plotly x-axis when large gaps exist.

Instead, create a display x-axis:
- Use sequential candle positions: `0, 1, 2, ...`
- Preserve original timestamps in hover text/customdata.
- Use tick labels derived from actual timestamps at sensible positions.
- This removes huge time-proportional blank areas.

Important:
- This is only the chart display axis.
- Do not change source CSV data.
- Do not change sample ids.
- Do not change review persistence.
- Do not change generated candidates.

### 3. Add visual gap marker

At each detected gap, add a narrow visual marker between the previous and next candle.

Options:
- Add a vertical dashed line using Plotly shape at x position between two candles.
- Add an annotation above the chart.

Example annotation:

```text
Weekend / market closed
Previous week → current week
48.0h gap compressed
```

The marker should be visually obvious but not an error.

Suggested implementation:
- If using sequential candle positions, for a gap between row i and i+1:
  - place vertical line at `x=i + 0.5`
  - annotation at `x=i + 0.5`
- Do not insert fake OHLC candles unless absolutely necessary.
- Prefer Plotly shapes/annotations.

### 4. Make chart diagnostics explicit

Below chart or inside debug expander, show:

```text
display_axis=compressed_gap_axis
raw_time_axis_preserved_in_hover=true
time_gap_count=N
largest_gap_hours=X
gap_markers=N
```

For each gap in debug:
- start timestamp
- end timestamp
- duration
- classification
- display x position

### 5. User-facing hint

Add a compact non-error hint near chart, for example:

```text
Chart gap compressed: 1 weekend/market-closed interval was collapsed and marked with a vertical line. Original timestamps remain available in hover/debug info.
```

If no large gap exists:

```text
display_axis=real_time_axis
time_gap_count=0
```

or simply no hint.

### 6. Preserve sample anchor marker

Existing sample anchor vertical marker must still point to the correct sample candle.

If chart x-axis changes to sequential positions:
- sample marker should use the sample candle display position, not raw timestamp.
- annotation should still show real timestamp.

### 7. Preserve hover timestamp

Candlestick hover should still show:
- original timestamp
- open/high/low/close
- sample_id or candidate info when relevant

### 8. Preserve all persistence behavior

Do not change:
- Save
- Save and Next
- Reset
- completed CSV
- JSONL audit events
- review schema
- score fields
- label fields

### 9. Add pure helper functions and tests

Suggested helpers:

```python
def detect_time_axis_gaps(timestamps, expected_interval_minutes=15, gap_threshold_bars=4) -> list[dict]:
    ...

def build_compressed_gap_axis(timestamps, gaps) -> dict:
    """Return display_x values, tick positions/labels, gap marker metadata."""
    ...

def summarize_compressed_gap_axis(gaps, display_axis_info) -> dict:
    ...
```

The display axis helper should be deterministic and independent of Streamlit.

## Tests Required

Add/update tests in:

```text
cajas/tests/test_eurusd_pattern_review_gui.py
```

Test cases:

1. No large gap:
   - Input continuous 15m timestamps.
   - No gaps detected.
   - display axis can remain real_time_axis or sequential without markers, depending implementation.
   - gap marker count = 0.

2. Weekend gap detection:
   - Friday candle followed by Sunday/Monday candle.
   - gap detected.
   - classification indicates weekend/market closed.
   - duration is correct.

3. Compressed display axis:
   - Given timestamps with a weekend gap.
   - display x values are compact/sequential.
   - distance between candle i and i+1 around the gap is not proportional to real gap duration.
   - marker is placed at `i + 0.5` or equivalent.

4. Gap marker metadata:
   - marker includes start/end timestamps.
   - marker includes duration.
   - marker includes label text mentioning weekend/market closed or gap compressed.

5. Sample anchor on compressed axis:
   - sample marker maps to correct display x position.
   - original timestamp preserved in metadata.

6. Debug summary:
   - includes `display_axis`
   - includes `time_gap_count`
   - includes `gap_markers`
   - includes `raw_time_axis_preserved_in_hover`

7. Regression:
   - Save/Save and Next/Reset helper tests still pass.
   - No persistence schema changes.

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
1. Open a sample around weekend/holiday gap.
2. Confirm there is no huge blank area.
3. Confirm a vertical marker/annotation indicates weekend/market-closed or previous-week/current-week gap.
4. Confirm original timestamp appears in hover/debug.
5. Confirm sample anchor marker points to the correct candle.
6. Confirm Save works.
7. Confirm Save and Next works.
8. Confirm Reset works.
9. Confirm no CSV/JSONL data is deleted or schema-changed.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py
git commit -m "feat: compress EURUSD chart market-closed gaps"
```

If task prompt files are managed in repo, add/update:

```bash
git add tasks/prompts tasks/README.md
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Gap compression behavior
- Gap marker/label behavior
- Whether raw timestamp hover/debug is preserved
- Whether huge weekend blank area is removed
- Sample anchor marker status
- Save/Save and Next/Reset regression status
- CSV/JSONL persistence status
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
- silently hide gaps without marker/annotation
