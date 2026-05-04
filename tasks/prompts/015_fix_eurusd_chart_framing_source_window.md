# 015 — Fix EURUSD GUI Chart Framing Source Window, Not Just Bounds Helper

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent commit:
- `fb62b23e`
- Added/fixed `compute_sample_window_bounds(...)`
- Added chart debug metadata:
  - `window_start`
  - `window_end`
  - `target_index_global`
  - `sample_position_ratio`
  - `boundary_clamp_start`
  - `boundary_clamp_end`

User retested the GUI and the sample marker is still near the far-left edge of the chart.

Screenshot behavior:
- sample marker is visible near the left edge
- there are very few or no pre-sample candles visible
- post-sample candles extend far to the right
- this is not acceptable for review because prior trend context is missing

Likely root cause:
- The helper may be correct, but the chart rendering path is passing an already-truncated source window into it.
- In other words:
  1. full EURUSD 15m candle data exists,
  2. some older logic first extracts a local window around/after the sample,
  3. then `compute_sample_window_bounds(...)` runs on that already-short window,
  4. so it cannot recover older pre-sample candles.
- The actual fix must ensure chart extraction starts from the full source OHLC data, not from a pre-truncated sample/review window.

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

Fix the actual runtime chart data path so non-boundary samples are framed near the center or slightly right-of-center, with enough pre-sample trend visible.

The sample should only appear near the left edge when it is truly close to the beginning of the full available OHLC data.

## Required Investigation

### 1. Inspect GUI chart data flow

Search:

```bash
grep -R "extract_chart_window" -n cajas/apps cajas/research
grep -R "extract_chart_window_with_diagnostics" -n cajas/apps cajas/research
grep -R "target_index_global" -n cajas/apps cajas/research
grep -R "window_start" -n cajas/apps cajas/research
grep -R "lookback" -n cajas/apps cajas/research
grep -R "forward" -n cajas/apps cajas/research
grep -R "timestamp" -n cajas/apps/eurusd_pattern_review_app.py
```

Find:
- where the full EURUSD OHLC/source CSV is loaded,
- where the sample timestamp is matched,
- whether the app passes full OHLC data or a pre-sliced chart window into the chart helper,
- whether `target_index_global` is actually global source index or only index in a pre-sliced window.

### 2. Verify with runtime debug

For the sample that still appears left-edge, use Chart Debug Info to check:
- `target_index_global`
- `window_start`
- `window_end`
- `sample_position_ratio`
- `boundary_clamp_start`
- source row count / chart source row count, if available

If `boundary_clamp_start=true` but the sample is from 2020-01-02 and the source should have earlier 2020-01-01 bars, then the source is pre-truncated and the clamp is false-positive.

Add debug fields if missing:
- `full_source_row_count`
- `chart_source_row_count`
- `source_min_timestamp`
- `source_max_timestamp`
- `sample_timestamp`
- `sample_is_near_full_source_start`
- `framing_source_kind`, e.g. `full_ohlc_source` vs `pre_sliced_window`

### 3. Fix source selection

The chart window extraction should work like this:

```python
full_ohlc = load_full_eurusd_15m_ohlc(...)
sample_timestamp = current_sample["timestamp"]
target_index_global = find_timestamp_index(full_ohlc, sample_timestamp)
window_start, window_end = compute_sample_window_bounds(
    target_index=target_index_global,
    total_rows=len(full_ohlc),
    window_bars=120,
    pre_context_ratio=0.6,
)
chart_window = full_ohlc.iloc[window_start:window_end]
sample_display_index = target_index_global - window_start
```

Do not do this:

```python
pre_sliced = get_existing_candidate_window(...)
target_index = find_timestamp_index(pre_sliced, sample_timestamp)
chart_window = pre_sliced[...]
```

unless the pre-sliced window is known to include enough pre-context.

### 4. Ensure global timestamp matching is robust

Implement or verify helper:

```python
def find_sample_timestamp_index(full_ohlc, sample_timestamp, timestamp_col="timestamp") -> int | None:
    ...
```

Requirements:
- handles timezone-aware timestamps
- handles string timestamps
- exact match preferred
- nearest match allowed only if explicitly marked as fallback
- returns diagnostics:
  - exact_match true/false
  - fallback true/false
  - matched_timestamp
  - target_index_global

### 5. Preserve compressed display axis

After chart_window is selected from full source:
- compressed display axis still uses sequential x positions inside chart_window
- sample marker x should be `sample_display_index`
- gap markers still based on timestamps inside chart_window
- raw timestamps preserved in hover/debug

### 6. Preserve sample marker behavior

Do not revert:
- diamond-open marker
- annotation arrow
- wick-sensitive no full-height line

### 7. Preserve persistence and review behavior

Do not change:
- Save / Save and Next / Previous / Next
- completed CSV schema
- JSONL event schema
- batch diversification
- review labels/scores

## Expected Runtime Result

For a non-boundary sample:
- `boundary_clamp_start=false`
- `sample_position_ratio` should be around `0.6`
- sample marker should visually appear around center-right
- pre-sample trend should be visible

For true beginning-of-source sample:
- `boundary_clamp_start=true`
- marker may appear near left
- debug should clearly say there is not enough pre-sample source data

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Required tests:

### 1. Full-source extraction test
Create synthetic OHLC with 300 bars.
Pick target index 150.
Call the actual chart window extraction helper.
Expect:
- window_start around target - 72
- sample_display_index around 72
- sample_position_ratio around 0.6
- `boundary_clamp_start=false`

### 2. Pre-sliced source regression
Create synthetic OHLC full source with 300 bars.
Also create pre-sliced window starting at target index.
Ensure the high-level extraction helper uses full source when available, not pre-sliced candidate window.
Expect sample not at display index 0 for non-boundary sample.

### 3. Timestamp matching
Test timezone-aware and string timestamp match:
- exact match returns global index
- fallback nearest match is flagged

### 4. Debug metadata
Assert debug includes:
- `full_source_row_count`
- `source_min_timestamp`
- `source_max_timestamp`
- `sample_timestamp`
- `target_index_global`
- `sample_position_ratio`
- `boundary_clamp_start`

### 5. Boundary case
For target index near start:
- boundary clamp true
- sample display index small
- status/diagnostics explain clamp

### 6. Existing regression tests
Ensure still passing:
- marker visibility/wick-safe behavior
- gap compression
- tick labels
- Save / Save and Next / Previous / Next
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
2. Confirm marker appears near center/right-of-center.
3. Confirm enough pre-sample trend is visible.
4. Open Chart Debug Info and confirm:
   - `framing_source_kind=full_ohlc_source`
   - `boundary_clamp_start=false` for non-boundary samples
   - `sample_position_ratio` around 0.6
5. Confirm marker is visible and does not cover wick.
6. Confirm compressed gap markers still work.
7. Confirm Save / Save and Next / Previous / Next still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/015_fix_eurusd_chart_framing_source_window.md
git commit -m "fix: frame EURUSD chart from full source data"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- Source window fix
- Runtime debug fields added
- Sample position ratio behavior
- Marker visibility/wick status
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
