# Phase 7046–7165 — EURUSD 15m GUI Chart UX Polish and Streamlit Width Compatibility

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current branch context:

- Recent chart visibility fix branch:
  - `cajas/phase-6926-7045-gui-chart-visibility-fix`
- The GUI chart is now visible in the Streamlit app.
- The previous blank chart bug appears fixed.
- The human user has manually confirmed that a K-line chart now appears.
- The GUI still needs a small UX/compatibility polish.

Current observed UI state:

- K-line chart is visible.
- `Chart Debug Info` exists but is collapsed by default.
- The human did not notice row count / trace count because they are inside the collapsed expander.
- `Review Notes` is now blank instead of literal `nan`, which is correct.
- Streamlit logs show repeated deprecation warnings:

```text
Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`.
For `use_container_width=False`, use `width='content'`.
```

Project constraints:

- EURUSD 15m Bid only.
- No 1H/4H aggregation.
- No live trading.
- No paper trading.
- No broker routing.
- No order generation.
- No production model training.
- No Qlib core modifications.
- No labels invented by automation.
- GUI remains the review interface.
- CSV/JSONL remain durable storage/interchange formats.

## Goal

Polish the GUI chart UX and remove the Streamlit width deprecation warning.

This phase should:

1. Replace deprecated `use_container_width=True` usage with `width="stretch"`.
2. Keep compatibility if needed for older Streamlit versions.
3. Make chart diagnostics easier to see without requiring the user to open the expander.
4. Make it visually obvious that blank `Review Notes` is expected when no note exists.
5. Keep the GUI review workflow stable.

## Required Work

### 1. Replace deprecated Streamlit chart width usage

Inspect:

```text
cajas/apps/eurusd_pattern_review_app.py
```

Find any usage of:

```python
st.plotly_chart(..., use_container_width=True, ...)
```

Replace with:

```python
st.plotly_chart(..., width="stretch", ...)
```

If the installed Streamlit version does not support `width`, implement a small compatibility helper, for example:

```python
def render_plotly_chart(fig):
    try:
        st.plotly_chart(fig, width="stretch", theme=None)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, theme=None)
```

Prefer the new API path, but do not break older environments.

### 2. Add always-visible chart diagnostic summary

Currently the detailed diagnostics are inside:

```text
Chart Debug Info
```

Keep that expander, but add a compact always-visible summary near the chart, for example:

```text
Chart window: 61 rows | traces: 1 | exact match: true | fallback: false
```

Requirements:

- Show row/window count.
- Show trace count.
- Show exact match status.
- Show nearest fallback status.
- Show target index if available.
- If chart failed, show a visible warning/error.

This helps the user immediately know whether the chart is valid without opening the expander.

### 3. Make the debug expander label more discoverable

Change:

```text
Chart Debug Info
```

to something like:

```text
Chart Debug Info (click to expand)
```

or add a short hint below the summary:

```text
Open "Chart Debug Info" for timestamp/window details.
```

### 4. Review Notes UX

Current behavior where blank notes replace `nan` is correct.

Make this clearer by:

- using an empty string for missing notes
- optionally adding placeholder text:
  - `Optional notes...`
- do not show `nan`
- do not auto-fill notes

### 5. Tests

Update:

```text
cajas/tests/test_eurusd_pattern_review_gui.py
```

Add or adjust tests for:

1. Chart diagnostics summary data exists.
2. NaN notes sanitize to empty string.
3. Plotly render wrapper exists if using compatibility helper.
4. Chart diagnostic values include:
   - row count
   - trace count
   - exact match/fallback flags

Do not require launching Streamlit in tests.

### 6. Documentation

Update minimally:

```text
cajas/docs/eurusd_pattern_research_kickoff.md
cajas/README.md
```

Document:

- chart diagnostics are shown near the chart
- detailed debug info is in an expandable section
- blank review notes mean no note has been entered yet
- Streamlit width deprecation warning has been addressed

### 7. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py
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

### 8. Commit Guidance

Suggested commit:

```bash
git add   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/README.md   tasks/phase_7046_7165_eurusd_15m_gui_chart_ux_polish_prompt.md

git commit -m "fix: polish EURUSD GUI chart diagnostics and Streamlit width"
```

Do not perform automated merge operations.

If ready, push branch and merge according to the user’s current workflow preference.

## Final Response Required

Report:

- active branch
- commits created
- files changed
- whether deprecated `use_container_width` usage was removed
- whether chart diagnostic summary is now always visible
- whether debug expander label was improved
- whether blank Review Notes behavior is confirmed
- validation results
- fast validation runtime
- push status
- merge instruction
- confirmation that GUI remains the review interface and CSV/JSONL remain durable storage
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
