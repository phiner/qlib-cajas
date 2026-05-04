# Phase 6926–7045 — EURUSD 15m GUI Chart Visibility and Review UX Fix

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current branch context:

- The active branch is likely still:
  - `phase-eurusd-15m-gui-review-stabilization`
- GUI stabilization has already been implemented.
- The local GUI launches successfully.
- Streamlit and Plotly are installed and available.
- GUI status report is `ready`.
- The intended workflow is:
  - open GUI
  - inspect a candlestick chart around the sample timestamp
  - fill review fields
  - save/update completed CSV

Current problem reported by the human user:

- The GUI opens, but the candlestick / K-line chart is not visible.
- The screen shows the metadata and review form, but there is a large blank area where the chart should be.
- This makes manual review impossible.

Observed UX clues from the screenshot:

- Sidebar is visible and populated.
- Candidate metadata is visible:
  - confidence score
  - review priority
  - reason codes
- The review form is visible.
- A large blank dark area appears above the form, suggesting the chart container exists but the chart is not rendering correctly.
- The `Review Notes` field currently shows literal `nan`, which should be cleaned up to empty string.

This phase is a bug-fix / UX repair phase.

## Goal

Fix the GUI so the candlestick chart reliably renders and is usable for review.

This phase should:

1. Ensure the candlestick chart is always shown when data exists.
2. Make failure states visible instead of blank.
3. Ensure timestamp window extraction is correct.
4. Ensure Plotly figure rendering is explicit and stable in Streamlit.
5. Improve the review UX slightly while fixing the chart issue.
6. Keep CSV/JSONL as durable storage and GUI as the review interface.
7. Keep everything offline and research-only.

## Required Work

### 1. Reproduce and inspect the chart rendering path

Inspect:

```text
cajas/apps/eurusd_pattern_review_app.py
cajas/research/eurusd_pattern_review_gui.py
```

Trace the flow:

- selected sample
- timestamp extraction
- clean-view data loading
- chart window extraction
- Plotly figure generation
- Streamlit rendering

Find why the chart area is blank.

Possible causes to explicitly check:

- sample timestamp parsing mismatch
- timezone mismatch or string-vs-datetime mismatch
- extracted chart window is empty
- figure object is `None`
- figure exists but has zero traces
- figure layout height is too small or unset
- chart is being rendered inside an empty/stale container
- plot colors match background and become invisible
- Streamlit layout places the chart off-screen or in collapsed container
- exceptions are swallowed and replaced by blank UI

### 2. Make chart rendering explicit and stable

In the Streamlit app:

- render the chart in a dedicated visible section titled:
  - `Candlestick Chart`
- use a dedicated container:
  - `chart_container = st.container()`
- render via:
  - `st.plotly_chart(fig, use_container_width=True, theme=None)`
- set an explicit figure height, for example:
  - `height=500` or `height=600`
- ensure the chart is placed before the review form

If the figure has no data, show a visible warning instead of blank space:

```text
No chart data available for the selected sample/timestamp.
```

If timestamp window extraction fails, show:

```text
Could not extract chart window for sample_id=<...> timestamp=<...>
```

Do not silently fail.

### 3. Improve chart helper robustness

In:

```text
cajas/research/eurusd_pattern_review_gui.py
```

Ensure the helper functions:

- parse timestamps safely
- normalize timestamps to the same dtype/timezone
- locate the target bar reliably
- extract a non-empty window around the target
- return useful diagnostics if no rows are found

Add or improve helper outputs so the app can know:

- whether target timestamp matched exactly
- how many rows are in the chart window
- index of the target bar inside the window
- whether a nearest-bar fallback was used

If exact timestamp match fails, optionally support a safe nearest-match fallback within the same dataset index context, but report that fallback was used.

### 4. Improve Plotly figure visibility

Ensure figure uses readable colors against dark background.

At minimum, verify:

- candlestick increasing/decreasing colors are visible
- gridlines are faint but visible
- plot background and paper background are not identical to line colors
- target bar marker/vertical line is visible
- figure title includes:
  - sample_id
  - timestamp
  - candidate_type

A reasonable layout is fine. Do not over-design.

### 5. Clean bad default form values

Fix the `Review Notes` field so it does not show literal `nan`.

Behavior:

- if notes value is missing/NaN, show empty string
- same for any other optional text field that may currently render `nan`

### 6. Add visible sample metadata near the chart

Above or beside the chart, show compact sample context:

- `sample_id`
- `timestamp`
- `candidate_type`
- `confidence_score`
- `review_priority`
- `reason_codes`

This should help confirm the chart corresponds to the selected sample.

### 7. Add optional debug diagnostics in UI

Add a small expander such as:

```text
Chart Debug Info
```

Inside, show:

- selected sample_id
- selected timestamp
- exact timestamp match found: true/false
- nearest fallback used: true/false
- chart window row count
- target index in window
- figure trace count

This is for local debugging only and can stay lightweight.

### 8. Tests

Add or update tests:

```text
cajas/tests/test_eurusd_pattern_review_gui.py
```

Required scenarios:

1. chart window extraction returns non-empty rows for valid timestamp
2. chart helper reports empty state for missing timestamp
3. figure builder returns a Plotly figure with at least one trace when data is valid
4. app/helper converts NaN notes to empty string
5. target bar index / diagnostic info is correct or at least populated
6. nearest-match fallback behavior is stable if implemented

If there is a GUI report test file, update it only if needed.

Do not require launching Streamlit in tests.

### 9. Documentation

Update minimally:

```text
cajas/docs/eurusd_pattern_research_kickoff.md
cajas/README.md
```

Document:

- if chart is unavailable, GUI now shows an explicit warning
- chart debug info is available
- notes fields sanitize NaN to empty string

### 10. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile for changed Python modules.

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

## Commit Guidance

Suggested commits:

```bash
git add   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py

git commit -m "fix: restore EURUSD GUI candlestick chart rendering"

git add   cajas/README.md   cajas/docs/eurusd_pattern_research_kickoff.md   tasks/phase_6926_7045_eurusd_15m_gui_chart_visibility_fix_prompt.md

git commit -m "docs: note EURUSD GUI chart diagnostics"
```

Do not perform automated merge operations.

If ready, push branch and ask the human user to merge manually on GitHub.

## Final Response Required

Report:

- active branch
- commits created
- files changed
- root cause found for blank chart
- chart render status after fix
- whether warning/diagnostic states were added
- whether NaN review notes were sanitized
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that GUI remains the review interface and CSV/JSONL remain durable storage
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
